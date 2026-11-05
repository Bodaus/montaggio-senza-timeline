"""La prova di installazione: monta il video di esempio dall'inizio alla fine.

Non chiama Scribe, quindi non consuma crediti: la trascrizione dell'esempio sta nel
kit. Se esce il file, tutta la catena funziona su questo computer.
"""

import shutil

import ponte_remotion
import prepara
import tutto
from comune import GIRATI, KIT


def prova():
    d = GIRATI / "esempio"
    if d.exists():
        shutil.rmtree(d)
    d.mkdir(parents=True)
    src = KIT / "esempio"
    for nome in ("parole.json", "montaggio.json"):
        shutil.copy(src / nome, d / nome)
    print("Preparo il girato di esempio...")
    prepara.prepara("esempio", src / "girato-esempio.mp4")
    tutto.tutto("esempio")
    print(f"\nGuardalo: {d / 'pubblicare'}")
    if not ponte_remotion.disponibile():
        print("Remotion assente: e' uscito con i sottotitoli semplici.")
