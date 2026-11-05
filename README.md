# Montaggio senza timeline

Un kit per montare un video verticale parlando con un agente: tagli, voce, sottotitoli,
copertina, effetti e musica. Nessun editor aperto. Il montaggio è un file di testo: lo
cambi, rilanci, esce il video nuovo.

È nato per il laboratorio di Lab 41 del 16 novembre 2026, partendo dal flusso con cui
Nicola Valletta monta i suoi contenuti. Va bene anche fuori dal laboratorio.

## Come funziona

Gli editor tengono le decisioni dentro la timeline. Qui stanno in `montaggio.json`, un
file di testo che l'agente scrive con te: quali frasi tenere, quale zoom, quali parole
accendere nei sottotitoli, dove mettere un effetto. Poi i comandi fanno il lavoro
ripetitivo, sempre allo stesso modo.

```
telefono → girato → trascrizione → montaggio.json → comandi → video finito
                                        ↑                         |
                                        └──── "togli quella frase" ┘
```

Ogni correzione è una riga cambiata e un comando rilanciato. Quando una correzione vale
anche per i video futuri, la scrivi in `manuale.md`: l'agente la rilegge ogni volta.

| Passaggio | Cosa succede | Con cosa |
|---|---|---|
| Script | Scrive lo script e ti dice cosa fare in ripresa | la skill `script-reel` |
| Trascrizione | Trascrive il girato parola per parola | ElevenLabs Scribe |
| Tagli | Sceglie sul testo, poi lo stacco lo decide il suono | Python, FFmpeg |
| Voce | Pulizia standard e volume costante | FFmpeg |
| Sottotitoli | Sottotitoli a pillola, con le aree sicure dei social | Remotion |
| Copertina | Cerca un fotogramma col sorriso e ci mette il titolo | MediaPipe, Remotion |
| Effetti | Scritte dietro la testa, cloni, fumetti e altro: 16 pronti, 22 ricette | EffectCraft, MediaPipe |
| Musica | Una base scritta nota per nota, sotto la voce | FluidSynth |
| Controlli | Dicono in italiano cosa non va, prima di pubblicare | Python |

**Provato su Windows, non ancora su Mac e Linux.** Se lo provi lì, aspettati qualche
inciampo.

## Cosa serve

- **Un agente:** Claude Code o Codex, con il tuo abbonamento.
- **Un computer:** Windows, Mac o Linux. Una scheda video aiuta, ma non serve.
- **Spazio:** circa 1,5 GB per il kit, più i tuoi video.
- **Una chiave ElevenLabs,** per la trascrizione. Il piano gratuito basta: 10.000 crediti
  al mese, circa 30 minuti di audio. Si crea su elevenlabs.io, in Developers, API Keys.

## Installazione

### 1. Scarica il kit

In cima a questa pagina premi il pulsante verde **Code**, poi **Download ZIP**, ed
estrai la cartella dove vuoi. Se usi Git:

```
git clone https://github.com/Bodaus/montaggio-senza-timeline.git
```

### 2. Quello che il kit non può installare da solo

Installa Python, FFmpeg e Node. Su Windows, in un terminale:

```
winget install Python.Python.3.12
winget install Gyan.FFmpeg
winget install OpenJS.NodeJS.LTS
```

Su Mac, con [Homebrew](https://brew.sh):

```
brew install python@3.12 ffmpeg node fluid-synth
```

Chiudi e riapri il terminale. Serve Python fra la 3.10 e la 3.12: la 3.13 non è provata.
Su Mac, ovunque qui e nei prompt trovi `python`, scrivi `python3.12`.

### 3. Il resto

Apri l'agente dentro questa cartella e scrivigli:

> Installa il kit: lancia `python kit.py installa`. Se qualcosa non va, sistemalo e
> rilancia. Poi lancia `python kit.py controlla` e dimmi com'è messo.

Oppure fallo tu, nel terminale, dentro questa cartella:

```
python kit.py installa
```

Ci vogliono una decina di minuti. Alla fine apri il file `.env` e incolla la chiave
ElevenLabs dopo l'uguale.

### 4. La prova

```
python kit.py controlla
```

Devi vedere tre righe:

```
VERDE  base
VERDE  grafiche
VERDE  effetti
```

Poi la prova vera, che monta un video di esempio dall'inizio alla fine senza consumare
crediti:

```
python kit.py prova
```

Se esce il file in `girati/esempio/pubblicare/`, sei a posto. **Se resta rosso, non
perderci il pomeriggio:** con base verde tagli e sottotitoli funzionano, con base e
grafiche manca solo l'effetto. Chiedi all'agente di guardarci. Se sei del laboratorio,
scrivilo nel gruppo.

## Come si usa

Scrivi all'agente "scrivi lo script di un video su ...". Gira. Poi:

```
python kit.py nuovo mio-video percorso/del/file.mp4
python kit.py trascrivi mio-video
```

Da lì parli con l'agente: i prompt dei passaggi stanno in `prompt/`.

| File | Cos'è |
|---|---|
| `REGOLE.md` | come lavora l'agente, e la forma di `montaggio.json` |
| `manuale.md` | gli errori già pagati. Cresce con i tuoi |
| `effetti.md` | il menu degli effetti: cosa si vede, quando, cosa fare in ripresa |
| `marchio.json` | i tuoi colori e i tuoi caratteri |
| `chi-sono.md` | chi sei e come parli, per gli script |
| `girati/` | un video, una cartella. Tutto si può cancellare e rifare, tranne `girato.mov` e `parole.json` |

I tuoi video e la tua chiave restano sul tuo computer: `.gitignore` li tiene fuori da Git.

## Licenze

Il kit è di Nicola Valletta, con licenza [MIT](LICENSE): usalo e modificalo come vuoi. Il
video di esempio resta suo e serve solo a provare il kit.

Il kit scarica altri strumenti, ognuno con la sua licenza. Remotion è gratis per privati,
non profit e aziende fino a 3 dipendenti: oltre serve la
[licenza aziendale](https://github.com/remotion-dev/remotion/blob/main/LICENSE.md).
EffectCraft è MIT o Apache 2.0. MediaPipe è Apache 2.0. Instrument Sans e IBM Plex Mono
sono OFL. GeneralUser GS si può usare per musica privata e commerciale.
