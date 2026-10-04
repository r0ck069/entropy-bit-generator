# Changelog — Generatore di bit da moneta, dado e tombola

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
