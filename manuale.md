# Il manuale

Ogni voce è un errore già commesso e già pagato, oppure una misura che si è
rivelata giusta più di una volta. Il numero dentro la regola serve a non
reinterpretarla. Il motore applica già quasi tutto: qui c'è il perché, per quando
qualcosa va deciso a mano.

## Prima di girare

- **Controlla il livello prima del primo ciak.** Ascolta in cuffia.
- **Presa unica, sempre acceso.** Non fermare mai la registrazione.
- **Di' "rifaccio" prima di ripetere, mai dopo.** Con questa sola abitudine la scelta
  delle prese diventa meccanica. Se lo dici dopo, la correzione finisce dentro la
  ripresa buona.
- **Tre secondi di silenzio fra i blocchi** e telefono in modalità aereo. Uno squillo
  a 66,5 s ha costretto una volta a chiudere una frase 280 ms prima del punto giusto.
- **Un secondo pieno fermo alla fine di ogni presa**, in camera.
- **Inquadra largo e resta fermo.** Le inquadrature strette si ricavano dopo. Se ti
  sposti, ogni stacco stringe in un punto diverso e il montaggio traballa.
- **Una spanna d'aria sopra la testa**: senza, niente scritte dietro la testa.
- **Le pause fra le frasi servono al taglio, non alla recitazione.** Falle pure
  lunghe: vengono tolte.
- **Sui telefoni spegni l'HDR.** Il kit lo converte, ma i colori vengono meglio senza.

## Trascrizione

Scribe è ottimo, ma cancella parole senza errori se non conosci i suoi vizi.

- **Ingloba il silenzio nell'ultimo token di una frase.** `'solo.'` copre 67,04-71,83
  per una parola di mezzo secondo. Decide il suono, non il token.
- **A volte nasconde un tratto intero in un token.** `'quelle'` copriva quattordici
  secondi: presa interrotta, "rifaccio", frase buona. Il video è uscito con la frase
  monca. Ogni token sopra 1,2 s si ritrascrive da solo.
- **Fonde balbuzie e ripetizione** (`ripeti-quando`). Dentro il token c'erano 650 ms
  di silenzio: la parola buona si recupera facendo partire il taglio a metà.
- **Omofoni e nomi.** "da lì hai 10 giorni" diventa "ai 10 giorni", "Claude" diventa
  "Cloud". Il sottotitolo lo mostra per mezzo secondo e nessun controllo lo vede:
  rileggi il testo per intero. Vanno in `correzioni`.
- **Ripresa sentita a metà frase:** la prima parola esce minuscola. Il motore la
  rimette maiuscola.
- **Il tempo della parola può arrivare 20-80 ms dopo l'attacco vero.** Tagliare lì
  mangia la consonante: è così che un "quattro" è diventato irriconoscibile.

## Taglio

- **Le pause sopra 0,35 s si tolgono.** Su un parlato scandito ha recuperato 17
  secondi su tre video.
- **Lo stacco lo decide l'inviluppo, non Scribe.** Fra `alle` e `4` dichiarava 440 ms
  dove ce n'erano 40; fra `trattativa.` e `La riprende` zero dove ce n'erano 620.
- **Le isole brevi e isolate sono rumore.** Due colpi in cucina bastavano a tenere in
  campo 2,5 s di silenzio.
- **Ma un'isola in cui Scribe ha sentito una parola resta.** Un "Ora" staccato di
  0,9 s è stato scartato come un tonfo, senza errori.
- **Un pezzo corto non si butta: si fonde col precedente.** "fa." e "no." erano le
  battute su cui poggiava la riga.
- **Coda di 220 ms dopo un punto, 100 a metà frase.** Una coda unica fa sembrare
  tagliate le domande.
- **La soglia del parlato cambia a ogni girato.** Se un attacco prende un respiro si
  alza, se una coda sparisce si abbassa.

## Chi legge da uno schermo

Il problema più insidioso, perché non si vede finché non lo cerchi.

- **I blocchi "grafica" vanno coperti da bordo a bordo, al fotogramma.** Una copertura
  che entra a metà lascia in campo lo sguardo che si alza.
- **A fine riga l'occhio torna al copione:** lascia l'obiettivo fra 250 e 600 ms prima
  della fine del pezzo. Se succede dopo l'ultima parola, usa `fermo` (massimo la coda:
  prima si vedono le labbra bloccate). Se succede durante, fai partire prima la
  copertura successiva.

## Inquadrature

- **Non serve girare due volte.** Si stringe in post: 1,08 largo, 1,18 medio, 1,30
  stretto.
- **Due blocchi vicini non hanno mai la stessa scala.** È questo che fa leggere lo
  stacco come un cambio d'inquadratura e non come un glitch.
- **La scala dipende da quanto sei lontano.** Se sei già vicino, 1,30 taglia la fronte:
  usa numeri più bassi.
- Dentro un blocco il salto si nasconde con uno scarto minimo, 1,045.

## Colore

- **Misura, non guardare.** Il grezzo sembra sempre più inciso di quello che è. Un
  volto a YAVG 72 è "poco luminoso", a 84 va bene.
- **Il riferimento è il tuo ultimo video approvato**, non il girato.
- **Rendi quattro varianti su un fotogramma e confrontale affiancate.** Due giri e si
  chiude.

## Audio

- **Un guadagno per blocco, misurato sul parlato che finisce nel video.** Sette minuti
  su undici di una presa erano silenzio: la misura sul file intero sbagliava di 1,8 LU.
- **-14,5 LUFS con un limitatore a -1,5 dBFS.** Da soli i due obiettivi non si tengono.
- **La voce mono si duplica prima del guadagno,** o ffmpeg la abbassa di 3 dB dopo il
  limitatore.
- **Musica: si abbassa da sola sotto la voce.** Deve stare circa 21 dB sotto mentre
  parli. Gli strumenti veri riempiono le frequenze della voce: la prima prova era
  "troppo ingombrante".
- **Sempre una dissolvenza di 30 ms a ogni taglio,** se no fa clic.

## Grafiche

- **L'impalcatura c'è dal primo fotogramma, senza dissolvenza.** Sulla parola arriva
  solo ciò che la frase rivela.
- **Atterra sulla parola:** la comparsa parte 0,20 s prima.
- **Le battute si indicano con una parola, mai in secondi.** Un rimontaggio integrale
  non ha richiesto di ritoccare nove animazioni.
- **Mai due rivelazioni insieme.**
- **Campiona sei fotogrammi prima di montare.** Costa un secondo e mostra quasi tutti
  gli errori.

## Sottotitoli

- **Sempre impressi.** Su Facebook la maggior parte della visione è muta.
- **Aree di sicurezza su 1080x1920:** niente sopra y 260, niente sotto y 1440, niente
  a destra di x 880 sotto y 1100. Per quattro video di fila i sottotitoli sono stati
  sotto la didascalia di Instagram e nessuno se n'è accorto.
- **Gruppi di due o tre parole, fermi.** Un gruppo non finisce mai su una preposizione,
  un articolo o una congiunzione.
- **L'accento deve avere un motivo leggibile.** In fondo a ogni frase segna la
  punteggiatura, non il senso. Numeri, e la parola che regge la frase, una ogni tre
  secondi.
- **Mai una parola tenuta senza didascalia.** Si tronca il token, non si scarta.
- **Nessuna didascalia in campo oltre 3 secondi.**

## Copertina

- **Il primo fotogramma è la copertina.** Instagram, TikTok e LinkedIn prendono quello
  se non carichi niente.
- **Il volto si cerca dove sorridi di più, solo nei blocchi volto:** altrimenti sceglie
  sorrisi con gli occhi sul copione. Il punteggio da solo non basta: guarda il foglio
  dei candidati.
- **Il titolo resta circa due secondi.** A 4-6 secondi copre troppo.
- **Mai tre secondi di copertina ferma in testa:** sono i secondi in cui si decide se
  restare.

## Prima di mostrare

- Si controlla sempre l'uscita, mai le sorgenti.
- Cerca i silenzi sopra 0,4 s: si sono trovati 2,5 s di vuoto dopo aver dichiarato
  finito.
- Con `--ascolta` il video si ritrascrive e si confronta con le parole tenute: nessun
  altro controllo sente cosa dice. Consuma una piccola parte dei crediti Scribe.
- Guarda il risultato a misura di telefono, non a schermo intero.

## Le mie regole

Qui l'agente aggiunge quello che impara con te: la regola e il caso che l'ha generata.
