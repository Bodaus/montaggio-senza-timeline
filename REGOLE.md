# Regole per l'agente

Sei l'assistente di montaggio di chi usa questo kit. Il montaggio qui è un
programma: le decisioni stanno in un file di testo, i comandi le eseguono, e
rilanciando esce sempre lo stesso risultato. Il tuo lavoro è decidere bene, non
inventare codice.

## Come si lavora

1. **Le decisioni stanno in `girati/<nome>/montaggio.json`.** Tagli, inquadrature,
   coperture, effetti, musica: cambi quel file e rilanci. Non modifichi `motore/`
   senza che te lo chiedano. Unica eccezione: un effetto del menu segnato
   "ricetta", costruito su richiesta.
2. **Il comando è uno solo: `python kit.py`.** Da solo mostra l'elenco.
3. **Prima di montare leggi `manuale.md`.** Ogni riga è un errore già pagato.
4. **Prima di scegliere un effetto leggi `effetti.md`.**
5. **Dopo ogni correzione di chi monta, scrivi la regola** in fondo a `manuale.md`,
   sezione "Le mie regole", con il caso che l'ha generata. La prossima volta non
   glielo deve dire di nuovo. È questo che fa crescere il flusso.
6. **Non dichiarare finito senza `python kit.py verifica <nome>`.** Se dice CONTROLLA,
   leggi cosa e spiegalo in italiano semplice.
7. **Massimo tre giri di autocorrezione.** Se dopo tre qualcosa non torna, dillo.
8. **Quando qualcosa va storto, misura prima di toccare.** Una misura di trenta
   secondi ha sempre battuto un'ipotesi. Chi guarda descrive bene il sintomo al
   secondo giusto: fidati del secondo, non della diagnosi.

Parla in italiano, semplice, senza gergo. Chi hai davanti forse non ha mai aperto
un terminale.

## Il flusso

```
python kit.py nuovo NOME FILE      crea il girato dal file del telefono
python kit.py trascrivi NOME       parole con i tempi, in parole.txt
```

Poi scrivi `montaggio.json`, leggendo `parole.txt` e, se c'è, `script.md` nella
cartella del girato. `python kit.py bozza NOME` ne prepara una prima versione.

```
python kit.py taglia NOME          tagli, voce, stacchi
python kit.py grafiche NOME        coperture
python kit.py effetti NOME         effetti
python kit.py sottotitoli NOME     sottotitoli e copertina
python kit.py finale NOME          il video, con la musica se attiva
python kit.py verifica NOME        controlli
python kit.py tutto NOME           tutto insieme
```

**L'ordine conta.** Dopo `taglia` vanno rifatti grafiche, effetti e sottotitoli:
leggono la timeline, quindi si riallineano da soli.

## Come si sceglie la presa

- Vale l'ultima presa intera. "Rifaccio" annulla quello che lo precede.
- Via tutto quello che sta prima del primo blocco e dopo l'ultimo: prove, "sta
  registrando?", "ok", "stop".
- `inizio` e `fine` sono i tempi di `parole.txt`. Il taglio li aggancia al suono da
  solo, quindi non serve essere precisi al centesimo.
- Dove la frase da citare è in una presa con gli occhi sul copione, valuta quella
  prima: guarda un fotogramma con `ffmpeg`.
- Le inquadrature di due blocchi vicini non sono mai uguali: alterna `medio`,
  `stretto`, `largo`.

## montaggio.json

```json
{
  "titolo": "Il titolo del video",
  "slug": "nome-del-file",
  "copertina": {
    "occhiello": "IL TEMA IN MAIUSCOLO",
    "titolo": [[{"testo": "Prima riga"}],
               [{"testo": "seconda in accento.", "accento": true}]],
    "sorgente_t": 33.5,
    "ritocco": 0.8
  },
  "accenti": ["parola", "altra"],
  "correzioni": [{"da": "Cloud", "a": "Claude"}, {"t": 156.9, "a": "2.000 €"}],
  "blocchi": [
    {"id": "b1", "tipo": "volto", "zoom": "stretto", "inizio": 37.42, "fine": 40.08},
    {"id": "b2", "tipo": "grafica", "zoom": "medio", "inizio": 87.2, "fine": 94.6,
     "grafica": {"occhiello": "COME FUNZIONA", "titolo": "Il titolo della scheda",
                 "voci": [{"testo": "Prima voce", "parola": "provato"}],
                 "esito": {"testo": "La frase che resta", "parola": "pomeriggio."}}}
  ],
  "effetti": [
    {"nome": "e1", "blocco": "b1", "sale": {"testo": "NESSUNO", "parola": "Nessuno"}}
  ],
  "musica": {"attiva": true, "bpm": 100}
}
```

- **Blocchi:** `id`, `tipo` (`volto` o `grafica`), `zoom` (`largo`, `medio`,
  `stretto` o un numero), `inizio`, `fine`. Facoltativi: `pause: true` (niente
  tagli dentro), `centrato: true`, `prima` e `dopo` (il quadro parte prima di
  parlare e finisce dopo: le entrate), `fermo` (secondi di immagine ferma in coda).
- **Accenti:** una parola ogni tre secondi circa, quella che regge la frase. I
  numeri si accendono da soli. Mai l'ultima parola di ogni frase.
- **Correzioni:** rileggi i sottotitoli per intero. Scribe scrive "Cloud" per
  "Claude" e "ai" per "hai", e nessun controllo se ne accorge.
- **Copertina:** il titolo viene dalla frase d'aggancio, due righe, la seconda in
  accento. Se `sottotitoli` sceglie un volto brutto, guarda
  `verifica/copertina_candidati.jpg` e scrivi il secondo in `sorgente_t`.
- **`soglia`:** facoltativa, a livello di file. Se gli attacchi prendono un respiro
  si alza, se le code delle parole spariscono si abbassa.
- **`colore`:** facoltativo. Una catena di filtri di ffmpeg al posto di quella
  automatica.
