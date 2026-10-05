#!/usr/bin/env python3
"""
Prove sul programma generatore_bit.py. Solo libreria standard di Python 3 (3.7 o superiore).
Uso, dalla cartella del repository:   python3 verifica/prove_programma.py
Esito 0 se tutte le prove passano, 1 altrimenti. Le prove con terminale simulato girano solo su Linux/Mac.
"""
import hashlib, importlib.util, itertools, math, os, random, re, subprocess, sys, tempfile, time
from pathlib import Path

sys.dont_write_bytecode = True      # non lasciare __pycache__ nel repository
RADICE = Path(__file__).resolve().parent.parent
PROGRAMMA = RADICE / "generatore_bit.py"
spec = importlib.util.spec_from_file_location("gb", PROGRAMMA)
G = importlib.util.module_from_spec(spec); spec.loader.exec_module(G)
ANSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
COLORE = re.compile(r"\x1b\[[0-9;]*m")
risultati = []

def prova(nome):
    def deco(f):
        print("... in corso: " + nome.split(")")[0] + ")", flush=True)
        t0 = time.time()
        try:
            dettaglio, ok = f() or "", True
        except AssertionError as e:
            dettaglio, ok = "ASSERT: %s" % (e,), False
        except Exception as e:
            dettaglio, ok = "ERRORE: %r" % (e,), False
        risultati.append((nome, ok, dettaglio))
        print(("OK  " if ok else "NO  ") + nome + ((" -> " + dettaglio) if dettaglio else "") + "  [%.1f s]" % (time.time() - t0), flush=True)
        return f
    return deco

# ---------------------------------------------------------------- A) modello e conti
@prova("A) modello, giri e ripetizioni (valori di riferimento e coerenza interna)")
def _():
    p = G.PROFILI["2"]
    assert (round(p.h_dado(), 4), round(p.h_moneta(), 4), round(p.h_tombola(), 4)) == (1.8931, 0.9714, 2.9296)
    assert round(G.h_ciclo(p, 1, 1, 1), 4) == 5.7941
    attesi = {"1": (54, 64, 70), "2": (56, 67, 72), "3": (58, 69, 75)}
    for k, trio in attesi.items():
        hc = G.h_ciclo(G.PROFILI[k], 1, 1, 1)
        assert tuple(G.cicli_per(t, hc) for t in (320, 384, 416)) == trio, (k, trio)
    assert [G.ripetizioni_necessarie(1200, b) for b in (360, 402, 1200, 6)] == [4, 3, 1, 200]
    n = 0
    for k in G.PROFILI:
        P = G.PROFILI[k]
        for nd, nm, nt in itertools.product(range(0, 6), repeat=3):
            if nd + nm + nt == 0: continue
            assert abs(G.h_ciclo(P, nd, nm, nt) - (nd * P.h_dado() + nm * P.h_moneta() + nt * P.h_tombola())) < 1e-9
            assert G.bit_ciclo(nd, nm, nt) == 2 * nd + nm + 3 * nt
            giri, bit = G.bit_per_esecuzione(P, nd, nm, nt, "entropia", 384)[:2]
            hc = G.h_ciclo(P, nd, nm, nt)
            assert giri * hc >= 384 - 1e-9 and (giri - 1) * hc < 384, (k, nd, nm, nt)
            assert bit == giri * G.bit_ciclo(nd, nm, nt)
            n += 1
    return "%d configurazioni controllate" % n

# ---------------------------------------------------------------- B) ordine, bit, annullamenti, soglia
COD = {"dado": lambda v: format(v - 1, "02b"), "moneta": lambda v: "0" if v == "T" else "1", "tombola": lambda v: format(v - 1, "03b")}
def esito_casuale(r, tipo):
    return r.randint(1, 4) if tipo == "dado" else (r.choice("TC") if tipo == "moneta" else r.randint(1, 8))

@prova("B) ordine moneta-dado-tombola, bit, annullamenti e soglia a fine giro (400 sessioni casuali)")
def _():
    passi = 0
    for seme in range(400):
        r = random.Random(seme)
        nd, nm, nt = r.randint(0, 4), r.randint(0, 4), r.randint(0, 4)
        if nd + nm + nt == 0: nm = 1
        prof = G.PROFILI[r.choice("123")]
        modo, soglia = r.choice([("entropia", 384), ("bit", 480), ("nessuna", 0), ("bit", 40)])
        S = G.Sessione(prof, nd, nm, nt, modo, soglia)
        assert S.fasi == [(t, n) for t, n in (("moneta", nm), ("dado", nd), ("tombola", nt)) if n > 0]
        attesi = []
        ciclo = ["moneta"] * nm + ["dado"] * nd + ["tombola"] * nt
        for _ in range(700):
            passi += 1
            if r.random() < 0.12 and attesi:
                k = r.randint(1, 5); reale = S.undo(k); tolti = min(k, G.MAX_UNDO, len(attesi))
                assert reale == tolti; del attesi[len(attesi) - tolti:]
            else:
                tipo = S.slot()[0]
                assert tipo == ciclo[len(attesi) % len(ciclo)], "ordine"
                assert S.slot()[3] == len(attesi) // len(ciclo) + 1, "numero del giro"
                v = esito_casuale(r, tipo); S.aggiungi(tipo, str(v), COD[tipo](v)); attesi.append((tipo, str(v), COD[tipo](v)))
            assert S.esiti == attesi
            assert S.bitstring() == "".join(b for _, _, b in attesi) and S.total_bits() == len(S.bitstring())
            assert abs(S.total_h() - sum(prof.h(t) for t, _, _ in attesi)) < 1e-9
            assert S.coerente()
            assert S.fine_ciclo() == (len(attesi) > 0 and len(attesi) % len(ciclo) == 0)
            if S.completato(): assert S.fine_ciclo(), "concluso solo a fine giro"
    return "%d passi" % passi

@prova("C) esempio della guida: moneta C, dado 5 (rilancio) poi 3, tombola 7 -> 110110")
def _():
    S = G.Sessione(G.PROFILI["2"], 1, 1, 1, "bit", 6)
    S.aggiungi("moneta", "C", "1"); S.rilancio(5); S.aggiungi("dado", "3", "10"); S.aggiungi("tombola", "7", "110")
    assert S.bitstring() == "110110" and S.completato()
    assert G.sha256_testo("110110") == hashlib.sha256(b"110110").hexdigest()

# ---------------------------------------------------------------- D) programma intero con ingresso da pipe
def esegui_pipe(righe, env_extra=None):
    with tempfile.TemporaryDirectory() as d:
        env = dict(os.environ); env.pop("NO_COLOR", None); env["PYTHONUTF8"] = "1"   # uscita sempre in UTF-8, anche su Windows
        if env_extra: env.update(env_extra)
        r = subprocess.run([sys.executable, str(PROGRAMMA)], input="\n".join(righe) + "\n", capture_output=True,
                           encoding="utf-8", cwd=d, timeout=60, env=env)
        file = {f: open(os.path.join(d, f), encoding="utf-8").read() for f in os.listdir(d)}
    return r, ANSI.sub("", r.stdout), file

@prova("D1) esecuzione completa da pipe: ordine delle richieste, bit salvati, registro")
def _():
    ing = ["2", "2", "2", "1", "2", "18", "C", "T", "5", "3", "1", "7", "T", "T", "4", "2", "1", "", "s", "prova.txt"]
    r, out, file = esegui_pipe(ing)
    assert r.returncode == 0, r.stderr[-300:]
    attesi = "1" + "0" + "10" + "00" + "110" + "0" + "0" + "11" + "01" + "000"
    assert file.get("prova.txt") == attesi, (file.get("prova.txt"), attesi)
    assert out.index("Lanci di MONETA per giro") < out.index("Lanci validi di DADO per giro") < out.index("Estrazioni di TOMBOLA per giro")
    ora = re.findall(r"Ora tocca a: ► (\w+) ◄", out)
    assert ora == ["MONETA", "MONETA", "DADO", "DADO", "DADO", "TOMBOLA", "MONETA", "MONETA", "DADO", "DADO", "TOMBOLA"], ora
    reg = file["prova_registro.txt"]
    for s in ("REGISTRO GENERATORE BIT v" + G.VERSIONE, "Per ciclo, nell'ordine di inserimento: moneta 2, dado 2 esiti validi, tombola 1",
              "min-entropia stimata per esito: moneta 0.9714 (su 1 bit), dado 1.8931 (su 2 bit), tombola 2.9296 (su 3 bit)",
              "Coerenza cronologia/esiti: OK", "Bit totali: 18", "Bit stimati (min-entropia, modello prudente):"):
        assert s in reg, s
    assert re.search(r"SHA-256 della stringa di bit: (\w+)", reg).group(1) == hashlib.sha256(attesi.encode()).hexdigest()
    assert "va ripetuta 67 VOLTE" in re.sub(r"\s+", " ", reg) or "67 volte" in re.sub(r"\s+", " ", reg)
    assert not COLORE.findall(r.stdout), "in modo pipe non devono comparire codici colore"
    assert "sicur" not in out.lower().replace("sicurezza", ""), "compare ancora la parola 'sicuri'"

@prova("D2) le quattro scelte di prudenza: a schermo solo il nome in maiuscolo")
def _():
    for scelta, extra, nome in [("1", [], "SOLO PROVA"), ("2", [], "PRUDENTE"), ("3", [], "MOLTO PRUDENTE"), ("4", ["5", "51"], "PERSONALIZZATO")]:
        r, out, _f = esegui_pipe([scelta] + extra + ["1", "1", "1", "2", "6", "C", "3", "7", "", "n"])
        assert r.returncode == 0 and "Prudenza:" not in out
        righe = [l.strip() for l in out.splitlines()]
        idx = [i for i, l in enumerate(righe) if l.startswith("Ora tocca a")]
        assert idx and all(righe[i - 1] == nome for i in idx), (nome, [righe[i - 1] for i in idx])
    return "4 scelte controllate"

@prova("D3) avviso: non e' un CSPRNG, i bit stimati sono una stima (compare all'avvio)")
def _():
    r, out, _f = esegui_pipe(["q"])
    t = re.sub(r"\s+", " ", out)
    assert "CSPRNG" in t and "non una prova di casualita'" in t, t[:300]

# ---------------------------------------------------------------- E) terminale simulato (Linux/Mac)
if os.name == "posix":
    import pty, select
    def sessione_pty(passi, env_extra=None, attesa_fine=0.8):
        pid, fd = pty.fork()
        if pid == 0:
            os.environ.pop("NO_COLOR", None); os.environ.update({"TERM": "xterm", "PYTHONUTF8": "1", **(env_extra or {})})
            d = tempfile.mkdtemp(); os.chdir(d); os.execv(sys.executable, [sys.executable, str(PROGRAMMA)])
        buf = ""
        def leggi(t):
            nonlocal buf
            fine = time.time() + t
            while time.time() < fine:
                if select.select([fd], [], [], 0.05)[0]:
                    try: buf += os.read(fd, 65536).decode("utf-8", "replace")
                    except OSError: return
        for atteso, invio in passi:
            fine = time.time() + 10
            while atteso not in ANSI.sub("", buf) and time.time() < fine: leggi(0.1)
            assert atteso in ANSI.sub("", buf), "manca: %s | ultimo output: %r" % (atteso, buf[-160:])
            for ch in invio: os.write(fd, ch.encode()); time.sleep(0.03)
        leggi(attesa_fine)
        try: os.kill(pid, 9)
        except OSError: pass
        os.waitpid(pid, 0)
        return buf
    NEG, GIALLO = "\x1b[1;7m", "\x1b[30;43m"
    PREP = [("scelta [2]", "2\r"), ("MONETA per giro", "1\r"), ("DADO per giro", "1\r"), ("TOMBOLA per giro", "1\r"),
            ("scelta [1]", "2\r"), ("raccogliere", "6\r")]

    @prova("E1) terminale simulato: tasti (Backspace, Canc, Invio), rilancio, negativo e giallo")
    def _():
        passi = PREP + [("Moneta", "C\r"), ("Dado", "\x7f\r"), ("Annullato 1 inserimento", ""), ("Moneta", "T\r"), ("Dado", "5\r"),
                        ("rilancia il dado", ""), ("Dado", "3\r"), ("Tombola", "\x1b[3~\r"), ("Annullato 1 inserimento", ""),
                        ("Dado", "3\r"), ("Tombola", "7\r"), ("Impronta di controllo", "")]
        buf = sessione_pty(passi)
        for nome in ("MONETA", "DADO", "TOMBOLA"):
            assert NEG + " ► " + nome + " ◄ " + "\x1b[0m" in buf, ("negativo", nome)
        assert GIALLO + "010110" + "\x1b[0m" in buf, "sequenza finale non evidenziata in giallo"

    @prova("E2) NO_COLOR toglie solo il giallo; TERM=dumb toglie ogni codice")
    def _():
        passi = PREP + [("Moneta", "C\r"), ("Dado", "3\r"), ("Tombola", "7\r"), ("Impronta di controllo", "")]
        b = sessione_pty(passi, {"NO_COLOR": "1"})
        assert NEG + " ► MONETA ◄ " in b and GIALLO not in b and "110110" in ANSI.sub("", b)
        b = sessione_pty(passi, {"TERM": "dumb"})
        assert "► MONETA ◄" in b and not ANSI.findall(b.replace("\x1b[2J\x1b[H", "")) and "110110" in b
else:
    risultati.append(("E) terminale simulato", True, "saltato: serve Linux o Mac"))
    print("OK  E) terminale simulato -> saltato: serve Linux o Mac", flush=True)

# ---------------------------------------------------------------- riepilogo
ok = sum(1 for _, v, _ in risultati if v)
print("\nPROVE SUL PROGRAMMA: %d su %d superate" % (ok, len(risultati)))
sys.exit(0 if ok == len(risultati) else 1)
