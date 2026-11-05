# Il menu degli effetti

Gli effetti **pronti** si usano scrivendoli in `montaggio.json`. Le **ricette** non
sono ancora codice: si sa come farle, e l'agente le costruisce su richiesta con
EffectCraft, partendo dagli esempi in `motore/effetti_scene.py`.

**Un effetto che chiede un gesto o un oggetto non si può aggiungere dopo.** Se non è
nello script, non c'è. Per questo si sceglie quando si scrive.

## Il dosaggio

- Un effetto segna un momento, non accompagna il video: in 40 secondi da 2 a 4.
- Il contorno (`spegni`) al massimo due volte per video.
- Due effetti di fila mai dello stesso stile.
- Mai sul volto quando non guardi in camera: sui blocchi grafica niente effetti.
- L'effetto deve voler dire qualcosa sulla frase. Se è solo decorazione, toglilo.
- Tutto sopra y 1240, dove passano i sottotitoli.
- La testa copre al massimo il quarto basso delle lettere.

## Pronti, sulla persona

Lavorano sulla tua sagoma, ricavata da MediaPipe. Rendono con il volto in primo piano
e la camera ferma. I capelli vengono un po' morbidi.

| Nome | Si vede | Quando | In ripresa |
|---|---|---|---|
| `nastro` | Una frase gigante scorre dietro la testa | Uno slogan di 2-4 parole | Testa ferma, aria sopra la testa |
| `sale` | Una parola sale da dietro la testa e ci si appoggia | Un numero, un sì, un no | Mezzo secondo di pausa prima e dopo la parola |
| `estruso` | La stessa parola, solida e illuminata, che ruota | Quando la parola è il centro del video. Una volta | Come sopra |
| `scheda` | Una scheda su una riga sale da dietro la testa | Una domanda o un'istruzione corta | Testa ferma per tutta la frase |
| `scheda` con `"ribalta": true` | La scheda si gira come un'anta | La domanda finale | Testa ferma |
| `spegni` | Sfondo in bianco e nero, tu a colori col contorno | La frase chiave | Sguardo in camera, nessun gesto che esca dalla sagoma |
| `sfoca` | Lo sfondo si sfoca e si scurisce | Una confidenza, un'ammissione | Abbassa la voce, avvicinati di poco |
| `vicino` | La camera si avvicina lenta al volto | Una frase lenta | Non muoverti avanti e indietro |
| `colpo` | Uno scatto in avanti su una parola | La chiusura, una parola secca | Dilla con un piccolo accento |
| `profondita` | La camera entra nella stanza, tu e lo sfondo scorrete diversi | L'inizio di un ragionamento | Testa ferma 3 secondi |
| `folla` | Il quadro si riempie di tue copie grigie, tu a colori | Proporzioni: "una persona su venti" | Dì il numero in camera, testa ferma |
| `vertigo` | Tu resti uguale, lo sfondo ti viene addosso | Il momento in cui il ragionamento cambia | Testa immobile 2-3 secondi, faccia seria |

## Pronti, su tutto il quadro

| Nome | Si vede | Quando | In ripresa |
|---|---|---|---|
| `fumetto` | L'immagine diventa un disegno, con l'etichetta ESEMPIO | Gli scenari ipotetici | Apri con "immagina" e cambia tono |
| `glitch` | Per otto fotogrammi l'immagine si rompe | Un errore, un blocco | Dì la frase secca, senza muoverti |
| `timbro` | Una scritta-timbro sbatte nel quadro, con un colpo basso | Una frase che chiude: "già pagato", "scaduto" | Niente |

## Pronti, in ripresa

| Nome | Si vede | Come si fa | In ripresa |
|---|---|---|---|
| Entrate dai bordi | Spunti di lato, cali dall'alto, esci dal quadro | Nel blocco `prima` e `dopo` (i secondi in cui entri ed esci) e `centrato: true` | Camera bloccata. Entri, ti fermi e solo dopo parli |

## Come si scrivono

```json
{"nome": "e1", "blocco": "b3", "sale": {"testo": "NON SERVE", "parola": "serve", "pieno": true}}
{"nome": "e2", "blocco": "b5", "nastro": {"testo": "NON È PAURA", "parola": "paura"},
 "spegni": {"parola": "paura", "fine": true}}
{"nome": "e3", "blocco": "b6", "scheda": {"testo": "E TU?", "parola": "tu", "ribalta": true, "accento": true}}
{"nome": "e4", "blocco": "b7", "fumetto": {"parola": "immagina", "parola_fine": "ufficio"}}
{"nome": "e5", "blocco": "b8", "timbro": {"testo": "GIÀ PAGATO", "parola": "pagato", "dura": 2}}
```

`parola` è la parola su cui parte, com'è scritta in `parole.txt`. Gli stili si possono
combinare sullo stesso blocco. `pieno: false` fa il testo a filo. `fine: true` torna
indietro prima della fine del blocco.

Dopo ogni effetto guarda `verifica/effetto_<nome>.png`: sei fotogrammi, prima di
montare.

## Ricette: con la sagoma

| Nome | Si vede | Si fa con | In ripresa |
|---|---|---|---|
| Fermo immagine | Il video si ferma a metà gesto, compare una nota, riparte | Time Remap, forme, testo | Un gesto da fermare, tenuto mezzo secondo |
| Eco | Copie trasparenti ti inseguono | Sagoma, Echo | Un movimento netto e corto |
| Scossa | Il quadro trema un attimo | Espressione wiggle, Directional Blur | Batti la mano sul tavolo |
| Solo un colore | Tutto in bianco e nero tranne una cosa gialla | Leave Color | Un oggetto giallo pieno in quadro |
| Anello di testo | Una scritta ti gira intorno alla testa | Testo 3D su cerchio, sagoma | Testa ferma 3 secondi |
| Te in due | Due di te nello stesso quadro | Due prese, sagoma, maschere | Camera bloccata, due posizioni |

## Ricette: con un oggetto o un gesto

| Nome | Si vede | Si fa con | In ripresa |
|---|---|---|---|
| Foglio che diventa schermo | Un foglio mostra un'immagine che lo segue | Tracker prospettico, Corner Pin | A4 bianco con un pallino in ogni angolo, 3-4 secondi quasi fermo |
| Post-it | Un post-it si riempie di una parola | Tracker, Write-on | Post-it giallo fermo 2 secondi |
| Schermo del telefono | Lo schermo mostra quello che dici | Tracker prospettico, Corner Pin | Telefono spento, senza riflessi |
| Lente | Una lente ingrandisce un dettaglio | Magnify, tracker | Oggetto fermo, indica il dettaglio |
| Indica e compare | Indichi un punto e lì compare la scritta | MediaPipe Hand Landmarker, Remotion | Indica ai lati della testa, braccio fermo 1,5 s |
| Sul palmo | Una parola si appoggia sulla mano e la segue | MediaPipe Hand Landmarker, Remotion | Mano aperta a lato della testa, ferma 2 s |
| Lancio | Butti via e la scritta vola fuori | Testo, motion blur | Gesto ampio dal petto verso fuori |
| Schiocco | Schiocchi le dita e il quadro va in pezzi | Shatter, o flash e taglio | Schiocca davanti al petto a fine frase |
| Pagina girata | Il quadro si gira come una pagina | CC Page Turn | Gesto della mano a fine frase |
| Grafica nella stanza | Cartellini e cifre ti passano dietro la testa | Remotion, sagoma | Camera bloccata, 10 s di stanza vuota |

## Ricette: senza chiederti niente

| Nome | Si vede | Si fa con |
|---|---|---|
| Tabellone a carte | Il quadro si divide in tessere che si girano | Card Wipe |
| Cerchio a mano | Un tratto a mano cerchia un dettaglio | Trim Paths, Scribble |
| Testo animato | Macchina da scrivere, lettere mescolate, parole che rimbalzano | Preset di testo di EffectCraft |
| Oggetto 3D | Un oggetto solido in scena, illuminato | Primitivi 3D, modelli .glb |
| Pioggia di fogli | Fogli o numeri che cadono e si accumulano | CC Particle World |
| Contatore | Un numero che corre fino al valore giusto | Numbers, espressione |

## Cosa portare sul set

- **Aria sopra la testa.** Una spanna sopra i capelli.
- **Camera bloccata.** Treppiede o telefono appoggiato, e non toccarla fra le prese.
- **Mani in quadro,** se lo script chiede gesti: inquadratura da metà busto in su.
- **Un secondo fermo** prima e dopo ogni frase che porta un effetto.

## EffectCraft

È un clone open source di After Effects, guidato con script in stile After Effects
(`.jsx`). Sa fare 307 effetti, testo animato, 3D con luci e ombre, tracker. Il kit usa
la versione 0.21.1: ne esce una quasi al giorno, quindi prima di aggiornarla rifai una
tavola di fotogrammi.
