"""Sottotitoli a gruppi di due o tre parole, fermi, con una pillola che scorre.

Ogni parola passa dalla timeline, perche' dopo il taglio non sta piu' dove stava.

**Dove si va a capo conta piu' di tutto il resto.** Un gruppo non finisce mai su una
parola che regge quella dopo: preposizioni, articoli, congiunzioni. Si provano
tutte le divisioni di una frase e si tiene quella che costa meno. Decidere una
parola alla volta dava "cercarsela / da soli".

**In accento solo quello che conta.** I numeri da soli, e le parole elencate in
`accenti` di montaggio.json. Metterlo in fondo a ogni frase sembra una regola ma
segna la punteggiatura, non il senso. Una ogni tre secondi circa.

Senza Remotion si passa ai sottotitoli ASS, una parola alla volta: niente pillola,
ma il video esce lo stesso.
"""

import json
import re
import unicodedata

import comune
import parole
import ponte_remotion
from comune import FPS, H, W, Girato, durata, hex_rgb, marchio

MAX_DUR = 3.2
GAP_BREAK = 0.34
MAX_CARATTERI = 18

NUMERI = {"due", "tre", "quattro", "cinque", "sette", "otto", "nove", "dieci", "undici",
          "dodici", "venti", "trenta", "quaranta", "cinquanta", "cento", "mille", "mezza"}

DEBOLI = {
    "il", "lo", "la", "i", "gli", "le", "l'", "un", "una", "uno", "un'",
    "di", "da", "a", "in", "con", "su", "per", "tra", "fra",
    "del", "dello", "della", "dei", "degli", "delle",
    "al", "allo", "alla", "ai", "agli", "alle",
    "dal", "dalla", "dai", "nel", "nella", "nei", "sul", "sulla", "sui",
    "e", "ed", "o", "ma", "che", "se", "non", "come", "cui",
    "mi", "ti", "ci", "vi", "si", "ne", "te", "me", "ha", "ho", "è", "sono",
    "più", "meno", "molto",
    "quel", "quella", "quello", "quei", "quelle", "sua", "suo", "sue", "mio", "mia", "tuo", "tua",
}


def testo(w):
    return re.sub(r"(?<=[a-zà-ÿ])([.!?])(?=[A-ZÀ-Þ])", r"\1 ", w["text"].replace("\n", " ")).strip()


def nudo(t):
    t = unicodedata.normalize("NFKC", t).lower().replace("’", "'")
    return t.strip(".,;:?!\"'«»()")


def fuori_tempo(ws, tl):
    """Solo le parole dentro i pezzi tenuti, con il loro tempo d'uscita."""
    out = []
    for c in tl["clips"]:
        lo, hi = c["a_start"], c["a_start"] + c["real_dur"]
        for w in ws:
            s, e = float(w["start"]), float(w["end"])
            if s < lo or s >= hi:
                continue
            # il token puo' sforare il pezzo: si tronca, non si scarta. Una parola
            # che si sente senza didascalia e' sparita cosi' piu' di una volta.
            out.append(dict(text=w["text"].strip(), start=c["out_start"] + (s - lo),
                            end=c["out_start"] + (min(e, hi) - lo), seg=c["id"]))
    out.sort(key=lambda w: w["start"])
    # Scribe scrive minuscola la prima parola di una ripresa sentita a meta' frase
    for i, w in enumerate(out):
        prec = out[i - 1]["text"] if i else "."
        if prec.rstrip().endswith((".", "?", "!")) and w["text"][:1].islower():
            w["text"] = w["text"][0].upper() + w["text"][1:]
    return out


def e_numero(t):
    n = nudo(t)
    return bool(re.search(r"\d", n)) or n in NUMERI


def marca_forti(ws, m):
    voluti = [nudo(a) for a in m.get("accenti", [])]
    for w in ws:
        n = nudo(testo(w))
        w["forte"] = e_numero(w["text"])
        if n in voluti:
            voluti.remove(n)     # una voce nell'elenco accende una parola sola
            w["forte"] = True
    if voluti:
        raise SystemExit(f"accenti che non cadono su nessuna parola tenuta: {voluti}. "
                         "Il montaggio e' cambiato: rivedi l'elenco.")
    return ws


def _debole(w):
    return nudo(testo(w)) in DEBOLI


def _chiude_male(g):
    if e_numero(g[-1]["text"]) and not testo(g[-1]).endswith((",", ".", "?", "!", ":")):
        return True
    if not _debole(g[-1]):
        return False
    return not (nudo(testo(g[-1])) == "più" and len(g) > 1 and nudo(testo(g[-2])) == "di")


def _costo(g, ultimo):
    t = " ".join(testo(w) for w in g)
    if len(g) > 1 and len(t) > MAX_CARATTERI:
        return None
    if g[-1]["end"] - g[0]["start"] > MAX_DUR:
        return None
    c = 0.0
    if not ultimo and _chiude_male(g):
        c += 20
    if len(g) == 1 and not g[0].get("forte"):
        c += 3
    if all(_debole(w) for w in g):
        c += 8
    c += 4 * sum(testo(w).endswith(",") for w in g[:-1])
    return c + 0.02 * (len(t) - 13) ** 2


def _dividi(fr):
    n = len(fr)
    meglio = [0.0] + [None] * n
    da = [0] * (n + 1)
    for j in range(1, n + 1):
        for i in range(max(0, j - 5), j):
            if meglio[i] is None:
                continue
            c = _costo(fr[i:j], j == n)
            if c is not None and (meglio[j] is None or meglio[i] + c < meglio[j]):
                meglio[j], da[j] = meglio[i] + c, i
    gruppi, j = [], n
    while j > 0:
        i = da[j] if meglio[j] is not None else j - 1
        gruppi.insert(0, fr[i:j])
        j = i
    return gruppi


def gruppi(g, m=None, tl=None):
    m = m or g.montaggio()
    tl = tl or g.timeline()
    ws = marca_forti(fuori_tempo(parole.carica(g, m), tl), m)
    fr, cur = [], []
    for w in ws:
        if cur and w["start"] - cur[-1]["end"] > GAP_BREAK:
            fr.append(cur)
            cur = []
        cur.append(w)
        if testo(w).rstrip().endswith((".", "?", "!", ":")):
            fr.append(cur)
            cur = []
    if cur:
        fr.append(cur)
    tutti = [x for f in fr for x in _dividi(f)]
    out = []
    for i, x in enumerate(tutti):
        a, b = x[0]["start"], x[-1]["end"]
        dopo = tutti[i + 1][0]["start"] if i + 1 < len(tutti) else tl["totale"]
        b = min(dopo - 0.02, b + 0.22, a + MAX_DUR)
        if b > a:
            out.append(dict(a=round(a, 3), b=round(b, 3),
                            parole=[dict(testo=testo(w), t=round(a if j == 0 else w["start"], 3),
                                         forte=bool(w["forte"])) for j, w in enumerate(x)]))
    return out


def rendi_pillola(g, da=0.0):
    dur = durata(g.master)
    dest = g.dir / "sottotitoli.mov"
    gg = [x for x in gruppi(g) if x["a"] >= da - 0.001]
    ponte_remotion.alfa("sottotitoli", dict(dur=round(dur, 3), stile="pillola", gruppi=gg), dest)
    print(f"  {len(gg)} gruppi di sottotitoli")
    return dest


_ASS = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Main,{font},96,&H00{testo},&H00{testo},&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,8,2,2,60,200,{mv},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def _bgr(h):
    r, gg, b = hex_rgb(h)
    return f"{b:02X}{gg:02X}{r:02X}"


def _ts(t):
    h, r = divmod(max(0.0, t), 3600)
    m, s = divmod(r, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def rendi_ass(g, da=0.0):
    """La via di riserva: una parola alla volta, con libass, senza Node."""
    k = marchio()
    testa = _ASS.format(font=k["font"], testo=_bgr(k["testo"]), mv=H - comune.SAFE_BOTTOM + 20)
    righe = []
    for x in gruppi(g):
        if x["a"] < da - 0.001:
            continue
        for i, p in enumerate(x["parole"]):
            a = p["t"]
            b = x["parole"][i + 1]["t"] if i + 1 < len(x["parole"]) else x["b"]
            if b <= a:
                continue
            col = _bgr(k["accento"]) if p["forte"] else _bgr(k["testo"])
            righe.append(f"Dialogue: 0,{_ts(a)},{_ts(b)},Main,,0,0,0,,"
                         rf"{{\fscx88\fscy88\t(0,110,\fscx100\fscy100)\c&H{col}&}}{p['testo']}")
    dest = g.dir / "sottotitoli.ass"
    dest.write_text(testa + "\n".join(righe) + "\n", encoding="utf-8")
    print(f"  {len(righe)} parole in {dest.name} (Remotion assente: niente pillola)")
    return dest


def sottotitoli(nome, da=0.0):
    g = Girato(nome)
    return rendi_pillola(g, da) if ponte_remotion.disponibile() else rendi_ass(g, da)
