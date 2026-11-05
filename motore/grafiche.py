"""Le coperture dei blocchi "grafica".

Su quei blocchi hai letto dallo schermo: il girato sotto non si puo' vedere, quindi
la copertura va da bordo a bordo, al fotogramma, e parte 0,30 s prima del blocco per
nascondere anche l'occhio che scende al copione.

Le battute non si scrivono in secondi: si indica la parola, e il tempo si ricava dal
montaggio. Cosi' se cambiano i tagli le grafiche si riallineano da sole.

Nel blocco di montaggio.json:
    "tipo": "grafica",
    "grafica": {
      "occhiello": "IL CONTO",
      "titolo": "Quello che conta davvero",
      "voci": [{"testo": "Fiere", "parola": "fiere"}, {"testo": "Sito", "parola": "sito"}],
      "esito": {"testo": "La frase che resta", "parola": "prezzo"}
    }
"""

import parole
import ponte_remotion
import sottotitoli as subs
from comune import FPS, Girato

ANTICIPO = 0.30


def battuta(ws, blocco_id, parola, ripiego):
    """Il secondo d'uscita della parola dentro il blocco."""
    voluta = subs.nudo(parola)
    for w in ws:
        if w["seg"].rstrip("abcdefghij") == blocco_id and subs.nudo(subs.testo(w)) == voluta:
            return w["start"]
    print(f"  attenzione: {parola!r} non c'e' nel blocco {blocco_id}, uso un tempo di ripiego")
    return ripiego


def grafiche(nome):
    g = Girato(nome)
    m, tl = g.montaggio(), g.timeline()
    g.grafiche.mkdir(exist_ok=True)
    ws = subs.fuori_tempo(parole.carica(g, m), tl)
    righe = [o for o in g.overlays() if o.get("kind") != "copertura"]
    blocchi = {b["id"]: b for b in tl["blocks"]}
    fatte = 0
    for s in m["blocchi"]:
        if s.get("tipo") != "grafica":
            continue
        if not s.get("grafica"):
            raise SystemExit(f"blocco {s['id']}: e' di tipo grafica ma manca il campo `grafica`")
        if not ponte_remotion.disponibile():
            print(f"  {s['id']}: Remotion assente, niente copertura")
            continue
        b = blocchi[s["id"]]
        prec = [x for x in tl["blocks"] if x["out_start"] < b["out_start"]]
        anticipo = ANTICIPO if prec and prec[-1]["tipo"] != "grafica" else 0.0
        inizio = round((b["out_start"] - anticipo) * FPS) / FPS
        fine = round((b["out_start"] + b["dur"]) * FPS) / FPS
        dur = round(fine - inizio, 3)
        gr = s["grafica"]
        voci = gr.get("voci", [])
        rel = lambda v, i, n: round(battuta(ws, s["id"], v.get("parola", ""),
                                            b["out_start"] + b["dur"] * (i + 1) / (n + 1)) - inizio, 3)
        props = dict(dur=dur, occhiello=gr.get("occhiello", ""), titolo=gr.get("titolo", ""),
                     voci=[dict(testo=v["testo"], t=rel(v, i, len(voci))) for i, v in enumerate(voci)],
                     esito=(dict(testo=gr["esito"]["testo"], t=rel(gr["esito"], len(voci), len(voci)))
                            if gr.get("esito") else None))
        f = g.grafiche / f"{s['id']}.mov"
        ponte_remotion.opaca("copertura", props, f)
        righe = [o for o in righe if o["name"] != s["id"]]
        righe.append(dict(name=s["id"], file=f"grafiche/{f.name}", start_in_output=inizio,
                          duration=dur, alpha=False, kind="copertura"))
        fatte += 1
        print(f"  {s['id']}: copertura di {dur:.2f} s")
    g.salva_overlays(righe)
    print(f"  {fatte} coperture")
