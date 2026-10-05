#!/usr/bin/env python3
"""
Generatore di bit da fonti fisiche (moneta, dado, tombola) - versione 2.9-beta

- Moneta: T/0 -> 0, C/1 -> 1
- Dado a 6 facce: 1-4 -> 2 bit (1=00, 2=01, 3=10, 4=11); 5 e 6 = rilancio
- Tombola 1-8 -> 3 bit (1=000 ... 8=111)
- Ordine di inserimento in ogni giro: PRIMA tutte le monete, POI tutti i dadi, POI tutte le tombole;
  a giro finito, se serve, il giro si ripete nello stesso ordine
- Stima PRUDENTE della min-entropia accumulata, con profili di bias
- Soglia di arresto opzionale: su min-entropia stimata, su bit grezzi, oppure nessuna
- Annulla (undo): tasto CANC/BACKSPACE + Invio, oppure u / uN; tutto e' registrato
- Schermo fisso con riepilogo in alto
- Riga "Ora tocca a" ben evidenziata senza usare colori: nome della fonte (MONETA, DADO, TOMBOLA) in
  negativo (colori invertiti) e grassetto, con i simboli ► ◄ che restano anche senza terminale
- Sequenza finale di bit evidenziata in giallo nel riepilogo (non con NO_COLOR e non fuori da un terminale)
- Sullo schermo la prudenza scelta compare solo come nome in maiuscolo (per esempio PRUDENTE), senza etichetta
- Salvataggio con permessi riservati (0600 su Linux/Mac) + registro di controllo
- Avviso chiaro: da solo NON basta, va unito ad altre sorgenti con EntropyPipeline (beta6 o successiva)
- Avviso: non e' un CSPRNG; i "bit stimati" sono una stima con un modello prudente, non una prova di casualita'
- Se si usa solo il Generatore, indica quante volte va ripetuta l'esecuzione
"""

import datetime
import hashlib
import math
import os
import shutil
import sys

try:
    import select
    import termios
    import tty
    MODO_TASTI = "posix"
except ImportError:
    try:
        import msvcrt
        MODO_TASTI = "windows"
        os.system("")          # abilita le sequenze ANSI nei terminali Windows recenti
    except ImportError:
        MODO_TASTI = None

VERSIONE = "2.9-beta"
MAX_UNDO = 20                  # massimo esiti annullabili con un singolo comando
RECENT_SHOW = 12
BIT_DEFAULT = 480              # soglia in bit grezzi usata dalla versione 1
TARGET_DEFAULT = 384           # bit di min-entropia (vedi guida, sezione 5)
TOTALE_DEFAULT = 1200          # bit grezzi in tutto per 256 bit con il solo Generatore (EntropyPipeline beta6)
PIPELINE = "EntropyPipeline v2.0.0-beta6 o successiva"
TARGET_SUGGERITI = (            # (bit stimati, etichetta mostrata)
    (320, "minimo"),
    (384, "consigliato"),
    (416, "piu' prudente"),
)
BITS_PER_ESITO = {"dado": 2, "moneta": 1, "tombola": 3}
ORDINE_FONTI = ("moneta", "dado", "tombola")
EPS = 1e-9
RESET = "\033[0m"
NEGATIVO = "\033[1;7m"          # grassetto + colori invertiti: leggibile su sfondo chiaro e scuro
GIALLO = "\033[30;43m"          # testo nero su sfondo giallo


def usa_attributi():
    """Negativo e grassetto solo su un terminale vero (non servono colori, quindi valgono anche con NO_COLOR)."""
    return sys.stdout.isatty() and os.environ.get("TERM") != "dumb"


def usa_colori():
    """Il giallo solo su un terminale vero, e mai se l'utente ha impostato NO_COLOR."""
    return usa_attributi() and "NO_COLOR" not in os.environ


def evidenzia(nome):
    """Nome della fonte ben visibile: ► NOME ◄, in negativo se possibile."""
    if usa_attributi():
        return f"{NEGATIVO} ► {nome} ◄ {RESET}"
    return f"► {nome} ◄"


def sequenza_evidenziata(stringa):
    """La sequenza finale di bit, evidenziata in giallo se i colori sono ammessi."""
    return f"{GIALLO}{stringa}{RESET}" if usa_colori() else stringa


# --------------------------------------------------------------------------
#  Modello di stima della min-entropia (ipotesi dichiarate nella guida)
# --------------------------------------------------------------------------

class Profilo:
    """
    bias_rel : scostamento relativo massimo ipotizzato della probabilita' di
               ciascuna faccia (dado, pallina) dal valore ideale; 0.05 = 5%.
    p_same   : probabilita' ipotizzata che la moneta cada sulla stessa faccia
               da cui e' partita (misurata 0.508 da Bartos e altri, 2023).
    """

    def __init__(self, nome, bias_rel, p_same):
        if not (0.0 <= bias_rel <= 0.5):
            raise ValueError("bias_rel deve essere tra 0 e 0.5")
        if not (0.5 <= p_same <= 0.6):
            raise ValueError("p_same deve essere tra 0.5 e 0.6")
        self.nome = nome
        self.bias_rel = bias_rel
        self.p_same = p_same

    def h_dado(self):
        # caso peggiore: una faccia accettata (1-4) al massimo, le altre tre
        # accettate al minimo, 5 e 6 al massimo (somma delle probabilita' = 1)
        d = self.bias_rel
        return -math.log2((1 + d) / (4 - 2 * d))

    def h_tombola(self):
        # una pallina al massimo (1+d)/8, le altre compensano
        d = self.bias_rel
        return -math.log2((1 + d) / 8)

    def h_moneta(self):
        p = max(self.p_same, 1 - self.p_same)
        return -math.log2(p)

    def h(self, tipo):
        return {"dado": self.h_dado, "moneta": self.h_moneta,
                "tombola": self.h_tombola}[tipo]()


PROFILI = {
    "1": Profilo("solo prova", 0.0, 0.5),
    "2": Profilo("prudente", 0.05, 0.51),
    "3": Profilo("molto prudente", 0.10, 0.52),
}


def h_ciclo(profilo, n_dado, n_moneta, n_tombola):
    return (n_dado * profilo.h_dado() + n_moneta * profilo.h_moneta()
            + n_tombola * profilo.h_tombola())


def bit_ciclo(n_dado, n_moneta, n_tombola):
    return 2 * n_dado + n_moneta + 3 * n_tombola


def cicli_per(target, h_per_ciclo):
    return int(math.ceil(target / h_per_ciclo - EPS))


def bit_per_esecuzione(profilo, n_dado, n_moneta, n_tombola, modo, soglia):
    """(giri, bit) di una esecuzione completa; None se la fine e' decisa a mano."""
    bc = bit_ciclo(n_dado, n_moneta, n_tombola)
    if modo == "entropia":
        giri = cicli_per(soglia, h_ciclo(profilo, n_dado, n_moneta, n_tombola))
    elif modo == "bit":
        giri = int(math.ceil(soglia / bc))
    else:
        return None
    return giri, giri * bc


def ripetizioni_necessarie(totale_bit, bit_esecuzione):
    """Quante esecuzioni (da bit_esecuzione bit ciascuna) servono per arrivare a totale_bit."""
    return max(1, int(math.ceil(totale_bit / bit_esecuzione)))


# --------------------------------------------------------------------------
#  Lettura tastiera
# --------------------------------------------------------------------------

def clear_screen():
    print("\033[2J\033[H", end="")


def get_terminal_width():
    try:
        return shutil.get_terminal_size().columns
    except Exception:
        return 80


class TastiDiretti:
    """
    Tiene il terminale in modalita' tasto-per-tasto (cbreak) per tutto il blocco
    'with'. Cambiare modalita' a ogni tasto, come faceva la versione 1, puo'
    far perdere un Invio quando i tasti arrivano ravvicinati.
    """
    attivo = 0
    vecchie = None

    def __enter__(self):
        if MODO_TASTI == "posix" and sys.stdin.isatty():
            if TastiDiretti.attivo == 0:
                fd = sys.stdin.fileno()
                TastiDiretti.vecchie = termios.tcgetattr(fd)
                tty.setcbreak(fd)
            TastiDiretti.attivo += 1
        return self

    def __exit__(self, *exc):
        if MODO_TASTI == "posix" and TastiDiretti.attivo > 0:
            TastiDiretti.attivo -= 1
            if TastiDiretti.attivo == 0:
                termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN,
                                  TastiDiretti.vecchie)
        return False


def _get_key_posix():
    fd = sys.stdin.fileno()
    b = os.read(fd, 1)
    if not b:
        raise EOFError
    c = b[0]
    if c == 0x1b:                                       # Esc o sequenza
        if not select.select([fd], [], [], 0.05)[0]:
            return "IGNORA"                             # Esc da solo
        b2 = os.read(fd, 1)
        if b2 in (b"[", b"O"):
            seq = b2
            while select.select([fd], [], [], 0.05)[0]:
                nb = os.read(fd, 1)
                seq += nb
                if 0x40 <= nb[0] <= 0x7e:
                    break
            return "BACKSPACE" if seq == b"[3~" else "IGNORA"   # Canc
        return "IGNORA"
    if c in (0x7f, 0x08):
        return "BACKSPACE"
    if c in (0x0d, 0x0a):
        return "ENTER"
    if c == 0x03:
        raise KeyboardInterrupt
    if c == 0x04:
        raise EOFError
    if 0x20 <= c <= 0x7e:
        return chr(c)
    return "IGNORA"


def _get_key_windows():
    ch = msvcrt.getwch()
    if ch in ("\x00", "\xe0"):
        ch2 = msvcrt.getwch()
        return "BACKSPACE" if ch2 == "S" else "IGNORA"      # Canc
    if ch == "\x08":
        return "BACKSPACE"
    if ch in ("\r", "\n"):
        return "ENTER"
    if ch == "\x03":
        raise KeyboardInterrupt
    if ch in ("\x04", "\x1a"):
        raise EOFError
    if ch.isascii() and ch.isprintable():
        return ch
    return "IGNORA"


def get_key():
    if MODO_TASTI == "posix":
        return _get_key_posix()
    return _get_key_windows()


def tasti_diretti():
    """True se si puo' leggere tasto per tasto (serve un terminale vero)."""
    return MODO_TASTI is not None and sys.stdin.isatty()


def leggi_riga(prompt):
    """
    Ritorna ("testo", stringa) oppure ("undo", n).
    Con terminale vero: CANC/BACKSPACE su riga vuota conta come annullamento
    (ripetibile), poi Invio conferma. Senza terminale: input() normale,
    si usano solo i comandi u / uN.
    """
    if not tasti_diretti():
        return ("testo", input(prompt).strip())

    with TastiDiretti():
        return _leggi_riga_tasti(prompt)


def _leggi_riga_tasti(prompt):
    print(prompt, end="", flush=True)
    buffer = []
    undo_count = 0
    while True:
        key = get_key()
        if key == "BACKSPACE":
            if undo_count == 0 and buffer:
                buffer.pop()
                print("\b \b", end="", flush=True)
            else:
                undo_count += 1
                print(f" [CANC x{undo_count}]", end="", flush=True)
            continue
        if key == "ENTER":
            print()
            if undo_count > 0:
                return ("undo", undo_count)
            return ("testo", "".join(buffer).strip())
        if key == "IGNORA":
            continue
        if undo_count > 0:
            continue            # dopo CANC si accettano solo altri CANC o Invio
        buffer.append(key)
        print(key, end="", flush=True)


# --------------------------------------------------------------------------
#  Stato della sessione (nessuna interfaccia, testabile da solo)
# --------------------------------------------------------------------------

class Sessione:
    def __init__(self, profilo, n_dado, n_moneta, n_tombola, modo, soglia):
        if min(n_dado, n_moneta, n_tombola) < 0:
            raise ValueError("valori negativi non ammessi")
        self.profilo = profilo
        self.n = {"dado": n_dado, "moneta": n_moneta, "tombola": n_tombola}
        self.fasi = [(t, self.n[t]) for t in ORDINE_FONTI if self.n[t] > 0]
        if not self.fasi:
            raise ValueError("almeno una fonte deve essere > 0")
        self.lungh_ciclo = sum(n for _, n in self.fasi)
        if modo not in ("entropia", "bit", "nessuna"):
            raise ValueError("modo soglia non valido")
        self.modo = modo
        self.soglia = soglia
        self.esiti = []         # (tipo, inserito, bits)
        self.eventi = []        # cronologia completa, mai cancellata
        self.rilanci = []       # valori 5/6 usciti (solo diagnostica)

    # -- posizione: ricavata sempre da quanti esiti ci sono, quindi l'undo
    #    non puo' mai sfasare i blocchi
    def slot(self):
        p = len(self.esiti)
        ciclo = p // self.lungh_ciclo + 1
        i = p % self.lungh_ciclo
        for tipo, n in self.fasi:
            if i < n:
                return tipo, i, n, ciclo
            i -= n
        raise AssertionError("posizione non valida")

    def aggiungi(self, tipo, inserito, bits):
        if tipo != self.slot()[0]:
            raise AssertionError("fonte diversa da quella attesa")
        if len(bits) != BITS_PER_ESITO[tipo] or set(bits) - {"0", "1"}:
            raise AssertionError("bit non validi")
        self.esiti.append((tipo, inserito, bits))
        self.eventi.append(("esito", tipo, inserito, bits))

    def rilancio(self, valore):
        self.rilanci.append(valore)
        self.eventi.append(("rilancio", valore))

    def undo(self, quanti):
        k = min(quanti, MAX_UNDO, len(self.esiti))
        if k <= 0:
            return 0
        rimossi = [self.esiti.pop() for _ in range(k)]
        self.eventi.append(("undo", rimossi))
        return k

    def bitstring(self):
        return "".join(b for _, _, b in self.esiti)

    def total_bits(self):
        return sum(len(b) for _, _, b in self.esiti)

    def total_h(self):
        return sum(self.profilo.h(t) for t, _, _ in self.esiti)

    def fine_ciclo(self):
        return len(self.esiti) > 0 and len(self.esiti) % self.lungh_ciclo == 0

    def soglia_raggiunta(self):
        if self.modo == "entropia":
            return self.total_h() >= self.soglia - EPS
        if self.modo == "bit":
            return self.total_bits() >= self.soglia
        return False

    def completato(self):
        # come nella versione 1 la soglia si controlla a fine ciclo; dipende
        # solo dal NUMERO di esiti, mai dal loro valore
        return self.fine_ciclo() and self.soglia_raggiunta()

    def ricostruisci_da_eventi(self):
        """Riesegue la cronologia e ritorna gli esiti che ne risultano."""
        lista = []
        for ev in self.eventi:
            if ev[0] == "esito":
                lista.append((ev[1], ev[2], ev[3]))
            elif ev[0] == "undo":
                for _ in ev[1]:
                    lista.pop()
        return lista

    def coerente(self):
        return self.ricostruisci_da_eventi() == self.esiti

    def conteggi(self):
        c = {"dado": {str(i): 0 for i in range(1, 5)},
             "moneta": {"T": 0, "C": 0},
             "tombola": {str(i): 0 for i in range(1, 9)}}
        for tipo, ins, _ in self.esiti:
            c[tipo][ins] += 1
        return c

    def parametri_testo(self):
        p = self.profilo
        righe = [
            f"Profilo di stima: {p.nome}",
            f"  scostamento relativo massimo ipotizzato per faccia/pallina: {p.bias_rel * 100:.1f}%",
            f"  probabilita' ipotizzata moneta stessa faccia: {p.p_same * 100:.1f}%",
            f"  min-entropia stimata per esito: moneta {p.h_moneta():.4f} (su 1 bit), "
            f"dado {p.h_dado():.4f} (su 2 bit), tombola {p.h_tombola():.4f} (su 3 bit)",
            f"Per ciclo, nell'ordine di inserimento: moneta {self.n['moneta']}, "
            f"dado {self.n['dado']} esiti validi, tombola {self.n['tombola']}",
        ]
        if self.modo == "entropia":
            righe.append(f"Soglia: {self.soglia:g} bit di min-entropia stimata")
        elif self.modo == "bit":
            righe.append(f"Soglia: {self.soglia} bit grezzi")
        else:
            righe.append("Soglia: nessuna (conclusione manuale)")
        return righe


# --------------------------------------------------------------------------
#  Salvataggio
# --------------------------------------------------------------------------

def sha256_testo(s):
    return hashlib.sha256(s.encode("ascii")).hexdigest()


def testo_registro(sess, inizio, fine, soglia_ok):
    L = []
    L.append(f"REGISTRO GENERATORE BIT v{VERSIONE}")
    L.append("NOTA: da solo il Generatore NON basta: questi bit vanno uniti ad altre sorgenti")
    L.append(f"indipendenti con {PIPELINE} (strumento della suite entropy-suite).")
    L.append(f"Se si usa SOLO il Generatore servono circa {TOTALE_DEFAULT} bit in tutto: questa esecuzione ne ha dati")
    L.append(f"{sess.total_bits()}, quindi l'esecuzione va ripetuta {ripetizioni_necessarie(TOTALE_DEFAULT, max(1, sess.total_bits()))} volte in tutto.")
    L.append(f"Inizio: {inizio:%Y-%m-%d %H:%M:%S} (ora locale)   Fine: {fine:%Y-%m-%d %H:%M:%S}")
    L.extend(sess.parametri_testo())
    L.append("Il registro contiene le stesse informazioni dei bit: trattalo come riservato.")
    L.append("")
    L.append("CRONOLOGIA COMPLETA (in ordine di inserimento, nulla viene cancellato)")
    for k, ev in enumerate(sess.eventi, 1):
        if ev[0] == "esito":
            L.append(f"{k:4d}  esito   {ev[1]:8s} inserito={ev[2]:6s} bit={ev[3]}")
        elif ev[0] == "rilancio":
            L.append(f"{k:4d}  rilancio dado: uscito {ev[1]}")
        else:
            rim = ", ".join(f"{t}:{i}" for t, i, _ in reversed(ev[1]))
            L.append(f"{k:4d}  ANNULLATI {len(ev[1])} esiti (dal piu' recente): {rim}")
    L.append("")
    L.append("ESITI VALIDI FINALI")
    for k, (t, i, b) in enumerate(sess.esiti, 1):
        L.append(f"{k:4d}  {t:8s} inserito={i:6s} bit={b}")
    L.append("")
    n_undo = sum(1 for ev in sess.eventi if ev[0] == "undo")
    n_rim = sum(len(ev[1]) for ev in sess.eventi if ev[0] == "undo")
    L.append(f"Comandi di annullamento: {n_undo} (esiti annullati in totale: {n_rim})")
    L.append(f"Rilanci del dado (5 o 6): {len(sess.rilanci)}")
    L.append(f"Bit totali: {sess.total_bits()}")
    L.append(f"Bit stimati (min-entropia, modello prudente): {sess.total_h():.2f}")
    if sess.modo != "nessuna":
        L.append("Soglia raggiunta: " + ("si" if soglia_ok else "NO"))
    L.append(f"Coerenza cronologia/esiti: {'OK' if sess.coerente() else 'ERRORE'}")
    L.append(f"SHA-256 della stringa di bit: {sha256_testo(sess.bitstring())}")
    return "\n".join(L) + "\n"


def scrivi_esclusivo(percorso, contenuto):
    """Crea un file nuovo (mai sovrascrive), permessi riservati dove supportati."""
    fd = os.open(percorso, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
        f.write(contenuto)


def percorsi_salvataggio(nome):
    base, ext = os.path.splitext(nome)
    return nome, f"{base}_registro.txt"


# --------------------------------------------------------------------------
#  Interfaccia
# --------------------------------------------------------------------------

class FineProgramma(Exception):
    pass


def plurale(n, uno, tanti):
    return uno if n == 1 else tanti


class Programma:
    def __init__(self):
        self.s = None
        self.msg = ""
        self.termina = False
        self.inizio = datetime.datetime.now()

    # ---------- preparazione ----------
    def _chiedi(self, prompt):
        r = input(prompt).strip()
        if r.lower() in ("q", "quit", "esci"):
            raise FineProgramma
        return r

    def _chiedi_int(self, prompt, minimo=0, default=None):
        while True:
            r = self._chiedi(prompt)
            if r == "" and default is not None:
                return default
            if r.isascii() and r.isdigit() and int(r) >= minimo:
                return int(r)
            print(f"  Scrivi un numero intero, {minimo} o piu'")

    def _chiedi_pct(self, prompt, minimo, massimo):
        while True:
            r = self._chiedi(prompt).replace(",", ".")
            try:
                v = float(r)
            except ValueError:
                print("  Scrivi un numero")
                continue
            if minimo <= v <= massimo and math.isfinite(v):
                return v
            print(f"  Il numero deve stare tra {minimo} e {massimo}")

    def scegli_profilo(self):
        print("  1) QUANTO VUOI ESSERE PRUDENTE?")
        print("     Dadi, monete e palline reali non sono mai perfetti.")
        print("     Piu' sei prudente, piu' lanci servono.")
        for k, p in PROFILI.items():
            extra = "  (consigliato)" if k == "2" else ""
            print(f"      {k}) {p.nome}{extra}")
        print("      4) personalizzato")
        while True:
            r = self._chiedi("  Scrivi il numero della scelta [2] → ") or "2"
            if r in PROFILI:
                return PROFILI[r]
            if r == "4":
                d = self._chiedi_pct(
                    "  Di quanto puo' essere 'truccato' un dado o una pallina?\n"
                    "  In percentuale, da 0 a 50 (consigliato: 5) → ", 0, 50)
                ps = self._chiedi_pct(
                    "  Su 100 lanci, quante volte la moneta ricade sulla faccia\n"
                    "  da cui e' partita? Da 50 a 60 (consigliato: 51) → ", 50, 60)
                return Profilo("personalizzato", d / 100, ps / 100)
            print("  Scelta non valida")

    def configura(self):
        clear_screen()
        print("═" * 66)
        print(f"  GENERATORE BIT v{VERSIONE}  -  PREPARAZIONE   (q = esci)")
        print("═" * 66)
        print("  Questo programma trasforma i tuoi lanci di dado e di moneta e le tue")
        print("  estrazioni della tombola in una lunga sequenza di 0 e 1.")
        print("  Ti dice anche quanti 'bit stimati' hai raccolto: piu' sono, meglio e'.")
        print()
        print("  IMPORTANTE: da solo questo programma NON basta.")
        print("  I bit che produce vanno uniti ad altre sorgenti INDIPENDENTI con")
        print("  EntropyPipeline v2.0.0-beta6 o successiva (lo strumento della suite")
        print("  entropy-suite, che li estrae con Peres e Toeplitz). Da solo il Generatore")
        print("  non produce una chiave.")
        print("  Non e' un generatore casuale per uso crittografico (CSPRNG): i 'bit stimati'")
        print("  sono una stima con un modello prudente, non una prova di casualita'.")
        print()
        profilo = self.scegli_profilo()
        if profilo.bias_rel == 0 and profilo.p_same == 0.5:
            print("  ATTENZIONE: 'solo prova' non tiene conto di nessuno squilibrio.")
            print("  Non usarlo per una chiave vera.")
        print()
        print("  2) QUANTI INSERIMENTI PER OGNI GIRO?")
        print("     Un giro e' una serie di lanci ed estrazioni sempre uguale.")
        print("     In ogni giro inserirai PRIMA tutte le monete, POI tutti i dadi, POI tutte")
        print("     le tombole; finito il giro, se servono altri bit, il giro si ripete.")
        print("     Scrivi 0 per saltare una fonte.")
        print("     Per il dado contano solo i lanci validi (1-4): con 5 o 6 si rilancia.")
        while True:
            nm = self._chiedi_int("  Lanci di MONETA per giro        → ")
            nd = self._chiedi_int("  Lanci validi di DADO per giro   → ")
            nt = self._chiedi_int("  Estrazioni di TOMBOLA per giro  → ")
            if nd + nm + nt > 0:
                break
            print("  Almeno una fonte deve essere maggiore di 0")

        hc = h_ciclo(profilo, nd, nm, nt)
        bc = bit_ciclo(nd, nm, nt)
        print()
        print(f"  Ogni giro ti da' {bc} bit e circa {hc:.1f} bit stimati.")
        print("  Per ricavare una chiave da 256 bit servono:")
        for t, etichetta in TARGET_SUGGERITI:
            c = cicli_per(t, hc)
            print(f"     {etichetta:12s} {t} bit stimati  →  {c} giri ({c * bc} bit)")
        print()
        print("  3) QUANDO VUOI FERMARTI?")
        print("      1) quando ho abbastanza bit stimati  (consigliato)")
        print(f"      2) dopo un certo numero di bit      (la versione 1 usava {BIT_DEFAULT})")
        print("      3) quando lo dico io, scrivendo 'fine'")
        while True:
            r = self._chiedi("  Scrivi il numero della scelta [1] → ") or "1"
            if r in ("1", "2", "3"):
                break
            print("  Scelta non valida")
        if r == "1":
            soglia = self._chiedi_int(
                f"  Quanti bit stimati vuoi? Invio per {TARGET_DEFAULT} (consigliato) → ",
                minimo=1, default=TARGET_DEFAULT)
            modo = "entropia"
            if soglia < 256:
                print("  ATTENZIONE: con meno di 256 bit stimati non puoi ricavare una chiave da 256 bit.")
        elif r == "2":
            soglia = self._chiedi_int(
                f"  Quanti bit vuoi raccogliere? Invio per {BIT_DEFAULT} → ",
                minimo=1, default=BIT_DEFAULT)
            modo = "bit"
            print(f"  Con {soglia} bit raccolti avrai circa {soglia * hc / bc:.0f} bit stimati.")
        else:
            soglia, modo = 0, "nessuna"
        self.s = Sessione(profilo, nd, nm, nt, modo, soglia)
        print()
        print("  SE USI SOLO IL GENERATORE (senza altre sorgenti esterne e indipendenti):")
        print(f"  {PIPELINE} chiede circa {TOTALE_DEFAULT} bit")
        print("  per ricavare 256 bit (circa 200 giri da 6 bit). Con versioni precedenti della")
        print("  pagina questi numeri non valgono.")
        prev = bit_per_esecuzione(profilo, nd, nm, nt, modo, soglia)
        if prev is None:
            print("  Con 'fine' deciso da te non posso calcolarlo adesso: lo scrivo alla fine,")
            print("  in base ai bit che avrai raccolto.")
        else:
            giri_esec, bit_esec = prev
            n = ripetizioni_necessarie(TOTALE_DEFAULT, bit_esec)
            print(f"  Una esecuzione con questa impostazione = {giri_esec} giri = {bit_esec} bit.")
            if n == 1:
                print("  Quindi basta UNA esecuzione per arrivare a quel numero di bit.")
            else:
                print(f"  Quindi il programma va eseguito {n} VOLTE in tutto,")
                print("  anche in giorni diversi, salvando ogni volta con un nome diverso.")
        print("  Con altre sorgenti indipendenti ne servono meno: lo dice la Fase 4 di EntropyPipeline.")

    # ---------- schermata ----------
    def disegna(self, fase_testo, istruzione, tipo=None, dettaglio=""):
        s = self.s
        clear_screen()
        w = get_terminal_width()
        linea = "═" * min(w, 70)
        print(linea)
        print(f"  GENERATORE BIT v{VERSIONE}  |  Moneta + Dado + Tombola")
        print(linea)
        tot, h = s.total_bits(), s.total_h()
        bar_len = 40
        if s.modo == "entropia":
            frac = min(1.0, h / s.soglia)
            print(f"  Bit raccolti: {tot:4d}      Bit stimati: {h:6.1f} su {s.soglia:g}")
        elif s.modo == "bit":
            frac = min(1.0, tot / s.soglia)
            print(f"  Bit raccolti: {tot:4d} su {s.soglia}      Bit stimati: {h:6.1f}")
        else:
            frac = None
            print(f"  Bit raccolti: {tot:4d}      Bit stimati: {h:6.1f}")
            print("  Scrivi 'fine' quando vuoi concludere.")
        if frac is not None:
            filled = int(bar_len * frac)
            print(f"  [{'█' * filled}{'░' * (bar_len - filled)}] {frac * 100:5.1f}%")
        print(f"  {s.profilo.nome.upper()}")
        if tipo:
            print(f"  Ora tocca a: {evidenzia(fase_testo)}  {dettaglio}")
        else:
            print(f"  Ora tocca a: {fase_testo}")
        print(linea)
        recent = s.bitstring()[-RECENT_SHOW:]
        print(f"  Ultimi {len(recent)} bit: ...{recent}" if recent else "  Ultimi bit: (ancora nessuno)")
        print(linea)
        if self.msg:
            print(f"  >> {self.msg}")
            print(linea)
            self.msg = ""
        print(f"  {istruzione}")
        print("  Hai sbagliato? Premi CANC (o Backspace) e poi Invio, oppure scrivi u")
        print("  Scrivi fine per concludere   |   q per uscire senza salvare")
        print(linea)
        print()

    # ---------- comandi ----------
    def conferma(self, domanda):
        try:
            tipo, v = leggi_riga(domanda)
        except EOFError:
            return False
        return tipo == "testo" and v.lower() in ("s", "si", "y", "yes")

    def _msg_undo(self, n):
        if n == 0:
            return "Non c'e' niente da annullare"
        return (f"Annullat{plurale(n, 'o', 'i')} {n} "
                f"{plurale(n, 'inserimento', 'inserimenti')}. "
                f"Bit raccolti ora: {self.s.total_bits()}")

    def gestisci(self, lettura):
        """Ritorna None se era un comando, altrimenti il testo da interpretare."""
        s = self.s
        tipo, v = lettura
        if tipo == "undo":
            self.msg = self._msg_undo(s.undo(v))
            return None
        low = v.strip().lower()
        if low in ("q", "quit", "esci"):
            if self.conferma("  Vuoi davvero uscire? Perderai tutto quello che hai inserito. (s/n) → "):
                print("\nUscita richiesta.")
                sys.exit(0)
            return None
        if low in ("u", "undo") or (low.startswith("u") and low[1:].isascii() and low[1:].isdigit()):
            self.msg = self._msg_undo(s.undo(1 if low in ("u", "undo") else int(low[1:])))
            return None
        if low in ("f", "fine"):
            if not s.esiti:
                self.msg = "Non hai ancora inserito niente: non c'e' nulla da concludere"
                return None
            avvisi = []
            if s.modo != "nessuna" and not s.soglia_raggiunta():
                avvisi.append(f"non hai ancora raggiunto l'obiettivo (bit stimati: {s.total_h():.1f})")
            if not s.fine_ciclo():
                avvisi.append("il giro non e' finito")
            if avvisi:
                print("  Attenzione: " + "; ".join(avvisi))
                if not self.conferma("  Concludere comunque? (s/n) → "):
                    return None
            self.termina = True
            return None
        return v

    # ---------- inserimenti ----------
    def processa(self, tipo, testo):
        s = self.s
        if tipo == "dado":
            if not (testo.isascii() and testo.isdigit()) or not 1 <= int(testo) <= 6:
                self.msg = "Non ho capito: scrivi un numero da 1 a 6"
                return
            v = int(testo)
            if v in (5, 6):
                s.rilancio(v)
                self.msg = f"Uscito {v}: rilancia il dado (nessun bit aggiunto)"
            else:
                s.aggiungi("dado", str(v), format(v - 1, "02b"))
        elif tipo == "moneta":
            up = testo.upper()
            if up in ("T", "0", "TESTA"):
                s.aggiungi("moneta", "T", "0")
            elif up in ("C", "1", "CROCE"):
                s.aggiungi("moneta", "C", "1")
            else:
                self.msg = "Non ho capito: scrivi T (testa) oppure C (croce)"
        else:
            if not (testo.isascii() and testo.isdigit()) or not 1 <= int(testo) <= 8:
                self.msg = "Non ho capito: scrivi un numero da 1 a 8"
                return
            v = int(testo)
            s.aggiungi("tombola", str(v), format(v - 1, "03b"))

    TESTI = {
        "dado": ("DADO", "Scrivi il numero uscito (da 1 a 6). Con 5 o 6 rilancia il dado.",
                 "  Dado → "),
        "moneta": ("MONETA", "Scrivi T se e' uscita testa, C se e' uscita croce.",
                   "  Moneta → "),
        "tombola": ("TOMBOLA", "Scrivi il numero estratto (da 1 a 8).",
                    "  Tombola → "),
    }

    # ---------- ciclo principale ----------
    def ciclo_principale(self):
        s = self.s
        while True:
            if self.termina or s.completato():
                if self.schermata_fine():
                    return
                self.termina = False
                continue
            tipo, i, n, ciclo = s.slot()
            nome, istr, prompt = self.TESTI[tipo]
            self.disegna(nome, istr, tipo,
                         f"(inserimento {i + 1} di {n} in questo giro)   giro numero {ciclo}")
            if usa_attributi():
                prompt = f"  {NEGATIVO} {prompt.strip()} {RESET} "
            cmd = self.gestisci(leggi_riga(prompt))
            if cmd is None:
                continue
            self.processa(tipo, cmd)

    def schermata_fine(self):
        s = self.s
        soglia_ok = s.soglia_raggiunta() if s.modo != "nessuna" else True
        self.disegna("RIEPILOGO FINALE",
                     "Premi Invio per confermare   |   scrivi u per annullare l'ultimo inserimento e continuare")
        stringa = s.bitstring()
        print(f"  Hai raccolto {s.total_bits()} bit.  Bit stimati (modello prudente): {s.total_h():.1f}")
        if s.modo != "nessuna":
            print("  Obiettivo raggiunto: " + ("SI" if soglia_ok else "NO"))
        print(f"  Rilanci del dado: {len(s.rilanci)}")
        c = s.conteggi()
        print("  Quante volte e' uscito ogni risultato (serve per controllo):")
        print(f"     moneta:       testa {c['moneta']['T']}   croce {c['moneta']['C']}")
        print("     dado 1-4:     " + "   ".join(f"{k}: {v}" for k, v in c["dado"].items()))
        print("     tombola 1-8:  " + "   ".join(f"{k}: {v}" for k, v in c["tombola"].items()))
        print(f"  Controllo interno dei dati: {'OK' if s.coerente() else 'ERRORE'}")
        print()
        print("  La tua sequenza di bit (copiala da qui):\n")
        print(sequenza_evidenziata(stringa))
        print(f"\n  Lunghezza: {len(stringa)} bit")
        print(f"  Impronta di controllo (SHA-256): {sha256_testo(stringa)}")
        print("  (serve a verificare che una copia sia identica all'originale)\n")
        self.avviso_entropypipeline()
        tipo, v = leggi_riga("  > ")
        if tipo == "undo" or v.lower() in ("u", "undo"):
            s.undo(1 if tipo == "testo" else v)
            return False
        return True

    def avviso_entropypipeline(self):
        bit = self.s.total_bits()
        print("  COSA FARE ORA: da solo il Generatore non basta. Questi bit vanno uniti ad altre")
        print("  sorgenti INDIPENDENTI con EntropyPipeline v2.0.0-beta6 o successiva (suite entropy-suite):")
        print("  incollali nella Fase 1 e prosegui con le Fasi 2, 3 e 4.")
        print(f"  SE USI SOLO IL GENERATORE servono circa {TOTALE_DEFAULT} bit in tutto.")
        if bit <= 0:
            print("  Questa esecuzione non ha ancora dato bit.")
        elif bit >= TOTALE_DEFAULT:
            print(f"  Questa esecuzione ha dato {bit} bit: da sola arriva a quel numero.")
        else:
            n = ripetizioni_necessarie(TOTALE_DEFAULT, bit)
            print(f"  Questa esecuzione ha dato {bit} bit: va ripetuta {n} VOLTE in tutto,")
            print(f"  cioe' ne mancano {n - 1}. Salva ogni esecuzione con un nome diverso e incolla i bit")
            print("  di tutte, una dopo l'altra, nella STESSA finestra di EntropyPipeline.")
        print()

    def salva(self):
        s = self.s
        soglia_ok = s.soglia_raggiunta() if s.modo != "nessuna" else True
        fine = datetime.datetime.now()
        if not self.conferma("  Vuoi salvare su file? (s/n) → "):
            return
        while True:
            _, v = leggi_riga("  Nome del file (Invio per usare bits.txt) → ")
            nome = v or "bits.txt"
            f_bit, f_reg = percorsi_salvataggio(nome)
            if os.path.exists(f_bit) or os.path.exists(f_reg):
                print(f"  Esiste gia' un file con questo nome ({f_bit} o {f_reg}).")
                print("  Non lo sovrascrivo: scegli un altro nome.")
                continue
            try:
                scrivi_esclusivo(f_bit, s.bitstring())
                scrivi_esclusivo(f_reg, testo_registro(s, self.inizio, fine, soglia_ok))
            except OSError as e:
                print(f"  Non sono riuscito a scrivere il file: {e}")
                if not self.conferma("  Riprovare con un altro nome? (s/n) → "):
                    return
                continue
            print("  Salvati:")
            print(f"     {f_bit}   (i bit, senza a capo finale)")
            print(f"     {f_reg}   (il diario di tutto quello che hai inserito)")
            print("  Sono riservati: contengono la tua sequenza. Custodiscili con cura")
            print("  e cancellali quando non servono piu'.")
            return

    def run(self):
        try:
            self.configura()
        except FineProgramma:
            print("\nUscita richiesta.")
            return
        with TastiDiretti():
            self.ciclo_principale()
            self.salva()


def main():
    try:
        Programma().run()
    except KeyboardInterrupt:
        print("\n\nInterrotto dall'utente.")
        sys.exit(0)
    except EOFError:
        print("\n\nIngresso terminato: uscita.")
        sys.exit(0)


if __name__ == "__main__":
    main()
