"""Dal taglio al file finito, nell'ordine giusto.

Le grafiche e gli effetti vanno sempre rifatti dopo il taglio: sono loro a riallinearsi.
"""

import time

import copertina
import effetti
import finale
import grafiche
import taglio
import verifiche


def tutto(nome):
    t0 = time.time()
    for titolo, fare in (("Taglio", lambda: taglio.taglia(nome)),
                         ("Coperture", lambda: grafiche.grafiche(nome)),
                         ("Effetti", lambda: effetti.effetti(nome)),
                         ("Sottotitoli e copertina", lambda: copertina.copertina(nome)),
                         ("Finale", lambda: finale.finale(nome)),
                         ("Controlli", lambda: verifiche.verifica(nome))):
        print(f"\n== {titolo}")
        t = time.time()
        fare()
        print(f"   ({time.time() - t:.0f} s)")
    print(f"\nFatto in {time.time() - t0:.0f} s")
