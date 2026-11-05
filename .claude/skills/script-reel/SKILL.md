---
name: script-reel
description: Scrive lo script di un video verticale in cui si parla in camera (30-40 secondi, una persona, girato col telefono) e lo salva pronto per la ripresa e per il montaggio con questo kit. Usala quando qualcuno chiede "scrivi lo script", "cosa dico nel video", "preparami il contenuto", "voglio fare un reel su", anche se non nomina mai la parola script.
---

# Script di un video verticale

Scrivi uno script che si possa dire in una presa sola e montare con questo kit. Lo
script è il copione **e** la lista di quello che deve succedere in ripresa: un effetto
che ha bisogno di un gesto non si può aggiungere dopo.

## Prima di scrivere

1. Leggi `chi-sono.md`. Se è ancora vuoto, fai tre domande, una alla volta: chi sei e
   cosa fai, a chi parli, come parli (due frasi tue vere, copiate da un messaggio o da
   un post). Scrivi le risposte in `chi-sono.md`.
2. Chiedi di cosa parla il video, se non te l'ha già detto. Serve una cosa sola: un
   errore, una scoperta, un conto, un'opinione.
3. Leggi `effetti.md`, sezione "Il dosaggio" e gli effetti pronti.
4. Se c'è un dato, verificalo sulla fonte e di' da dove viene. Se non riesci a
   verificarlo, dillo e riscrivi senza.

## Le misure

- **30-40 secondi, 85-110 parole.** Si parla a circa 2,8 parole al secondo. Conta le
  parole dette e scrivi il numero vero.
- **4-5 blocchi.** Almeno il 60% di volto.
- **Una copertura a piena inquadratura al massimo:** un blocco "grafica", dove puoi
  leggere dallo schermo. Mai come primo o ultimo blocco.
- **Il gancio sta nei primi 6 secondi** ed è la frase della copertina.
- **2 effetti,** scelti fra i pronti, sui blocchi volto. Il primo è sempre `sale` o
  `nastro`, quello che faremo insieme. Devono voler dire qualcosa sulla frase.
- **Chiudi con una cosa sola da fare o una domanda.**

## Come si scrive

Si scrive per la voce: frasi che si pronunciano in un fiato, con parole che chi parla
usa davvero. Leggi ogni blocco ad alta voce prima di consegnarlo.

Togli questi segni di testo scritto da una macchina:

- "Non è X, è Y" e tutte le sue varianti, anche con i due punti;
- tre elementi in fila, con l'ultimo più lungo: usane due, o quattro;
- la raffica di frasi brevissime una dopo l'altra;
- la frase d'effetto che chiude ogni blocco;
- parole che nessuno dice a voce: "fondamentale", "cruciale", "in un mondo in cui",
  "il vero segreto", "scopriamo insieme".

Niente clienti inventati. Gli esempi sono scenari tipici e si dicono come tali.

Se l'effetto chiede un gesto, scrivi la frase in modo che il gesto ci stia dentro: un
"questo" detto mentre indichi, una pausa dopo l'ultima parola.

## Cosa consegnare

Crea la cartella `girati/<nome>/` con un nome breve, minuscolo, senza spazi, e scrivici
`script.md` con questa forma:

```markdown
# Titolo

85-110 parole, N secondi, N blocchi, N effetti

## Copertina
Occhiello: IL TEMA IN MAIUSCOLO
Titolo: prima riga / seconda riga in accento

## Script

### b1 · volto · stretto
"La frase da dire."
Inq: come dirla, dove guardare.
Fx: nome dell'effetto. In ripresa: l'azione precisa, con il punto del quadro e la durata.

### b2 · grafica
"La frase da dire: qui puoi leggere."
Scheda: titolo e voci della copertura.

## Prima di girare
- telefono in verticale, appoggiato o sul treppiede, all'altezza degli occhi
- modalità aereo, HDR spento
- una spanna d'aria sopra la testa, finestra davanti a te, non alle spalle
- presa unica: se sbagli dici "rifaccio" PRIMA di ripetere, e riparti da inizio blocco
- tre secondi di silenzio fra i blocchi
- un secondo fermo, in camera, alla fine
- oggetti da portare: ...
```

Poi mostra lo script e chiedi cosa cambiare. Quando va bene, ricorda: gira, poi
`python kit.py nuovo <nome> <file>` e `python kit.py trascrivi <nome>`.

## Controlli

- Le parole sono contate davvero, non stimate.
- Ogni effetto è fra i pronti di `effetti.md` e sta su un blocco volto.
- Ogni oggetto citato in una riga `Fx` è nella lista "Prima di girare".
- Chiediti cosa rende questo testo palesemente scritto da una macchina, e correggi.
