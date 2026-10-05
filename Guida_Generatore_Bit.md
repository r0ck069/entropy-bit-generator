# Guida: Generatore di bit da fonti fisiche (versione 2.9-beta)

**Documento pensato per chi non ha alcuna conoscenza precedente dell'argomento.**
Descrive il contesto, le regole, il modello di stima e l'uso del programma `generatore_bit.py`.

> **Da solo questo programma non basta.** I bit che produce vanno uniti ad altre sorgenti **indipendenti** con **EntropyPipeline**, lo strumento della suite entropy-suite che li estrae con Peres e Toeplitz, **nella versione v2.0.0-beta6 o successiva**. Il programma non produce una chiave, e da solo non è sufficiente per ricavarne una. **Non è un generatore casuale per uso crittografico (CSPRNG):** i «bit stimati» sono una stima con un modello prudente, non una prova di casualità.

**Verifica dei file.** Il programma `generatore_bit.py` di questa versione ha SHA-256:

`337b4c07031d435cbf41555d1b2b08c4469ac35083f34507349831a8960b60a1`

Controllalo con `sha256sum generatore_bit.py` (Linux/Mac) prima di usarlo.

---

## 1. Contesto: a cosa serve

A volte serve una lunga stringa di **bit** (zeri e uni) che sia il più possibile **imprevedibile** e non prodotta da una formula di un computer. Una fonte fisica (dado, moneta, palline estratte da un sacchetto) non segue una formula.

Questo programma ti fa inserire i risultati di lanci ed estrazioni reali e li converte in bit secondo regole fisse. **Non** produce una chiave finita: produce una stringa di bit grezzi e una stima prudente di quanta imprevedibilità contiene. L'estrazione successiva (Peres, Toeplitz, hash) va fatta con un altro strumento: **EntropyPipeline** (v2.0.0-beta6 o successiva), nella suite entropy-suite; questo programma non la esegue e, da solo, non basta.

**Importante:** la qualità dipende interamente da come esegui lanci ed estrazioni (sezione 3).

**Parole usate dal programma e da questa guida:**
- **giro** = una serie di lanci ed estrazioni sempre uguale, che si ripete (nella versione 1 e nel codice si chiamava "ciclo"); in ogni giro si inseriscono **prima tutte le monete, poi tutti i dadi, poi tutte le tombole**, nelle quantità scelte all'avvio;
- **esito** = ciò che è uscito da un singolo lancio valido o da una singola estrazione (sullo schermo si chiama "inserimento");
- **bit stimati** = la stima prudente di quanto sono imprevedibili i bit raccolti; il termine tecnico è **min-entropia**.

---

## 2. Regole di conversione

### 2.1 Dado a 6 facce (2 bit per lancio valido)

| Esce | Risultato |
|------|-----------|
| 1 | bit `00` |
| 2 | bit `01` |
| 3 | bit `10` |
| 4 | bit `11` |
| 5 o 6 | **rilancia**, nessun bit |

Le quattro facce accettate hanno la stessa probabilità, quindi ogni lancio valido vale 2 bit. La versione 1 ne ricavava solo 1 per lancio: la resa del dado è raddoppiata.

**Attenzione alla procedura operativa.** Il testo `procedura operativa` del repository `document` consiglia per il dado una mappatura a 1 bit (le facce 1 e 2 danno 0, le facce 3 e 4 danno 1, con 5 e 6 rilancio). Questo programma e la pagina HTML usano invece **2 bit** per lancio valido (tabella qui sopra). Per una sessione fatta con il Generatore vale la mappatura a 2 bit: chi converte a mano gli stessi lanci con la mappatura a 1 bit ottiene bit diversi.

### 2.2 Moneta (1 bit per lancio)

- Testa (`T`, `0` o `TESTA`) → bit `0`
- Croce (`C`, `1` o `CROCE`) → bit `1`

### 2.3 Tombola, numeri da 1 a 8 (3 bit per estrazione)

| Estratto | Bit | | Estratto | Bit |
|---|---|---|---|---|
| 1 | 000 | | 5 | 100 |
| 2 | 001 | | 6 | 101 |
| 3 | 010 | | 7 | 110 |
| 4 | 011 | | 8 | 111 |

---

## 3. Regole di rigore operativo (obbligatorie)

### Principio generale
**Non scegliere mai un esito.** Inserisci solo ciò che è realmente uscito. Non decidere nemmeno quando fermarti guardando i bit già prodotti: la fine si decide in base al **numero** di esiti (soglia), mai in base ai loro valori.

### Moneta
- Lanciala fisicamente, non decidere a mente.
- Si consiglia una moneta da 2 euro (o di peso e dimensioni simili) in buone condizioni.
- Una moneta lanciata a mano tende a ricadere sulla stessa faccia da cui è partita. Il valore misurato da Bartoš e altri (2023, 350.757 lanci, 46 valute) è **50,8%**, con intervallo credibile al 95% tra 50,6% e 50,9%; la previsione teorica di Diaconis e colleghi (2007) è circa 51%. Il programma ne tiene conto (sezione 4).

### Dado
- Mescolalo almeno **3 secondi** in un piccolo contenitore chiuso che permetta la libera rotazione; solo dopo leggi l'esito.
- Dado in buone o ottime condizioni (facce leggibili, angoli non consumati, nessun difetto di forma).

### Tombola (palline da 1 a 8)
- Dopo ogni estrazione la pallina va **reinserita** nel sacchetto.
- Sacchetto abbastanza ampio; palline mescolate **almeno 5 secondi** prima di ogni estrazione.
- Palline e sacchetto in buone o ottime condizioni.

### Uso dell'annullamento
L'annullamento serve **solo** per correggere un errore di battitura. Annullare un esito perché non ti piace falsa la sequenza. Il programma registra ogni annullamento (sezione 8), ma non può impedirti di farlo.

---

## 4. Stima prudente dei bit (min-entropia)

Il programma non conta solo i bit: stima quanti **bit stimati** contengono (in termini tecnici, la **min-entropia**), cioè quanto è difficile indovinarli nel caso peggiore, se la sorgente fosse un po' sbilanciata. Un bit prodotto da un dado leggermente sbilanciato vale meno di 1 bit stimato. Sullo schermo la scelta si chiama «Quanto vuoi essere prudente?».

**Modello usato (ipotesi di lavoro, dichiarate):**
1. Ogni lancio o estrazione è **indipendente** dagli altri e da fonti diverse.
2. Dado e palline: la probabilità di ciascuna faccia/pallina non si discosta dal valore ideale di più di una percentuale relativa *d* (profilo). Nel caso peggiore una faccia ha probabilità massima e le altre minima; il rifiuto di 5 e 6 viene calcolato nello stesso caso peggiore. Formule: dado `-log2((1+d)/(4-2d))` per lancio valido; tombola `-log2((1+d)/8)` per estrazione. Verificate enumerando tutte le distribuzioni estreme ammesse (accordo a 6 decimali).
3. Moneta: probabilità massima del risultato = `p`, la probabilità di ricadere sulla stessa faccia; vale `-log2(p)` per lancio.
4. Le min-entropie di esiti indipendenti si sommano.

**Profili disponibili** (sullo schermo compaiono i soli nomi; il profilo 2, «prudente», è il consigliato):

| Profilo | d (dado, pallina) | p (moneta) | Dado | Moneta | Tombola | Giro 1 moneta+1 dado+1 pallina |
|---|---|---|---|---|---|---|
| solo prova | 0% | 50% | 2,0000 su 2 | 1,0000 su 1 | 3,0000 su 3 | 6,000 su 6 |
| prudente | 5% | 51% | 1,8931 su 2 | 0,9714 su 1 | 2,9296 su 3 | 5,794 su 6 |
| molto prudente | 10% | 52% | 1,7885 su 2 | 0,9434 su 1 | 2,8625 su 3 | 5,594 su 6 |

- **p = 51%** per il profilo prudente è la previsione teorica, un po' sopra il 50,8% misurato (margine voluto).
- **I valori d = 5% e 10% e p = 52% sono ipotesi prudenti, non misure.** Non c'è in questa guida un valore misurato di bias per i tuoi dadi e le tue palline. Se hai dubbi sul loro stato, usa "molto prudente" o un profilo personalizzato (opzione 4: il programma chiede di quanto può essere «truccato» un dado o una pallina, in percentuale da 0 a 50, e quante volte su 100 la moneta ricade sulla faccia di partenza, da 50 a 60).
- Il profilo "solo prova" non tiene conto di nessuno squilibrio: serve solo per provare il programma.

**Limite importante.** Questa è una stima *del modello*, non una misura sui tuoi dati. Con poche decine di lanci non è possibile dimostrare statisticamente che un dado è equilibrato. Se un tuo oggetto fosse sbilanciato oltre l'ipotesi, la stima sarebbe troppo ottimistica.

---

## 5. Soglie di arresto (opzionali)

All'avvio scegli uno dei tre modi:

1. **Quando ho abbastanza bit stimati** (consigliata; valore proposto 384). Il programma si ferma, a fine giro, quando la stima raggiunge il valore scelto.
2. **Dopo un certo numero di bit** (valore proposto 480, come nella versione 1). Il programma mostra quanti bit stimati corrispondono.
3. **Quando lo dico io**, scrivendo `fine`.

**Soglie di bit stimati (min-entropia) suggerite per ricavare una chiave da 256 bit.** Con un estrattore di tipo Toeplitz la min-entropia in ingresso deve essere almeno la lunghezza d'uscita più 2·log2(1/ε), dove ε è l'errore ammesso. Per 256 bit d'uscita:

| Soglia | Etichetta sullo schermo | Errore ammesso ε |
|---|---|---|
| 320 bit | minimo | 2^-32 |
| 384 bit | consigliato | 2^-64 |
| 416 bit | più prudente | 2^-80 |

**Quanti giri servono** (un giro = 1 moneta + 1 lancio valido di dado + 1 pallina = 6 bit grezzi):

| Soglia | ε | Solo prova | Prudente | Molto prudente |
|---|---|---|---|---|
| 320 (minimo) | 2^-32 | 54 giri (324 bit) | 56 giri (336 bit) | 58 giri (348 bit) |
| 384 (consigliato) | 2^-64 | 64 giri (384 bit) | 67 giri (402 bit) | 69 giri (414 bit) |
| 416 (piu' prudente) | 2^-80 | 70 giri (420 bit) | 72 giri (432 bit) | 75 giri (450 bit) |

**Confronto con la versione 1.** La soglia di 480 bit grezzi richiedeva 96 giri (5 bit per giro, dado a 1 bit), corrispondenti nel profilo prudente a circa 464 bit stimati, cioè più di quanto serva per le soglie sopra, e circa 336 azioni fisiche (contando i rilanci del dado, in media 1,5 lanci per esito valido). Con la soglia di 384 bit nel profilo prudente servono 67 giri, circa 234 azioni fisiche: circa 30% in meno, mantenendo ε = 2^-64 nel modello.

### Quante volte ripetere l'esecuzione se usi solo il Generatore

Se decidi di usare **solo** il Generatore, senza altre sorgenti esterne e indipendenti, **EntropyPipeline v2.0.0-beta6 o successiva** chiede circa **1200 bit** per ricavare 256 bit (circa 200 giri da 6 bit). Il programma lo scrive chiaramente, due volte:
- **all'avvio**, dopo aver scelto la soglia, in base ai bit di una esecuzione: per esempio con 60 giri (360 bit) dice «va eseguito 4 VOLTE in tutto»; con la soglia di 384 bit stimati (67 giri, 402 bit) dice 3 volte; con 1200 bit basta una volta;
- **a fine esecuzione**, in base ai bit realmente raccolti, con quante ne mancano. Vale anche quando la fine è decisa da te con `fine`.

Il programma **non** ripete da solo l'esecuzione: ogni esecuzione è una sessione a sé, anche in giorni diversi. Salva ogni volta con un nome diverso (per esempio `bits_1.txt`, `bits_2.txt`) e incolla i bit di tutte, una dopo l'altra, nella **stessa** finestra di EntropyPipeline. In una prova su 150 casi simulati stimare spezzoni corti a parte, invece che in fila, ha reso dal 19% al 23% in meno; l'ordine invece non cambia nulla. Con altre sorgenti indipendenti ne servono meno: lo dice la Fase 4 di EntropyPipeline.

**Attenzione alla versione della pagina.** I numeri valgono per EntropyPipeline v2.0.0-beta6 o successiva. Con versioni precedenti la stima della pagina è troppo pessimista e servirebbero più bit: usa la beta6 o una successiva.

**Cosa NON garantiscono queste soglie:**
- valgono per il modello della sezione 4 (indipendenza, bias entro d);
- la formula m + 2·log2(1/ε) è quella dell'estrattore Toeplitz; questo programma non esegue l'estrazione;
- uno strumento successivo con stimatori statistici propri (per esempio quelli del NIST SP 800-90B) può accreditare **meno** di questa stima sui pochi dati disponibili: non è stato verificato; in tal caso serviranno più giri;
- la soglia è un minimo, non una prova di casualità.

---

## 6. Come funziona il programma

1. **Preparazione.** Prima di tutto un avviso: da solo il programma non basta. Poi tre domande: «Quanto vuoi essere prudente?»; «Quanti inserimenti per ogni giro?» (moneta, dado valido, tombola; 0 = salta); «Quando vuoi fermarti?». Dopo l'ultima il programma scrive quante volte va ripetuta l'esecuzione se usi solo il Generatore (con EntropyPipeline v2.0.0-beta6 o successiva). Il programma mostra quanti giri servono per le soglie suggerite.
2. **Giri.** Ogni giro chiede nell'ordine moneta, dado, tombola: prima tutte le monete del giro, poi tutti i dadi, poi tutte le tombole, nelle quantità scelte all'avvio (anche diverse tra loro); finito il giro, se la soglia non è raggiunta, il giro si ripete nello stesso ordine. La posizione nel giro è sempre ricavata dagli esiti presenti: l'annullamento non può sfasarla (difetto della versione 1 corretto).
3. **Fine.** A fine giro, se la soglia è raggiunta, compare il riepilogo con la stringa di bit, conteggi per faccia, rilanci e SHA-256. Con `INVIO` confermi; con `u` annulli l'ultimo esito e riprendi.
4. **Schermo fisso.** Ogni inserimento ridisegna lo schermo con bit raccolti, bit stimati (stima), barra di avanzamento, la prudenza scelta (solo il nome in maiuscolo, per esempio PRUDENTE), «Ora tocca a», ultimi 12 bit e un breve promemoria dei comandi. La riga «Ora tocca a» è evidenziata, senza usare colori, per non confondere le fonti: il nome (MONETA, DADO, TOMBOLA) compare in negativo (colori invertiti rispetto al terminale) e in grassetto, racchiuso da ► ◄; la parola davanti al punto in cui scrivi («Moneta →», «Dado →», «Tombola →») è in negativo allo stesso modo. Nel riepilogo finale la sequenza di bit è evidenziata in giallo (testo nero su sfondo giallo): la selezione e la copia del testo non ne risentono. Il giallo non compare se è impostata la variabile `NO_COLOR` (per esempio `NO_COLOR=1 python3 generatore_bit.py`); fuori da un terminale vero, o con `TERM=dumb`, non compare nessuna evidenziazione e restano i simboli ► ◄.

### Comandi (in qualsiasi momento durante gli inserimenti)

| Comando | Effetto |
|---|---|
| CANC o BACKSPACE su riga vuota, poi `Invio` | annulla l'ultimo esito; premuto più volte, ne annulla altri (massimo 20 per comando) |
| `u` / `uN` + `Invio` | annulla l'ultimo / gli ultimi N esiti |
| `fine` (o `f`) | conclude ora; avvisa se l'obiettivo non è raggiunto o il giro non è finito e chiede conferma |
| `q` | esce **senza salvare**, dopo la domanda «Vuoi davvero uscire?» |

Il rilancio del dado (5 o 6) non è un esito e non si annulla. Nella configurazione `q` + `Invio` esce.

---

## 7. Requisiti e avvio

- Python 3.7 o superiore, nessuna libreria aggiuntiva. Verifica: `python3 --version`.
- Avvio: `python3 generatore_bit.py`

**Stato delle prove di questa versione.**
- Provata su Linux (Python 3.12.3), con terminale simulato (pseudo-terminale) e con ingresso da pipe. La lettura dei tasti è identica dalla 2.4 alla 2.9-beta: con la 2.4 sono stati provati Invio, Canc, Backspace, Esc, frecce e tasti ravvicinati; dalla 2.5 in poi sono stati ripetuti solo Invio, Canc e Backspace.
- **Provata su Windows** dall'autore il 05/10/2026 (Python 3.14.8, PowerShell 5): lettura dei tasti con `msvcrt` (Invio, Canc, Backspace), annullamenti, salvataggio e registro, aspetto di negativo e giallo. **Non provata su Mac.** La versione 1 non poteva funzionare su Windows (usava solo moduli Linux/Mac).
- Dalla 2.0 alla 2.4 la parte di calcolo (conversioni, stima prudente della min-entropia, posizione nel giro) è la stessa: la prova al terminale con l'ordine di inserimento di allora dava gli stessi bit e lo stesso SHA-256 della 2.0; la 2.1 ha cambiato solo i testi, la 2.3 aggiunge l'avviso «da solo non basta» e l'indicazione di quante volte ripetere l'esecuzione, la 2.4 riferisce tutto a EntropyPipeline v2.0.0-beta6 o successiva (18 prove automatiche su: 60 giri, soglia in bit stimati, esecuzione unica, fine manuale, esecuzione da 12 bit, esecuzione da oltre 1200 bit, indicazione della versione della pagina sullo schermo e nel registro). La 2.5 cambia l'ordine di inserimento in ogni giro (moneta, dado, tombola invece di dado, moneta, tombola): conversioni, stima dei bit stimati, soglie e numeri di giri sono invariati, ma a parità di lanci la sequenza di bit è diversa da quella delle versioni precedenti. Prove della 2.5: calcolo identico alla 2.4 (8.241 controlli su profili, quantità per giro e soglie); ordine, bit, annullamenti e soglia a fine giro in 400 sessioni casuali (280.000 passi, confrontate con un modello indipendente); esecuzione completa con ingresso da pipe e con terminale simulato (Backspace e Canc); confronto con la stima della pagina EntropyPipeline v2.0.0-beta6 su 1200 bit simulati (fonti ideali, moneta al 51%, 600 prove accoppiate): il nuovo ordine accredita da 1,6 a 4,0 bit in meno su circa 699, differenza entro un errore standard (4,4-4,6 bit), quindi non distinguibile da zero. La 2.7 evidenzia la riga «Ora tocca a» in negativo (nome della fonte a colori invertiti, senza usare colori) e la sequenza finale di bit in giallo; nessun cambiamento nei calcoli e nei bit. Prove della 2.7: tutte quelle della 2.5 ripetute; in modo pipe nessun codice di formattazione, solo i simboli ► ◄; con terminale simulato compaiono il negativo per moneta, dado e tombola e il giallo sulla sequenza finale, e nessun altro colore; con `NO_COLOR=1` resta il negativo ma non il giallo; con `TERM=dumb` non compare nessun codice. L'aspetto è stato controllato disegnando i codici catturati in un browser, **non** su un terminale vero: il negativo e il giallo esatti dipendono dalla tavolozza del tuo terminale. La 2.8 mostra la scelta di prudenza solo con il nome in maiuscolo, senza l'etichetta «Prudenza:» (nessun cambiamento nei calcoli e nei bit). Prove della 2.8: tutte quelle della 2.7 ripetute, più il controllo delle quattro scelte (SOLO PROVA, PRUDENTE, MOLTO PRUDENTE, PERSONALIZZATO) in ogni schermata. Prove della 2.9-beta: tutte quelle della 2.8 rifatte con gli script della cartella `verifica/` (8 prove sul programma; sulla pagina 15 controlli, 1500 sessioni identiche al programma e 180.081 stringhe di input senza anomalie) più 24 prove di interfaccia in Chromium. Sul Raspberry Pi (05/10/2026, Python 3.13.5 e Node.js 20.19.2) gli script della cartella `verifica/` sono stati eseguiti con tutte le prove superate; **non è stata ancora provata la pagina aperta in Firefox sul Pi**. Su Windows, la pagina 2.9-beta in tre browser, con tre sessioni a risultato non noto in anticipo (l'atteso era calcolato da Claude e non rivelato): Edge (12 bit, un rilancio, un annullamento), Chrome (2 monete, 2 dadi e 1 tombola per giro, 18 bit, due rilanci, `testa` e `croce` scritti per esteso, un annullamento) e Firefox (profilo molto prudente, 1 moneta, 3 dadi e 2 tombole per giro, arresto manuale a metà giro con conferma, due rilanci, un annullamento). In tutte e tre sequenza o impronta SHA-256, bit stimati, rilanci, conteggi, ripetizioni e controllo interno coincidono con il modello, con 15 controlli su 15 e l'impronta del codice attesa. Il giallo è confermato nei tre browser; «Ora tocca a» in nero è confermato in Chrome e in Firefox, non in Edge (l'autore non lo ricorda). Nella prova in Firefox il testo copiato non conteneva la sequenza in chiaro, quindi la sequenza è confermata dall'impronta SHA-256. Su Windows, il 05/10/2026 (Python 3.14.8, PowerShell 5), il programma: gli script di `verifica/` (7 prove su 7; la prova con terminale simulato viene saltata perché serve Linux o Mac); una sessione interattiva a risultato non noto (profilo personalizzato, 2 monete, 1 dado e 2 tombole per giro, 30 bit, un rilancio, annullamenti con Canc e con `u`), con sequenza, SHA-256, bit stimati (anche i valori intermedi) e conteggi uguali al modello; il Backspace, provato a parte, annulla l'ultimo inserimento; input sbagliati gestiti; salvataggio verificato (l'impronta del file calcolata da Windows è uguale a quella del registro, quindi nessun a capo finale né conversioni); aspetto di «Ora tocca a» in negativo e della sequenza in giallo confermato.
- Gli script di prova (ordine, bit, annullamenti, soglie, ingresso da pipe, terminale simulato, parità con la pagina HTML in Node.js, prova dell'input su centinaia di migliaia di stringhe) sono nella cartella `verifica/` del repository: vedi `verifica/LEGGIMI.md`. Si lanciano con `python3 verifica/esegui_tutto.py` e richiedono solo Python 3 e Node.js.
- Se non c'è un terminale vero (pipe, redirezione) il programma funziona in modo riga per riga: CANC non è disponibile, si usano `u` e `uN`.

---

## 8. File prodotti

Al termine, se rispondi `s`, vengono creati due file nella cartella corrente:

| File | Contenuto |
|---|---|
| `bits.txt` (o il nome scelto) | la stringa di bit, **senza a capo finale** |
| `bits_registro.txt` | il «diario»: parametri, cronologia completa (esiti, rilanci, annullamenti), esiti finali, conteggi, SHA-256; è scritto in modo più tecnico del resto |

- I file **non vengono mai sovrascritti**: se il nome esiste, ne viene chiesto un altro.
- Su Linux e Mac sono creati con permessi `0600` (solo il proprietario). Su Windows i permessi non sono impostati dal programma.
- **Entrambi sono riservati**: il registro contiene le stesse informazioni dei bit.
- Il registro permette di ricostruire e verificare la cerimonia; contiene anche un controllo di coerenza tra cronologia ed esiti.

**Verifica della copia.** Lo SHA-256 mostrato a schermo e nel registro è calcolato sulla stringa di bit. Su Linux/Mac: `sha256sum bits.txt` deve dare lo stesso valore.

---

## 9. Esempio

Prudente, 1 moneta + 1 dado + 1 tombola per giro, 384 bit stimati (servono 67 giri):

```
Lancio moneta → C      bit 1
Lancio dado → 5        rilancio, nessun bit
Lancio dado → 3        bit 10
Estrazione tombola → 7 bit 110
```

Il primo giro produce `110110` (6 bit). Se sbagli un inserimento, premi CANC e poi `Invio` (oppure scrivi `u`): l'esito sbagliato viene tolto e il programma richiede di nuovo quella fonte.

---

## 10. Riepilogo veloce

| Fonte | Input | Bit |
|---|---|---|
| Dado | 1 / 2 / 3 / 4 | 00 / 01 / 10 / 11 |
| Dado | 5 o 6 | rilancio |
| Moneta | T / 0 / TESTA | 0 |
| Moneta | C / 1 / CROCE | 1 |
| Tombola | 1 … 8 | 000 … 111 |

Promemoria: non scegliere mai un esito; dado mescolato 3 secondi; palline reinserite e mescolate 5 secondi; moneta da 2 euro lanciata fisicamente; oggetti in buone condizioni; annullare solo per errori di battitura; non fermarti guardando i bit.

---

## 11. Cosa cambia rispetto alla versione 1

1. **Undo corretto.** Prima toglieva i bit ma non aggiornava il contatore del blocco; ora la posizione deriva sempre dagli esiti presenti.
2. **Dado a 2 bit** (1-4 → 00, 01, 10, 11; 5-6 rilancio).
3. **Soglia opzionale** (min-entropia, bit grezzi o nessuna) e stima prudente della min-entropia con profili di bias.
4. **Soglia controllata solo a fine giro**, in modo coerente con il tipo di soglia scelto.
5. **Compatibilità**: non dipende più solo da `termios`; lettura tasti robusta (Esc da solo non blocca; Invio non si perde con tasti ravvicinati); funziona anche senza terminale.
6. **Salvataggio** con permessi riservati, senza sovrascrittura, più registro di controllo con SHA-256.
7. **Guida allineata al codice**; non riporta più un frammento del codice.
8. **Versione 2.1: testi più semplici** (richiesta dopo la prima prova sul Raspberry Pi). Parole come «min-entropia», «ciclo», «esito» e «profilo» sullo schermo diventano «bit sicuri» (dalla 2.9-beta «bit stimati»), «giro», «inserimento» e «prudenza»; messaggi di errore e istruzioni riscritti. Nessun cambiamento nei calcoli e nelle regole.
9. **Versione 2.3: avviso «da solo non basta» e indicazione delle ripetizioni.** Avviso all'avvio, nel riepilogo, nel registro e in questa guida; se usi solo il Generatore il programma scrive quante volte va ripetuta l'esecuzione (all'avvio e a fine esecuzione). Nessun giro automatico e nessun cambiamento nei calcoli e nelle regole.

10. **Versione 2.4: tutto riferito a EntropyPipeline v2.0.0-beta6 o successiva.** Avvio, riepilogo, registro e guida indicano la versione della pagina a cui si riferiscono i numeri; sullo schermo resta scritto che con versioni precedenti i numeri non valgono. Nessun cambiamento nei calcoli e nelle regole.

11. **Versione 2.5: ordine di inserimento moneta, dado, tombola.** In ogni giro si inseriscono prima tutte le monete, poi tutti i dadi, poi tutte le tombole (nelle quantità scelte all'avvio, anche diverse tra loro); finito il giro, se serve, il giro si ripete nello stesso ordine. Cambia l'ordine dei bit: a parità di lanci la sequenza non coincide con quella della 2.4 (esempio della sezione 9: `110110` invece di `101110`). Conversioni, stima, soglie, numeri di giri e quantità da raccogliere non cambiano.

12. **Versione 2.6: riga «Ora tocca a» evidenziata con un colore diverso per fonte** (giallo, azzurro, viola). Sostituita dalla 2.7, che non usa colori per questa riga. Nessun cambiamento nei calcoli, nei bit e nelle regole.

13. **Versione 2.7: riga «Ora tocca a» in negativo e sequenza finale in giallo.** Il nome della fonte (MONETA, DADO, TOMBOLA) e la parola davanti al punto di inserimento sono in negativo (colori invertiti) e in grassetto, con i simboli ► ◄; senza terminale restano i simboli. La sequenza di bit del riepilogo finale è evidenziata in giallo (non con `NO_COLOR`). Nessun cambiamento nei calcoli, nei bit e nelle regole.

14. **Versione 2.8: la prudenza a schermo è solo il nome scelto.** Al posto della riga «Prudenza: prudente» compare soltanto il nome in maiuscolo (SOLO PROVA, PRUDENTE, MOLTO PRUDENTE o PERSONALIZZATO). Nessun cambiamento nei calcoli, nei bit e nelle regole; il registro continua a riportare il profilo e i suoi parametri.

15. **Versione 2.9-beta: testi più prudenti.** (a) «bit sicuri» diventa **«bit stimati»** in tutto il programma, nella pagina, nel registro e in questa guida, perché «sicuri» dava un'impressione di garanzia che la stima non offre; anche «più sicuro» diventa «più prudente»; (b) nuovo avviso: non è un generatore casuale per uso crittografico (CSPRNG) e i bit stimati sono una stima con un modello prudente, non una prova di casualità; (c) nota sulla mappatura del dado a 2 bit contro il consiglio a 1 bit della procedura operativa; (d) pagina HTML: dichiarata la prova su Firefox e Raspberry Pi nella versione 2.8; (e) consiglio sugli appunti nei limiti noti; (f) cartella `verifica/` con gli script di prova, che ora stampano l'avanzamento e impostano da soli la codifica UTF-8; (g) documentato il limite dell'uscita reindirizzata. Nessun cambiamento nei calcoli, nei bit e nelle regole.

## 12. Limiti noti

- La stima dipende da ipotesi (indipendenza, bias entro d) non verificabili con pochi lanci.
- Nessuna estrazione (Peres, Toeplitz, hash) è eseguita da questo programma, e da solo non basta.
- I 1200 bit proposti (circa 200 giri) vengono da simulazioni con EntropyPipeline v2.0.0-beta6 (pubblicata su GitHub il 04/10/2026) e con fonti ideali; con versioni precedenti i numeri non valgono; il programma non ripete da solo l'esecuzione.
- Le stringhe e il registro restano visibili a schermo e nei file: usa una macchina e un ambiente di cui ti fidi.
- Se l'uscita del programma viene reindirizzata (su un file o in una pipe) e il sistema usa una codifica che non è UTF-8 (su Windows cp1252 o cp850, su Linux `LANG=C`), il programma si ferma subito con `UnicodeEncodeError`, prima che sia stato inserito qualcosa. Nel terminale interattivo non succede (provato su Windows, PowerShell 5). Rimedio: imposta prima `PYTHONUTF8=1` (PowerShell: `$env:PYTHONUTF8="1"`; bash: `export PYTHONUTF8=1`). Gli script di `verifica/` lo impostano da soli. Verificato in simulazione su Linux con le codifiche cp1252 e cp850; non provato su un Windows reale senza `PYTHONUTF8`.
- Se copi i bit negli appunti (pagina HTML), dopo averli incollati in EntropyPipeline copia qualcos'altro per svuotare gli appunti: i bit restano altrimenti nella memoria degli appunti del sistema.
- Mac non provato; Windows provato in PowerShell 5, non in altri terminali.

**Fine della guida.**
