"""Gli effetti sulle persone: EffectCraft piu' le sagome di MediaPipe.

Ogni effetto e' un tratto del master rifatto per intero, fotogramma per fotogramma,
con la persona ritagliata sopra i testi: cosi' i testi le passano dietro. In
`finale.py` viene steso prima delle coperture.

Un effetto si scrive in `effetti` di montaggio.json. Si indica il blocco e, per ogni
stile, la parola su cui parte:

    {"nome": "e1", "blocco": "b3",
     "sale": {"testo": "NON SERVE", "parola": "serve", "pieno": true},
     "spegni": {"parola": "serve", "fine": true}}

Gli stili si combinano. Sulla persona: nastro, sale, estruso, scheda (con "ribalta"
e "accento"), spegni, sfoca, vicino, colpo, profondita, folla, vertigo. Su tutto il
quadro: fumetto, glitch. A parte: timbro, che non chiede la sagoma.

Regole di dosaggio, tutte imparate guardando il risultato:
- un effetto segna un momento, non accompagna il video: uno ogni 8-10 secondi;
- il contorno (`spegni`) al massimo due volte per video;
- due effetti di fila mai dello stesso stile;
- mai sul volto quando non guardi in camera.

    python kit.py effetti NOME           tutti
    python kit.py effetti NOME e1        solo quello
"""

import json
import subprocess
import sys

import numpy as np

import effetti_scene as S
import parole
import ponte_remotion
import sottotitoli as subs
from comune import CIMA, FPS, MOTORE, STRUMENTI, Girato, blocco, fotogrammi, marchio, sh

STILI = ("nastro", "sale", "scheda", "estruso", "profondita", "folla", "fumetto", "vertigo",
         "glitch", "spegni", "sfoca", "vicino", "colpo")


def cerca_effectcraft():
    nome = "effectcraft-cli.exe" if sys.platform == "win32" else "effectcraft-cli"
    trovati = sorted((STRUMENTI / "effectcraft").rglob(nome)) if (STRUMENTI / "effectcraft").is_dir() else []
    return trovati[-1] if trovati else None


def _tratto(tl, blocchi):
    bb = [blocco(tl, i) for i in blocchi]
    a = round(bb[0]["out_start"] * FPS)
    b = round((bb[-1]["out_start"] + bb[-1]["dur"]) * FPS)
    return a, b - a


def _piano(g, nome, f0, n):
    d = g.dir / "_effetti" / nome
    d.mkdir(parents=True, exist_ok=True)
    p = d / "piano.mov"
    sh(["ffmpeg", "-y", "-v", "error", "-i", g.master, "-an",
        "-vf", f"select=between(n\\,{f0}\\,{f0 + n - 1}),setpts=N/{FPS}/TB",
        "-frames:v", n, "-c:v", "prores_ks", "-profile:v", "3", "-pix_fmt", "yuv422p10le", p])
    return d, p


def _sagome(d, p, colore):
    sh([sys.executable, MOTORE / "sagome.py", p, "--out", d / "sagome", "--contorno", "9",
        "--colore", colore])
    return d / "sagome"


def _volti(d, p):
    j = d / "volti.json"
    sh([sys.executable, MOTORE / "traccia_volti.py", p, "--out", j, "--volti", "1"])
    fot = json.loads(j.read_text())["fotogrammi"]
    boxes = np.array([f["volti"][0]["box"] for f in fot if f["volti"]])
    if not len(boxes):
        raise SystemExit(f"{d.name}: nessun volto nel tratto")
    return boxes


def _sfondo_vuoto(d, p, sag):
    """Il tratto senza la persona: la sagoma allargata riempita da OpenCV."""
    import cv2
    out = d / "vuoto.mov"
    if out.exists():
        return out
    tmp = d / "vuoto"
    tmp.mkdir(exist_ok=True)
    cap = cv2.VideoCapture(str(p))
    k = 0
    nucleo = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (45, 45))
    while True:
        ok, fr = cap.read()
        if not ok:
            break
        m = cv2.imread(str(sag / "persona" / f"{k:04d}.png"), cv2.IMREAD_GRAYSCALE)
        m = cv2.dilate((m > 40).astype(np.uint8) * 255, nucleo)
        piccolo = cv2.resize(fr, (540, 960), interpolation=cv2.INTER_AREA)
        mp_ = cv2.resize(m, (540, 960), interpolation=cv2.INTER_NEAREST)
        riempito = cv2.inpaint(piccolo, mp_, 9, cv2.INPAINT_TELEA)
        su = cv2.resize(riempito, (fr.shape[1], fr.shape[0]), interpolation=cv2.INTER_CUBIC)
        a = (cv2.GaussianBlur(m, (0, 0), 6) / 255.0)[..., None]
        cv2.imwrite(str(tmp / f"{k:04d}.png"), (su * a + fr * (1 - a)).astype(np.uint8))
        k += 1
    sh(["ffmpeg", "-y", "-v", "error", "-framerate", FPS, "-i", tmp / "%04d.png",
        "-c:v", "prores_ks", "-profile:v", "3", "-pix_fmt", "yuv422p10le", out])
    return out


def _cima_testa(sag, cx, da, a):
    import cv2
    cime = []
    for p in sorted((sag / "persona").glob("*.png")):
        if not da * FPS <= int(p.stem) <= a * FPS:
            continue
        m = cv2.imread(str(p), cv2.IMREAD_GRAYSCALE)[:, max(0, int(cx) - 220):int(cx) + 220]
        r = np.where(m.max(1) > 128)[0]
        if len(r):
            cime.append(int(r[0]))
    return float(min(cime)) if cime else 400.0


class Tempi:
    """Traduce la parola di uno stile nel secondo dentro il tratto."""

    def __init__(self, ws, blocchi, f0, dur):
        self.ws, self.blocchi, self.t0, self.dur = ws, blocchi, f0 / FPS, dur

    def di(self, e, chiave="parola"):
        if e.get(chiave):
            voluta = subs.nudo(e[chiave])
            for w in self.ws:
                if w["seg"].rstrip("abcdefghij") in self.blocchi and subs.nudo(subs.testo(w)) == voluta:
                    return max(0.0, w["start"] - self.t0)
            raise SystemExit(f"la parola {e[chiave]!r} non c'e' nei blocchi {self.blocchi}")
        return float(e.get("t", 0.0))


def _aria(testa, nome, minimo=90):
    """Lo spazio fra la testa e il limite alto. Senza, una scritta dietro la testa non esiste."""
    if testa - CIMA < minimo:
        print(f"  attenzione, {nome}: poca aria sopra la testa ({testa - CIMA:.0f} px). "
              "Su quel blocco usa uno zoom piu' largo o \"testa\": 0.22, poi rilancia taglia")
    return max(testa, CIMA + minimo)


def costruisci(g, e, ws, tl, ec):
    nome = e["nome"]
    blocchi = e["blocco"] if isinstance(e["blocco"], list) else [e["blocco"]]
    f0, n = _tratto(tl, blocchi)
    dur = n / FPS
    m = marchio()
    accento = m["accento"].lstrip("#")
    dest = g.grafiche / f"{nome}.mov"
    d, p = _piano(g, nome, f0, n)
    sag = _sagome(d, p, accento)
    boxes = _volti(d, p)
    cx = float(np.median((boxes[:, 0] + boxes[:, 2]) / 2))
    y0 = float(np.median(boxes[:, 1]))
    fh = float(np.median(boxes[:, 3] - boxes[:, 1]))
    acc = ", ".join(f"{int(accento[i:i + 2], 16) / 255:.4f}" for i in (0, 2, 4))
    q = lambda s: json.dumps(s, ensure_ascii=False)
    fine = lambda da: max(da + 1.0, dur - 0.45)
    T = Tempi(ws, blocchi, f0, dur)
    torna_di = lambda x, da: fine(da) if x.get("fine") else 0.0

    js = S.BASE % dict(dur=dur, acc=acc, font=m["font"], piano=p.as_posix())
    if "nastro" in e:
        x = e["nastro"]
        da = T.di(x)
        testa = _aria(_cima_testa(sag, cx, da, dur), nome)
        veloce = (840 + 520 * (dur - da)) / (0.55 * len(x["testo"]))
        corpo = int(min(320, (testa - CIMA) / (0.45 * 0.72), veloce))
        js += S.NASTRO % dict(testo=q(x["testo"]), corpo=corpo, pieno=str(x.get("pieno", True)).lower(),
                              testa=testa, da=da, a=dur)
    if "sale" in e:
        x = e["sale"]
        da = max(0.0, T.di(x) - 0.2)
        testa = _aria(_cima_testa(sag, cx, da, dur), nome)
        copre = 0.25    # la testa copre al massimo il quarto basso delle lettere
        corpo = int(min(300, 940 / (0.68 * len(x["testo"])), (testa - CIMA) / ((1 - copre) * 0.74)))
        js += S.SALE % dict(testo=q(x["testo"]), corpo=corpo, pieno=str(x.get("pieno", True)).lower(),
                            testa=testa, copre=copre, da=da, torna=fine(da))
    if "scheda" in e:
        x = e["scheda"]
        da = max(0.0, T.di(x) - 0.25)
        testa = _aria(_cima_testa(sag, cx, da, dur), nome)
        corpo = min(66, int(((testa - CIMA) / 0.75 - 44) / 1.08), int(900 / (0.66 * len(x["testo"]))))
        torna = dur - 0.45 if dur - da > 1.6 else 0.0
        js += S.SCHEDA % dict(testo=q(x["testo"]), corpo=corpo, accento=str(bool(x.get("accento"))).lower(),
                              cx=cx, testa=testa, da=da, torna=torna,
                              ribalta=str(bool(x.get("ribalta"))).lower())
    if "estruso" in e:
        x = e["estruso"]
        da = max(0.0, T.di(x) - 0.2)
        testa = _aria(_cima_testa(sag, cx, da, dur), nome)
        copre = 0.25
        corpo = int(min(300, 900 / (0.68 * len(x["testo"])), (testa - CIMA) / ((1 - copre) * 0.74)))
        js += S.ESTRUSO % dict(testo=q(x["testo"]), corpo=corpo, testa=testa, copre=copre, da=da,
                               torna=fine(da), xc=min(max(cx, 300), 780), bordo=max(16, round(0.12 * corpo)))
    js += S.PERSONA % dict(ritaglio=(sag / "ritaglio.mov").as_posix(),
                           contorno=(sag / "contorno.mov").as_posix())
    if "profondita" in e:
        js += S.PROFONDITA % dict(vuoto=_sfondo_vuoto(d, p, sag).as_posix(), da=T.di(e["profondita"]),
                                  cx=cx, cy=y0 + 0.5 * fh)
    if "folla" in e:
        js += S.FOLLA % dict(da=T.di(e["folla"]), ax=cx, ay=y0 + 0.5 * fh,
                             s=round(min(24.0, 12000.0 / fh), 2))
    if "fumetto" in e:
        x = e["fumetto"]
        fin = T.di(x, "parola_fine") + 0.25 if x.get("parola_fine") else dur
        js += S.FUMETTO % dict(da=T.di(x), a=min(dur, fin))
    if "vertigo" in e:
        js += S.VERTIGO % dict(vuoto=_sfondo_vuoto(d, p, sag).as_posix(), da=T.di(e["vertigo"]),
                               cx=cx, cy=y0 + 0.5 * fh)
    if "glitch" in e:
        js += S.GLITCH % dict(da=T.di(e["glitch"]))
    if "spegni" in e:
        x = e["spegni"]
        da = T.di(x)
        torna = torna_di(x, da)
        js += S.luce("tinta.property(3)", da, torna, 100)
        js += S.luce("scuro.transform.opacity", da, torna, 42)
        js += S.luce("contorno.transform.opacity", da, torna, 100)
    if "sfoca" in e:
        x = e["sfoca"]
        da = T.di(x)
        torna = torna_di(x, da)
        js += S.luce("sfoc.property(1)", da, torna, 28)
        js += S.luce("scuro.transform.opacity", da, torna, 22)
    vuoti = [e[x] for x in ("nastro", "sale") if x in e and not e[x].get("pieno", True)]
    if vuoti and "spegni" not in e and "sfoca" not in e:
        da = T.di(vuoti[0])
        js += S.luce("sfoc.property(1)", da, fine(da), 14)
        js += S.luce("scuro.transform.opacity", da, fine(da), 30)
    if "vicino" in e:
        js += S.scala(T.di(e["vicino"]), dur - 0.04, 114, cx, y0 + 0.5 * fh)
    if "colpo" in e:
        t = T.di(e["colpo"])
        js += S.scala(t - 0.06, t + 0.12, 108, cx, y0 + 0.5 * fh, inf=90)

    (d / "scena.jsx").write_text(js, encoding="utf-8")
    prog = d / "scena.ecproj"
    r = subprocess.run([str(ec), "script", str(d / "scena.jsx"), "--empty", "--save-as", str(prog)],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode:
        raise SystemExit(r.stdout + r.stderr)

    # la tavola: sei istanti, per guardare sguardo e testi prima di montare
    png = []
    for i, t in enumerate(np.linspace(0.1, dur - 0.1, 6)):
        f = d / f"tav{i}.png"
        sh([ec, "render-frame", "--project", prog, "--comp", "Effetto", "--time", f"{t:.2f}",
            "--scale", "0.3", "--out", f])
        png.append(f)
    ingressi = [x for f in png for x in ("-i", f)]
    sh(["ffmpeg", "-v", "error", "-y", *ingressi, "-filter_complex", f"hstack=inputs={len(png)}",
        g.verifica / f"effetto_{nome}.png"])
    sh([ec, "render", "--project", prog, "--comp", "Effetto", "--out", dest.resolve().as_posix(),
        "--format", "prores", "--prores", "hq"])
    if fotogrammi(dest) != n:
        raise SystemExit(f"{nome}: {fotogrammi(dest)} fotogrammi invece di {n}")
    print(f"  {nome}: {n} fotogrammi da {f0 / FPS:.2f} s")
    return dict(name=nome, file=f"grafiche/{nome}.mov", start_in_output=round(f0 / FPS, 3),
                duration=round(n / FPS, 3), alpha=False, kind="effetto")


def timbro(g, e, ws, tl):
    """Il timbro e' Remotion: una sovrimpressione con alfa, nessuna sagoma."""
    nome = e["nome"]
    blocchi = e["blocco"] if isinstance(e["blocco"], list) else [e["blocco"]]
    f0, n = _tratto(tl, blocchi)
    T = Tempi(ws, blocchi, f0, n / FPS)
    x = e["timbro"]
    t = T.di(x)
    dur = min(n / FPS, t + float(x.get("dura", 2.0)))
    dest = g.grafiche / f"{nome}.mov"
    ponte_remotion.alfa("timbro", dict(dur=round(dur, 3), t=round(t, 3), testo=x["testo"],
                                       centro=dict(x=x.get("x", 480), y=x.get("y", 1030))), dest)
    print(f"  {nome}: timbro a {f0 / FPS + t:.2f} s")
    return dict(name=nome, file=f"grafiche/{nome}.mov", start_in_output=round(f0 / FPS, 3),
                duration=round(dur, 3), alpha=True, kind="alfa", t_colpo=round(f0 / FPS + t, 3))


def effetti(nome, soli=()):
    g = Girato(nome)
    m, tl = g.montaggio(), g.timeline()
    voci = m.get("effetti", [])
    if not voci:
        print("  nessun effetto in montaggio.json")
    g.grafiche.mkdir(exist_ok=True)
    g.verifica.mkdir(exist_ok=True)
    ws = subs.fuori_tempo(parole.carica(g, m), tl)
    righe = [o for o in g.overlays()
             if o.get("kind") == "copertura" or o["name"] in {e["nome"] for e in voci}]
    for e in voci:
        if soli and e["nome"] not in soli:
            continue
        ignoti = set(e) - set(STILI) - {"nome", "blocco", "timbro"}
        if ignoti:
            raise SystemExit(f"{e['nome']}: stili sconosciuti {sorted(ignoti)}. Ci sono: {', '.join(STILI)}, timbro")
        fatti = []
        if "timbro" in e:
            if not ponte_remotion.disponibile():
                raise SystemExit("il timbro ha bisogno di Remotion: `kit.py installa`")
            fatti.append(timbro(g, e, ws, tl))
        if set(e) & set(STILI):
            ec = cerca_effectcraft()
            if not ec:
                raise SystemExit("manca EffectCraft: `kit.py installa`")
            fatti.append(costruisci(g, e, ws, tl, ec))
        righe = [o for o in righe if o["name"] != e["nome"]]
        righe += fatti
    g.salva_overlays(righe)
