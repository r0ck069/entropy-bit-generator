# Prove del Generatore di bit

Script per controllare che il programma (`generatore_bit.py`) e la pagina (`generatore_bit.html`) facciano quello che dichiarano. Servono **Python 3.7 o superiore** e, per la pagina HTML, **Node.js** (nessuna libreria da installare). Se Node.js manca, le prove sulla pagina vengono saltate e lo script lo dice.

## Come si lancia

Dalla cartella del repository:

```
python3 verifica/esegui_tutto.py
```

Esito 0 se nessun passo fallisce, esito 1 se anche uno solo fallisce. Il riepilogo finale elenca ogni passo come `OK`, `FALLITO` o `SALTATO`.

Le prove stampano l'avanzamento man mano. Durano da pochi secondi a un paio di minuti secondo il computer (la B, con 280.000 passi, è la più lenta): **non interromperle con Ctrl+C**.

Gli script impostano da soli `PYTHONUTF8=1` per il programma che lanciano, quindi non serve farlo a mano, nemmeno su Windows.

## Cosa controllano

| File | Cosa fa |
|---|---|
| `prove_programma.py` | Valori di riferimento del modello (dado 1,8931, moneta 0,9714, tombola 2,9296 bit nel profilo prudente; giri per 320, 384 e 416 nei tre profili; quante volte ripetere); 400 sessioni casuali (280.000 mosse con inserimenti e annullamenti) confrontate con un modello indipendente per ordine moneta-dado-tombola, bit, soglia a fine giro e coerenza; l'esempio della guida (`110110`); il programma intero con ingresso da pipe (ordine delle richieste, bit salvati, registro, SHA-256); le quattro scelte di prudenza; l'avviso «non è un CSPRNG»; su Linux e Mac, un terminale simulato con i tasti (Invio, Backspace, Canc), il rilancio del dado, il negativo di «Ora tocca a», il giallo della sequenza finale, `NO_COLOR` e `TERM=dumb`. |
| `genera_casi.py` | Dal programma produce 1500 sessioni casuali (con rilanci e annullamenti), 300 stringhe per lo SHA-256 e 126 configurazioni di giri, e le scrive in un file JSON. |
| `confronto_pagina.js` | Carica il codice della pagina in Node.js ed esegue i suoi 15 controlli all'avvio; poi rifà le stesse sessioni e controlla che bit, bit stimati, posizione nel giro, soglie, conteggi e **testo del registro** siano identici a quelli del programma; SHA-256 uguale su 300 stringhe; giri e ripetizioni uguali su 126 configurazioni. |
| `prova_input.js` | Prova la validazione dell'input della pagina con 180.081 stringhe (casuali e avversarie: HTML, cifre unicode, segni, NUL, numeri enormi): devono entrare solo i valori validi, con i bit giusti; controlla anche che nella pagina non compaiano `innerHTML`, `eval` o simili. |
| `esegui_tutto.py` | Lancia nell'ordine i passi precedenti e stampa il riepilogo. |

Gli script sono stati controllati anche al contrario, introducendo errori di proposito in una copia (ordine delle fonti vecchio; conversione del dado sbagliata nella pagina): sono stati rilevati.

## Cosa NON controllano

- Non provano che i bit siano casuali né che la stima sia giusta: controllano che il codice faccia ciò che dichiara e che programma e pagina coincidano. La stima dei bit è un modello prudente, non una prova di casualità.
- **Non sono qui** le prove dell'autore che richiedono un browser comandato da programma (l'aspetto della pagina, il salvataggio simulato) né il confronto statistico degli ordini con la pagina di EntropyPipeline: in questo repository mancano.
- Il terminale simulato non gira su Windows (la prova E viene saltata e lo dice). La lettura dei tasti su Windows è stata provata a mano dall'autore (vedi il CHANGELOG), non da uno script.
- Nessuna prova con lanci fisici veri.
