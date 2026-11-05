"""Le parole del girato, corrette, e la bozza di `montaggio.json`.

`correzioni` in montaggio.json accetta due forme:
    {"da": "Cloud", "a": "Claude"}       ovunque, parola per parola
    {"t": 156.9, "a": "2.000 €"}         solo la parola che comincia a quel secondo

Una correzione che non cade su nessuna parola ferma tutto: un refuso che resta nel
sottotitolo non da' errore, e nessun controllo lo vede.
"""

import difflib
import json
import re

from comune import Girato
from trascrivi import solo_parole

ZOOM_NOMI = ("medio", "stretto", "largo")


def carica(g, m=None):
    dati = json.loads(g.parole_json.read_text(encoding="utf-8"))
    ws = solo_parole(dati["words"])
    ws.sort(key=lambda w: float(w["start"]))
    usate = set()
    for i, c in enumerate((m or {}).get("correzioni", [])):
        for w in ws:
            nudo = w["text"].strip()
            finale = nudo[len(nudo.rstrip(".,;:?!")):]
            if "t" in c:
                if abs(float(w["start"]) - float(c["t"])) < 0.02:
                    w["text"] = c["a"] + finale
                    usate.add(i)
            elif nudo.rstrip(".,;:?!").lower() == c["da"].lower():
                w["text"] = c["a"] + finale
                usate.add(i)
    mancate = [c for i, c in enumerate((m or {}).get("correzioni", [])) if i not in usate]
    if mancate:
        raise SystemExit(f"correzioni che non cadono su nessuna parola: {mancate}")
    return ws


def frasi(ws):
    righe, cur = [], []
    for w in ws:
        cur.append(w)
        if w["text"].rstrip().endswith((".", "?", "!")):
            righe.append(cur)
            cur = []
    if cur:
        righe.append(cur)
    return righe


def _testo(fr):
    return " ".join(w["text"].strip() for w in fr)


def _nudo(fr):
    return re.sub(r"[^\w ]", "", _testo(fr).lower())


def _simili(a, b):
    return difflib.SequenceMatcher(None, _nudo(a), _nudo(b)).ratio()


def bozza(nome):
    """Una prima proposta: toglie le prese annunciate da "rifaccio" e quelle ripetute.

    E' una base di partenza. L'agente, con lo script davanti, fa meglio; ma cosi' il
    montaggio si puo' lanciare anche se l'agente non c'e'.
    """
    g = Girato(nome)
    ws = carica(g)
    fr = frasi(ws)
    tenute = []
    for i, f in enumerate(fr):
        pos = [k for k, w in enumerate(f) if re.sub(r"\W", "", w["text"].lower()) == "rifaccio"]
        if pos:
            # quello che segue "rifaccio" nella stessa frase e' la ripresa buona
            resto = f[pos[-1] + 1:]
            successiva = resto or (fr[i + 1] if i + 1 < len(fr) else [])
            if tenute and successiva and _simili(tenute[-1], successiva) > 0.45:
                tenute.pop()
            if resto:
                tenute.append(resto)
            continue
        if tenute and _simili(tenute[-1], f) > 0.72:
            tenute.pop()         # ripetuta senza annunciarlo: vale l'ultima
        tenute.append(f)

    blocchi = []
    for k, f in enumerate(tenute):
        blocchi.append(dict(id=f"b{k + 1}", tipo="volto",
                            zoom=ZOOM_NOMI[k % 3],
                            inizio=round(float(f[0]["start"]), 2),
                            fine=round(float(f[-1]["end"]), 2),
                            testo=_testo(f)))
    titolo = _testo(tenute[0])[:60] if tenute else nome
    m = dict(titolo=titolo, slug=nome,
             copertina=dict(occhiello="", titolo=[[dict(testo=titolo[:30])]]),
             accenti=[], correzioni=[], blocchi=blocchi, effetti=[],
             musica=dict(attiva=False))
    if g.montaggio_json.exists():
        raise SystemExit(f"{g.montaggio_json.name} esiste gia': non lo sovrascrivo")
    g.montaggio_json.write_text(json.dumps(m, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  {len(blocchi)} blocchi su {len(fr)} frasi -> {g.montaggio_json.name}")
