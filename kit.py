#!/usr/bin/env python3
"""Il comando unico del kit. `python kit.py` senza niente mostra cosa c'e'.

Gira con il Python di .venv se esiste: chi lancia il kit con quello di sistema
non deve ricordarsi di attivare niente.
"""

import os
import subprocess
import sys
from pathlib import Path

KIT = Path(__file__).resolve().parent
VENV_PY = KIT / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")

if VENV_PY.exists() and Path(sys.prefix).resolve() != (KIT / ".venv").resolve():
    sys.exit(subprocess.run([str(VENV_PY), __file__, *sys.argv[1:]]).returncode)

sys.path.insert(0, str(KIT / "motore"))
for flusso in (sys.stdout, sys.stderr):
    flusso.reconfigure(encoding="utf-8", errors="replace")

AIUTO = """
Comandi (al posto di NOME il nome del tuo girato):

  python kit.py installa              installa quello che manca
  python kit.py controlla             semafori: base, grafiche, effetti e musica
  python kit.py prova                 monta il video di esempio dall'inizio alla fine

  python kit.py nuovo NOME FILE       crea il girato dal file del telefono
  python kit.py trascrivi NOME        parole con i tempi (Scribe, una volta sola)
  python kit.py bozza NOME            prima proposta di montaggio.json

  python kit.py taglia NOME           tagli, voce e stacchi
  python kit.py grafiche NOME         le coperture dei blocchi "grafica"
  python kit.py sottotitoli NOME      sottotitoli e copertina
  python kit.py effetti NOME [nome]   gli effetti elencati in montaggio.json
  python kit.py finale NOME           il video in pubblicare/, con la musica se attiva

  python kit.py verifica NOME         controlli sull'uscita
  python kit.py tutto NOME            dal taglio al file finito
"""


def main():
    a = sys.argv[1:]
    if not a or a[0] in ("-h", "--help", "aiuto"):
        print(AIUTO)
        return
    cmd, resto = a[0], a[1:]
    if cmd == "installa":
        import installa
        installa.installa()
    elif cmd == "controlla":
        import installa
        sys.exit(installa.controlla())
    elif cmd == "prova":
        import prova
        prova.prova()
    elif cmd == "nuovo":
        import prepara
        from comune import GIRATI
        nome, file = resto[0], resto[1]
        (GIRATI / nome).mkdir(parents=True, exist_ok=True)
        prepara.prepara(nome, file)
    elif cmd == "trascrivi":
        import trascrivi
        trascrivi.trascrivi(resto[0], forza="--forza" in resto)
    elif cmd == "bozza":
        import parole
        parole.bozza(resto[0])
    elif cmd == "taglia":
        import taglio
        taglio.taglia(resto[0])
    elif cmd == "grafiche":
        import grafiche
        grafiche.grafiche(resto[0])
    elif cmd == "sottotitoli":
        import copertina
        copertina.copertina(resto[0])
    elif cmd == "effetti":
        import effetti
        effetti.effetti(resto[0], resto[1:])
    elif cmd == "finale":
        import finale
        finale.finale(resto[0])
    elif cmd == "verifica":
        import verifiche
        sys.exit(verifiche.verifica(resto[0], "--ascolta" in resto))
    elif cmd == "tutto":
        import tutto
        tutto.tutto(resto[0])
    else:
        print(f"comando sconosciuto: {cmd}")
        print(AIUTO)
        sys.exit(2)


if __name__ == "__main__":
    main()
