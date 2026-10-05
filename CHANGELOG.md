# Changelog — Generatore di bit da moneta, dado e tombola

## v2.9-beta (2026-10-05) — testi più prudenti, cartella di prove, nota sulla revisione di Copilot

- `generatore_bit.py` — SHA-256: `337b4c07031d435cbf41555d1b2b08c4469ac35083f34507349831a8960b60a1`
- `generatore_bit.html` — SHA-256: `a8126b93cf1d255317748718cc330ca4350be24a2e03e0ba7f299d69fd8353d4`; blocco `<script id="core-script">`: `267bb5ccc3a651198dd5a685a099ada34ee1886af0120f6b16917cddfdc05a1a`
- `Guida_Generatore_Bit.md` — SHA-256: `400d337247e415bb3b63ed7e94030caae43b619333d6fffb8c619b319f2c7991`

**Cosa cambia.** Calcolo, bit e regole sono invariati rispetto alla v2.8: cambiano testi e documentazione, e si aggiunge la cartella `verifica/`.
- **«bit sicuri» diventa «bit stimati»** in tutto il programma, nella pagina, nel registro, nella guida e nel README, perché «sicuri» dava un'impressione di garanzia che la stima non offre; «più sicuro» diventa «più prudente» e, nell'elenco dei controlli della pagina, i nomi di file «resi sicuri» diventano «normalizzati». Le voci storiche di questo CHANGELOG e della guida sulle versioni passate non sono state riscritte.
- **Nuovo avviso** (avvio del programma, pagina, guida, README): non è un generatore casuale per uso crittografico (CSPRNG) e i bit stimati sono una stima con un modello prudente, non una prova di casualità.
- **Pagina:** il sottotitolo dice che la pagina è stata provata su Firefox e Raspberry Pi nella versione 2.8 (04/10/2026); la versione è `2.9-beta`, con data di build 2026-10-05.
- **Guida:** nota sul dado a 2 bit (qui) contro il consiglio a 1 bit della procedura operativa del repository `document`; consiglio di copiare altro per svuotare gli appunti dopo aver incollato i bit in EntropyPipeline; voce 15 delle novità.
- **README:** tolta la riga sull'ordine dei documenti di cerimonia (la `procedura operativa` di `document` è stata riallineata all'ordine moneta, dado, pallina il 04/10/2026, commit `93a143e`; il PDF dei 60 turni è fuori da questo repository); aggiornati verifiche e limiti.
- **Nuova cartella `verifica/`** con gli script di prova (Python e Node.js): `python3 verifica/esegui_tutto.py`; vedi `verifica/LEGGIMI.md`. Gli script stampano l'avanzamento man mano (prima non stampavano nulla finché non finivano) e impostano da soli `PYTHONUTF8=1` per il programma che lanciano; con una codifica non UTF-8 e senza questo rimedio le prove D ed E fallirebbero.
- **Revisione automatica di GitHub Copilot (04/10/2026), non un audit umano indipendente.** Recepiti i rilievi sul testo (avviso, parola «sicuri»). Non adottati, dopo averli controllati sul codice: CSP basata su hash (Chromium ignora 4 attributi `style=` e l'aspetto cambia; chi modifica il file modifica anche la CSP); controllo dell'impronta scritto dentro lo script (non può mai coincidere con l'impronta del blocco che lo contiene, provato; l'ancora è esterna: `SHA256SUMS.txt` e questo CHANGELOG); riscrittura della validazione dell'input (già a lista di valori ammessi: 180.081 stringhe, 0 anomalie, nessun `innerHTML` né `eval`); intestazione sui bit copiati (EntropyPipeline respinge il testo); sovrascrittura della memoria dopo il download (azzererebbe i bit ancora in uso: `110110` diventava `000000`); catena di hash e log in console.

**Verifica (ambiente di prova dell'autore, 05/10/2026).**
- Programma: 8 prove su 8 (645 configurazioni del modello; 400 sessioni casuali, 280.000 passi; esempio `110110`; esecuzione da pipe; quattro scelte di prudenza; avviso CSPRNG; terminale simulato con tasti, negativo e giallo; `NO_COLOR` e `TERM=dumb`).
- Pagina, in Node.js: 15 controlli su 15; 1500 sessioni identiche al programma (registro identico in 1500 su 1500); SHA-256 uguale su 300 stringhe; 126 configurazioni uguali; input su 180.081 stringhe con 0 anomalie.
- Pagina, in Chromium: 24 prove su 24 sull'interfaccia; per la copia pubblicata come artefatto, 12 prove su 12 sul salvataggio simulato.
- Gli script, controllati introducendo errori di proposito (ordine vecchio nel programma; conversione del dado sbagliata nella pagina), li rilevano.
- **Raspberry Pi (05/10/2026), Python 3.13.5 e Node.js 20.19.2:** `python3 verifica/esegui_tutto.py` eseguito sul pacchetto 2.9-beta con tutte le prove superate (programma 8 su 8; pagina 15 controlli su 15; 1500 sessioni identiche al programma, registro identico in 1500 su 1500; SHA-256 su 300 stringhe; 126 configurazioni; input su 180.081 stringhe con 0 anomalie).
- **Windows (05/10/2026):** Su Windows, il 05/10/2026 (Python 3.14.8, PowerShell 5), il programma: gli script di `verifica/` (7 prove su 7; la prova con terminale simulato viene saltata perché serve Linux o Mac); una sessione interattiva a risultato non noto (profilo personalizzato, 2 monete, 1 dado e 2 tombole per giro, 30 bit, un rilancio, annullamenti con Canc e con `u`), con sequenza, SHA-256, bit stimati (anche i valori intermedi) e conteggi uguali al modello; il Backspace, provato a parte, annulla l'ultimo inserimento; input sbagliati gestiti; salvataggio verificato (l'impronta del file calcolata da Windows è uguale a quella del registro, quindi nessun a capo finale né conversioni); aspetto di «Ora tocca a» in negativo e della sequenza in giallo confermato.
- **Browser su Windows (05/10/2026):** Su Windows, la pagina 2.9-beta in tre browser, con tre sessioni a risultato non noto in anticipo (l'atteso era calcolato da Claude e non rivelato): Edge (12 bit, un rilancio, un annullamento), Chrome (2 monete, 2 dadi e 1 tombola per giro, 18 bit, due rilanci, `testa` e `croce` scritti per esteso, un annullamento) e Firefox (profilo molto prudente, 1 moneta, 3 dadi e 2 tombole per giro, arresto manuale a metà giro con conferma, due rilanci, un annullamento). In tutte e tre sequenza o impronta SHA-256, bit stimati, rilanci, conteggi, ripetizioni e controllo interno coincidono con il modello, con 15 controlli su 15 e l'impronta del codice attesa. Il giallo è confermato nei tre browser; «Ora tocca a» in nero è confermato in Chrome e in Firefox, non in Edge (l'autore non lo ricorda). Nella prova in Firefox il testo copiato non conteneva la sequenza in chiaro, quindi la sequenza è confermata dall'impronta SHA-256.
- **Limite noto, documentato e non corretto (il programma resta com'è):** Se l'uscita del programma viene reindirizzata (su un file o in una pipe) e il sistema usa una codifica che non è UTF-8 (su Windows cp1252 o cp850, su Linux `LANG=C`), il programma si ferma subito con `UnicodeEncodeError`, prima che sia stato inserito qualcosa. Nel terminale interattivo non succede (provato su Windows, PowerShell 5). Rimedio: imposta prima `PYTHONUTF8=1` (PowerShell: `$env:PYTHONUTF8="1"`; bash: `export PYTHONUTF8=1`). Gli script di `verifica/` lo impostano da soli. Verificato in simulazione su Linux con le codifiche cp1252 e cp850; non provato su un Windows reale senza `PYTHONUTF8`.
- **Non verificato:** sessioni con lanci fisici veri; il programma su Mac e su Windows in terminali diversi da PowerShell 5; la pagina HTML 2.9-beta aperta in Firefox sul Pi; la pagina su Safari, Android e iPhone; l'aspetto di «Ora tocca a» in nero su Edge (non ricordato dall'autore).

## v2.8 (2026-10-04) — prima pubblicazione in questo repository

- `generatore_bit.py` — SHA-256: `f26491a567a81e1c964f7560b0480e3600b28b544ea8e6d0da8b08fd3fb9bdfc`
- `generatore_bit.html` — SHA-256: `4b888be0450a8544234fb46a01b6b47ab51fbcd6476de84e382a9df9d757f33f`; blocco `<script id="core-script">`: `5c463197d0cd756d329a723ad8b23256965ef712d2b1444128bc677a9528067a`
- `Guida_Generatore_Bit.md` — SHA-256: `411eba3e87d4df82ec3279e63582a4c56726d7771871b1aa6a17f66ef28f9b02`

**Stato alla pubblicazione.** Programma e pagina HTML fanno lo stesso calcolo e producono lo stesso testo di registro (a parte la riga «Generato dalla pagina HTML»). Tutto è riferito a EntropyPipeline v2.0.0-beta6 o successiva (pubblicata il 04/10/2026): i numeri di bit e di ripetizioni non valgono con versioni precedenti.

**Cosa fa la v2.8.**
- Ordine di inserimento in ogni giro: prima tutte le monete, poi tutti i dadi, poi tutte le tombole, nelle quantità scelte all'avvio; il giro poi si ripete.
- Riga «Ora tocca a» evidenziata senza colori: nome della fonte (MONETA, DADO, TOMBOLA) in negativo e grassetto, con ► ◄ (nel programma da terminale solo su un terminale vero; senza terminale o con `TERM=dumb` restano i simboli). Anche la parola davanti al punto di inserimento è in negativo.
- Sequenza finale del riepilogo evidenziata in giallo (nel programma non con `NO_COLOR`).
- La prudenza compare a schermo solo come nome in maiuscolo (SOLO PROVA, PRUDENTE, MOLTO PRUDENTE, PERSONALIZZATO); il registro riporta il profilo e i parametri.
- Avviso «da solo non basta» all'avvio, nel riepilogo, nel registro e nella guida; indicazione di quante volte ripetere l'esecuzione se si usa solo il Generatore.

**Verifica (eseguita dall'autore in un ambiente di prova).**
- Programma: calcolo identico alla v2.4 (8.241 controlli); ordine, bit, annullamenti e soglia a fine giro in 400 sessioni casuali (280.000 passi) confrontate con un modello indipendente; esecuzione con ingresso da pipe e con terminale simulato; nel calcolo è cambiato rispetto alla v2.4 solo l'ordine dei bit (esempio della guida: `110110` invece di `101110`).
- Pagina: 15 controlli all'avvio su 15; in Node.js 1500 sessioni identiche al programma Python (registro identico in 1500 su 1500), SHA-256 uguale su 300 stringhe, giri, bit e ripetizioni uguali su 126 configurazioni; in Chromium 21 prove su 21 sull'interfaccia e 12 su 12 sul salvataggio simulato (funzione disponibile solo nella versione pubblicata come artefatto, non in questo file).
- Cambio d'ordine (v2.5): con la pagina EntropyPipeline beta6 su 1200 bit simulati e 600 prove accoppiate, da 1,6 a 4,0 bit in meno su circa 699, entro un errore standard (4,4-4,6 bit): non distinguibile da zero.
- Raspberry Pi dell'autore, 04/10/2026, programma 2.8: «funziona».
- **Non verificato:** lanci fisici veri; Mac e Windows; la pagina 2.8 su Firefox, Safari, Android, iPhone e Raspberry Pi; l'aspetto del negativo e del giallo su un terminale o un browser veri.

**Versioni precedenti, non pubblicate in questo repository** (dettagli nella sezione 11 della guida).
- v1: prima versione (il dado dava 1 bit per lancio; l'annullamento non riallineava il contatore del blocco).
- v2.0: annullamento corretto, dado a 2 bit (1-4, con 5 e 6 rilancio), soglia opzionale, stima prudente della min-entropia con profili, lettura dei tasti più robusta, salvataggio con permessi riservati e registro di controllo.
- v2.1: testi più semplici, dopo la prima prova sul Raspberry Pi (01/10/2026). La pagina HTML nasce con la v2.4.
- v2.2 e v2.3: avviso «da solo non basta» e indicazione delle ripetizioni (la v2.2 non è stata rilasciata).
- v2.4: tutto riferito a EntropyPipeline v2.0.0-beta6 o successiva.
- v2.5: ordine moneta, dado, tombola.
- v2.6 e v2.7: evidenziazione di «Ora tocca a» con colori e poi in negativo; non rilasciate, assorbite nella v2.8.
