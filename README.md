# Generatore di bit da moneta, dado e tombola

> ⚠ **v2.9-beta — BETA non auditata.** Il programma e la pagina trasformano lanci e estrazioni reali in bit grezzi e ne stimano l'imprevedibilità con un modello prudente. **Non producono una chiave e, da soli, non bastano**: i bit vanno uniti ad altre sorgenti indipendenti con [EntropyPipeline](https://github.com/r0ck069/EntropyPipeline) v2.0.0-beta6 o successiva. **Non sono un generatore casuale per uso crittografico (CSPRNG)**: i «bit stimati» sono una stima con un modello prudente, non una prova di casualità. Non usare per nulla che conti davvero finché non è stato verificato da un revisore indipendente.

Strumento didattico della *entropy-suite*: la fonte fisica più semplice, quella che si tiene in mano e si controlla a occhio (una moneta, un dado, le palline numerate della tombola). Scrivere a mano centinaia di lanci su un foglio e convertirli in bit è lento e fa sbagliare: qui il programma toglie gli errori di trascrizione, registra tutto (annullamenti compresi) e dice in ogni momento quanti bit hai raccolto e quanti ne stima.

Esiste in due forme che fanno lo stesso calcolo:

- **`generatore_bit.py`**: programma da terminale (Python 3.7 o superiore, nessuna libreria da installare);
- **`generatore_bit.html`**: pagina standalone, offline, senza dipendenze esterne: apri il file in un browser moderno. Non invia e non salva nulla da sola: i bit si scaricano o si copiano.

---

## File

| File | Cosa contiene | SHA-256 |
|---|---|---|
| `generatore_bit.py` | programma da terminale, versione 2.9-beta | `337b4c07031d435cbf41555d1b2b08c4469ac35083f34507349831a8960b60a1` |
| `generatore_bit.html` | pagina standalone, versione 2.9-beta | `a8126b93cf1d255317748718cc330ca4350be24a2e03e0ba7f299d69fd8353d4` |
| `Guida_Generatore_Bit.md` | guida completa (regole, modello di stima, soglie, comandi) | `400d337247e415bb3b63ed7e94030caae43b619333d6fffb8c619b319f2c7991` |
| `verifica/` | script di prova (Python e Node.js), vedi `verifica/LEGGIMI.md` | — |
| `CHANGELOG.md` | cronologia | — |
| `SHA256SUMS.txt` | impronte di tutti i file del repository (tranne se stesso) | — |

Controlla i file con `sha256sum -c SHA256SUMS.txt`. Il blocco `<script id="core-script">` della pagina ha SHA-256 `267bb5ccc3a651198dd5a685a099ada34ee1886af0120f6b16917cddfdc05a1a`: è il valore che la scheda «Integrità» della pagina mostra al caricamento.

---

## Come funziona

Ogni risultato diventa bit con una regola fissa:

| Fonte | Si inserisce | Bit prodotti |
|---|---|---|
| Moneta | T (testa), C (croce) | 0, 1 |
| Dado a 6 facce | 1, 2, 3, 4 | 00, 01, 10, 11 (con 5 o 6 si rilancia, nessun bit) |
| Tombola, numeri 1-8 | da 1 a 8 | da 000 a 111 (il numero meno 1, in binario) |

**Attenzione al dado.** Il testo `procedura operativa` del repository `document` consiglia per il dado una mappatura a 1 bit; questo programma e la pagina usano **2 bit** per lancio valido (tabella qui sopra). Per una sessione fatta con il Generatore vale la mappatura a 2 bit: gli stessi lanci convertiti a mano con la mappatura a 1 bit danno bit diversi.

Un **giro** è una serie sempre uguale di inserimenti: scegli tu quante monete, quanti dadi validi e quante palline per giro (per esempio 1 + 1 + 1 = 6 bit). **In ogni giro si inseriscono prima tutte le monete, poi tutti i dadi, poi tutte le tombole**; finito il giro, se la soglia non è raggiunta, il giro si ripete nello stesso ordine. I bit sono accodati nell'ordine d'inserimento, senza XOR, hash o scarti.

Sullo schermo, a ogni passo: bit raccolti, bit stimati, la prudenza scelta (solo il nome, per esempio PRUDENTE) e la riga «Ora tocca a», con la fonte da inserire in negativo (colori invertiti, in grassetto). Nel riepilogo finale la sequenza di bit è evidenziata in giallo. Per correggere un errore: CANC o Backspace e poi Invio, oppure `u`; `fine` conclude, `q` esce senza salvare. Alla fine si possono salvare due file mai sovrascritti: i bit e un registro con tutto ciò che è stato inserito.

---

## Per un esito robusto: mescola bene e fai ruotare bene

Il programma conta i bit, non può controllare come li ottieni. Le stime valgono solo se ogni lancio è indipendente dagli altri.

- **Dado**: mescolalo bene, almeno 3 secondi in un contenitore chiuso che gli lasci rotolare liberamente; solo dopo leggi l'esito.
- **Tombola**: mescola bene le palline; reinserisci la pallina dopo ogni estrazione e mescola almeno 5 secondi prima della successiva, in un sacchetto abbastanza ampio.
- **Moneta**: falla ruotare bene in aria (meglio una moneta da 2 euro), senza decidere a mente. Una moneta lanciata a mano tende comunque a ricadere sulla faccia di partenza (50,8% misurato su 350.757 lanci, Bartoš e altri, 2023): il profilo «prudente» assume al massimo il 51%, il «molto prudente» il 52%, e senza una buona rotazione non c'è nessuna garanzia che l'ipotesi valga.

Decidi la tecnica prima di cominciare e tienila uguale per tutti i lanci. Non scartare e non ripetere un esito dopo averlo visto: l'unico rilancio previsto è quello del dado con 5 o 6. Le regole complete sono nella guida.

---

## Quanti bit servono

- Con il profilo «prudente» e 1 moneta, 1 dado e 1 pallina per giro servono 67 giri (402 bit) per stimare 384 bit, la soglia consigliata per ricavare 256 bit con un estrattore Toeplitz (errore ε = 2^-64).
- Se usi **solo** il Generatore, EntropyPipeline v2.0.0-beta6 o successiva chiede circa 1200 bit grezzi (circa 200 giri da 6 bit) per ricavare 256 bit; il programma e la pagina scrivono quante volte va ripetuta l'esecuzione. Questo numero viene da simulazioni con fonti ideali, non da misure su dadi veri. Con versioni precedenti di EntropyPipeline i numeri non valgono.
- Con altre sorgenti indipendenti ne servono meno: lo dice la Fase 4 di EntropyPipeline.

---

## Cosa è verificato e cosa no

Gli script di prova sono nella cartella `verifica/`: `python3 verifica/esegui_tutto.py` (servono Python 3 e Node.js; vedi `verifica/LEGGIMI.md`). Le prove dell'autore che richiedono un browser comandato da programma non sono nel repository.

**Verificato (ambiente di prova dell'autore, 05/10/2026, versione 2.9-beta):**
- programma: valori di riferimento del modello e coerenza interna su 645 configurazioni; ordine moneta, dado, tombola, bit, annullamenti e soglia a fine giro in 400 sessioni casuali (280.000 passi) confrontate con un modello indipendente; esecuzione completa con ingresso da pipe; le quattro scelte di prudenza; su Linux, un terminale simulato con i tasti, il negativo di «Ora tocca a» e il giallo della sequenza;
- pagina HTML, in Node.js: 15 controlli all'avvio su 15; 1500 sessioni casuali identiche al programma (bit, bit stimati, posizione, soglie, conteggi; testo del registro identico in 1500 su 1500); SHA-256 uguale su 300 stringhe; giri, bit e ripetizioni uguali su 126 configurazioni; validazione dell'input su 180.081 stringhe, anche avversarie, con 0 anomalie e senza `innerHTML` né `eval` nella pagina;
- pagina HTML, in Chromium: 24 prove sull'interfaccia, nessun errore in console e nessuna richiesta di rete;
- cambio d'ordine (da dado, moneta, tombola a moneta, dado, tombola): con la pagina EntropyPipeline beta6 su 1200 bit simulati e 600 prove accoppiate, da 1,6 a 4,0 bit in meno su circa 699, entro un errore standard, quindi non distinguibile da zero;
- gli script sono stati controllati anche al contrario, introducendo errori di proposito: li rilevano.

**Provato dall'autore sul Raspberry Pi il 04/10/2026, nella versione 2.8:** il programma «funziona»; la pagina in Firefox: 15 controlli su 15, impronta del codice corretta, due sessioni con sequenza e impronta SHA-256 coincidenti con quelle calcolate a parte (`110110` e `001000`), aspetto del negativo e del giallo confermato. La 2.9-beta cambia solo testi e aggiunge la cartella `verifica/`. **Sul Pi, il 05/10/2026, nella versione 2.9-beta:** gli script di `verifica/` (Python 3.13.5, Node.js 20.19.2) con tutte le prove superate, cioè programma 8 su 8, pagina 15 controlli su 15, 1500 sessioni identiche al programma, SHA-256 su 300 stringhe, 126 configurazioni e 180.081 stringhe di input senza anomalie; la pagina 2.9-beta **non è ancora stata aperta in Firefox sul Pi**.

**Provato dall'autore su Windows il 05/10/2026, nella versione 2.9-beta:** Su Windows, il 05/10/2026 (Python 3.14.8, PowerShell 5), il programma: gli script di `verifica/` (7 prove su 7; la prova con terminale simulato viene saltata perché serve Linux o Mac); una sessione interattiva a risultato non noto (profilo personalizzato, 2 monete, 1 dado e 2 tombole per giro, 30 bit, un rilancio, annullamenti con Canc e con `u`), con sequenza, SHA-256, bit stimati (anche i valori intermedi) e conteggi uguali al modello; il Backspace, provato a parte, annulla l'ultimo inserimento; input sbagliati gestiti; salvataggio verificato (l'impronta del file calcolata da Windows è uguale a quella del registro, quindi nessun a capo finale né conversioni); aspetto di «Ora tocca a» in negativo e della sequenza in giallo confermato.

Su Windows, la pagina 2.9-beta in tre browser, con tre sessioni a risultato non noto in anticipo (l'atteso era calcolato da Claude e non rivelato): Edge (12 bit, un rilancio, un annullamento), Chrome (2 monete, 2 dadi e 1 tombola per giro, 18 bit, due rilanci, `testa` e `croce` scritti per esteso, un annullamento) e Firefox (profilo molto prudente, 1 moneta, 3 dadi e 2 tombole per giro, arresto manuale a metà giro con conferma, due rilanci, un annullamento). In tutte e tre sequenza o impronta SHA-256, bit stimati, rilanci, conteggi, ripetizioni e controllo interno coincidono con il modello, con 15 controlli su 15 e l'impronta del codice attesa. Il giallo è confermato nei tre browser; «Ora tocca a» in nero è confermato in Chrome e in Firefox, non in Edge (l'autore non lo ricorda). Nella prova in Firefox il testo copiato non conteneva la sequenza in chiaro, quindi la sequenza è confermata dall'impronta SHA-256.

**Non verificato:** sessioni con lanci fisici veri; il programma su Mac e su Windows in terminali diversi da PowerShell 5; la pagina HTML 2.9-beta aperta in Firefox sul Pi; la pagina su Safari, Android e iPhone; l'aspetto di «Ora tocca a» in nero su Edge (non ricordato dall'autore).

---

## Limiti noti

- Non estrae né mescola: da solo non basta, e non è un CSPRNG.
- La stima vale solo se le ipotesi valgono (indipendenza dei lanci, scostamento massimo di dadi e palline, probabilità della moneta): con poche decine di lanci non si può dimostrare che un dado sia equilibrato. I valori d = 5%, d = 10% e p = 52% sono ipotesi prudenti, non misure.
- Il confronto tra i modi di accodare i bit riguarda solo fonti simulate e indipendenti.
- La soglia «per la verifica statistica» (circa 700-880 bit grezzi per 384 bit, misurata con lo strumento ufficiale NIST `ea_non_iid`) non è calcolata dal programma.
- Il dado usa 4 facce su 6 e rende 1,33 bit per lancio fisico.
- Le stringhe e il registro restano visibili a schermo e nei file: usa una macchina e un ambiente di cui ti fidi.
- Se l'uscita del programma viene reindirizzata (su un file o in una pipe) e il sistema usa una codifica che non è UTF-8 (su Windows cp1252 o cp850, su Linux `LANG=C`), il programma si ferma subito con `UnicodeEncodeError`, prima che sia stato inserito qualcosa. Nel terminale interattivo non succede (provato su Windows, PowerShell 5). Rimedio: imposta prima `PYTHONUTF8=1` (PowerShell: `$env:PYTHONUTF8="1"`; bash: `export PYTHONUTF8=1`). Gli script di `verifica/` lo impostano da soli. Verificato in simulazione su Linux con le codifiche cp1252 e cp850; non provato su un Windows reale senza `PYTHONUTF8`.

---

## Revisione automatica (GitHub Copilot, 04/10/2026)

Il 04/10/2026 GitHub Copilot ha eseguito una revisione di `generatore_bit.html` v2.8. È una revisione automatica, **non** un audit umano indipendente: i suoi rilievi sono stati controllati sul codice e, dove possibile, provati.

- **Recepito, come testo:** l'avviso che non è un CSPRNG e che i bit stimati sono una stima con un modello prudente; la parola «sicuri» tolta ovunque; la cartella `verifica/`.
- **Non adottato:** una CSP basata su hash (la pagina parte ma Chromium ignora 4 attributi `style=` e l'aspetto cambia; chi può modificare il file può modificare anche la CSP); un controllo dell'impronta del codice scritto dentro lo script (non può mai coincidere con l'impronta del blocco che lo contiene, provato; l'ancora di verifica è esterna, cioè `SHA256SUMS.txt` e le impronte del CHANGELOG); la riscrittura della validazione dell'input (già a lista di valori ammessi, 0 anomalie su 180.081 stringhe); un'intestazione sui bit copiati (EntropyPipeline respinge il testo); la sovrascrittura della memoria dopo il download (azzererebbe i bit ancora in uso: `110110` diventava `000000`); una catena di hash e un log in console (nessun beneficio verificabile per questo uso).

---

## Licenza

MIT, vedi `LICENSE`. Parte della *entropy-suite*, nata dal caso COLDCARD di agosto 2026 e dall'idea di costruire un metodo alternativo con strumenti casalinghi e matematica, senza pretese di uso reale. Solo per usi didattici.
