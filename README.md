# Generatore di bit da moneta, dado e tombola

> ⚠ **v2.8 — BETA non auditata.** Il programma e la pagina trasformano lanci e estrazioni reali in bit grezzi e stimano, con un modello prudente, quanti sono davvero imprevedibili. **Non producono una chiave e, da soli, non bastano**: i bit vanno uniti ad altre sorgenti indipendenti con [EntropyPipeline](https://github.com/r0ck069/EntropyPipeline) v2.0.0-beta6 o successiva. Non usare per nulla che conti davvero finché non è stato verificato da un revisore indipendente.

Strumento didattico della *entropy-suite*: la fonte fisica più semplice, quella che si tiene in mano e si controlla a occhio (una moneta, un dado, le palline numerate della tombola). Scrivere a mano centinaia di lanci su un foglio e convertirli in bit è lento e fa sbagliare: qui il programma toglie gli errori di trascrizione, registra tutto (annullamenti compresi) e dice in ogni momento quanto si è raccolto davvero.

Esiste in due forme che fanno lo stesso calcolo:

- **`generatore_bit.py`**: programma da terminale (Python 3.7 o superiore, nessuna libreria da installare);
- **`generatore_bit.html`**: pagina standalone, offline, senza dipendenze esterne: apri il file in un browser moderno. Non invia e non salva nulla da sola: i bit si scaricano o si copiano.

---

## File

| File | Cosa contiene | SHA-256 |
|---|---|---|
| `generatore_bit.py` | programma da terminale, versione 2.8 | `f26491a567a81e1c964f7560b0480e3600b28b544ea8e6d0da8b08fd3fb9bdfc` |
| `generatore_bit.html` | pagina standalone, versione 2.8 | `4b888be0450a8544234fb46a01b6b47ab51fbcd6476de84e382a9df9d757f33f` |
| `Guida_Generatore_Bit.md` | guida completa (regole, modello di stima, soglie, comandi) | `411eba3e87d4df82ec3279e63582a4c56726d7771871b1aa6a17f66ef28f9b02` |
| `CHANGELOG.md` | cronologia | — |
| `SHA256SUMS.txt` | impronte dei file del repository | — |

Controlla i file con `sha256sum -c SHA256SUMS.txt`. Il blocco `<script id="core-script">` della pagina ha SHA-256 `5c463197d0cd756d329a723ad8b23256965ef712d2b1444128bc677a9528067a`: è il valore che la scheda «Integrità» della pagina mostra al caricamento.

---

## Come funziona

Ogni risultato diventa bit con una regola fissa:

| Fonte | Si inserisce | Bit prodotti |
|---|---|---|
| Moneta | T (testa), C (croce) | 0, 1 |
| Dado a 6 facce | 1, 2, 3, 4 | 00, 01, 10, 11 (con 5 o 6 si rilancia, nessun bit) |
| Tombola, numeri 1-8 | da 1 a 8 | da 000 a 111 (il numero meno 1, in binario) |

Un **giro** è una serie sempre uguale di inserimenti: scegli tu quante monete, quanti dadi validi e quante palline per giro (per esempio 1 + 1 + 1 = 6 bit). **In ogni giro si inseriscono prima tutte le monete, poi tutti i dadi, poi tutte le tombole**; finito il giro, se la soglia non è raggiunta, il giro si ripete nello stesso ordine. I bit sono accodati nell'ordine d'inserimento, senza XOR, hash o scarti.

Sullo schermo, a ogni passo: bit raccolti, bit sicuri stimati, la prudenza scelta (solo il nome, per esempio PRUDENTE) e la riga «Ora tocca a», con la fonte da inserire in negativo (colori invertiti, in grassetto). Nel riepilogo finale la sequenza di bit è evidenziata in giallo. Per correggere un errore: CANC o Backspace e poi Invio, oppure `u`; `fine` conclude, `q` esce senza salvare. Alla fine si possono salvare due file mai sovrascritti: i bit e un registro con tutto ciò che è stato inserito.

---

## Per un esito robusto: mescola bene e fai ruotare bene

Il programma conta i bit, non può controllare come li ottieni. I «bit sicuri» valgono solo se ogni lancio è indipendente dagli altri.

- **Dado**: mescolalo bene, almeno 3 secondi in un contenitore chiuso che gli lasci rotolare liberamente; solo dopo leggi l'esito.
- **Tombola**: mescola bene le palline; reinserisci la pallina dopo ogni estrazione e mescola almeno 5 secondi prima della successiva, in un sacchetto abbastanza ampio.
- **Moneta**: falla ruotare bene in aria (meglio una moneta da 2 euro), senza decidere a mente. Una moneta lanciata a mano tende comunque a ricadere sulla faccia di partenza (50,8% misurato su 350.757 lanci, Bartoš e altri, 2023): il profilo «prudente» assume al massimo il 51%, il «molto prudente» il 52%, e senza una buona rotazione non c'è nessuna garanzia che l'ipotesi valga.

Decidi la tecnica prima di cominciare e tienila uguale per tutti i lanci. Non scartare e non ripetere un esito dopo averlo visto: l'unico rilancio previsto è quello del dado con 5 o 6. Le regole complete sono nella guida.

---

## Quanti bit servono

- Con il profilo «prudente» e 1 moneta, 1 dado e 1 pallina per giro servono 67 giri (402 bit) per stimare 384 bit sicuri, la soglia consigliata per ricavare 256 bit con un estrattore Toeplitz (errore ε = 2^-64).
- Se usi **solo** il Generatore, EntropyPipeline v2.0.0-beta6 o successiva chiede circa 1200 bit grezzi (circa 200 giri da 6 bit) per ricavare 256 bit; il programma e la pagina scrivono quante volte va ripetuta l'esecuzione. Questo numero viene da simulazioni con fonti ideali, non da misure su dadi veri. Con versioni precedenti di EntropyPipeline i numeri non valgono.
- Con altre sorgenti indipendenti ne servono meno: lo dice la Fase 4 di EntropyPipeline.

---

## Cosa è verificato e cosa no

Le prove sono state eseguite dall'autore in un ambiente di prova; gli script di prova non sono in questo repository.

**Verificato:**
- il calcolo del programma 2.8 è identico alla 2.4 (8.241 controlli su profili, quantità per giro, soglie e ripetizioni);
- ordine moneta, dado, tombola, bit, annullamenti e soglia a fine giro: 400 sessioni casuali (280.000 passi) confrontate con un modello indipendente; esecuzione completa con ingresso da pipe e con terminale simulato;
- pagina HTML: 15 controlli all'avvio su 15; in Node.js, 1500 sessioni casuali identiche al programma Python (bit, bit sicuri, posizione, soglie, conteggi; testo del registro identico in 1500 su 1500), SHA-256 uguale su 300 stringhe; in Chromium, 21 prove su 21 sull'interfaccia, nessun errore in console e nessuna richiesta di rete;
- cambio d'ordine (da dado, moneta, tombola a moneta, dado, tombola): con la pagina EntropyPipeline beta6 su 1200 bit simulati e 600 prove accoppiate, da 1,6 a 4,0 bit in meno su circa 699, entro un errore standard, quindi non distinguibile da zero;
- una prova sul Raspberry Pi dell'autore il 04/10/2026 con il programma 2.8: «funziona».

**Non verificato:** sessioni con lanci fisici veri; Mac e Windows (su Windows il codice usa una via per i tasti mai eseguita); la pagina HTML 2.8 su Firefox, Safari, Android, iPhone e Raspberry Pi (provata solo in Chromium e Node.js); l'aspetto del negativo e del giallo su un terminale o un browser veri.

---

## Limiti noti

- Non estrae né mescola: da solo non basta.
- La stima dei bit sicuri vale solo se le ipotesi valgono (indipendenza dei lanci, scostamento massimo di dadi e palline, probabilità della moneta): con poche decine di lanci non si può dimostrare che un dado sia equilibrato. I valori d = 5%, d = 10% e p = 52% sono ipotesi prudenti, non misure.
- Il confronto tra i modi di accodare i bit riguarda solo fonti simulate e indipendenti.
- La soglia «per la verifica statistica» (circa 700-880 bit grezzi per 384 bit, misurata con lo strumento ufficiale NIST `ea_non_iid`) non è calcolata dal programma.
- Il dado usa 4 facce su 6 e rende 1,33 bit per lancio fisico.
- Le stringhe e il registro restano visibili a schermo e nei file: usa una macchina e un ambiente di cui ti fidi.
- I documenti di cerimonia dell'autore (il protocollo dei 60 turni e la procedura operativa) fissano ancora l'ordine pallina, dado, moneta; questo strumento usa moneta, dado, tombola: a parità di lanci la sequenza di bit è diversa.

---

## Licenza

MIT, vedi `LICENSE`. Parte della *entropy-suite*, nata dal caso COLDCARD di agosto 2026 e dall'idea di costruire un metodo alternativo con strumenti casalinghi e matematica, senza pretese di uso reale. Solo per usi didattici.
