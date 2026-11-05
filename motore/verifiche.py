"""I controlli sull'uscita. Si guarda il file finito, mai le sorgenti.

Niente di quello che si controlla qui da' errore da solo: un sottotitolo sotto la
didascalia di Instagram, 2,5 s di vuoto, una frase monca escono tutti da un
montaggio "riuscito". Lo si scopre solo cercandolo.

    durata       il file dura quanto la timeline
    volume       attorno a -14,5 LUFS, picchi sotto -1 dBFS
    silenzi      nessun vuoto sopra 0,4 s nella voce
    aree         niente di nostro dove le piattaforme mettono la loro interfaccia
    coperture    primo e ultimo fotogramma: nessun volto che scappa
    ascolta      (--ascolta) ritrascrive l'uscita e la confronta con le parole tenute
"""

import difflib
import re
import subprocess
import unicodedata

import numpy as np

import comune
import parole
import sottotitoli as subs
from comune import FPS, H, SAFE_BOTTOM, SAFE_RIGHT, SAFE_TOP, SUB_TOP, W, Girato, durata, sh
from trascrivi import scribe, solo_parole

SOGLIA_ALFA = 25


def zone():
    y, x = np.mgrid[0:H, 0:W]
    return {"in alto": y < SAFE_TOP, "in basso": y > SAFE_BOTTOM,
            "sotto i pulsanti": (x > SAFE_RIGHT) & (y > 1100)}


def leggi_fotogrammi(cmd, canali):
    passo = W * H * canali
    p = subprocess.Popen([str(c) for c in cmd], stdout=subprocess.PIPE)
    i = 0
    while True:
        buf = p.stdout.read(passo)
        if len(buf) < passo:
            break
        yield i, np.frombuffer(buf, np.uint8).reshape(H, W, canali)
        i += 1
    p.wait()


def tocca(nome, maschera, Z):
    return [f"{nome}: {z}" for z, m in Z.items() if (maschera & m).any()]


def alfa_mov(mov, fps=5):
    """Dove una sovrimpressione con alfa disegna fuori dalle aree."""
    Z = zone()
    trovati = {}
    cmd = ["ffmpeg", "-v", "error", "-i", mov, "-vf", f"fps={fps}", "-f", "rawvideo",
           "-pix_fmt", "rgba", "-"]
    for i, f in leggi_fotogrammi(cmd, 4):
        for r in tocca(mov.name, f[:, :, 3] > SOGLIA_ALFA, Z):
            trovati.setdefault(r, i / fps)
    return [f"{r} (a {t:.1f} s)" for r, t in trovati.items()]


def _volume(f):
    r = subprocess.run(["ffmpeg", "-nostats", "-i", str(f), "-af", "ebur128=peak=true:framelog=quiet",
                        "-f", "null", "-"], capture_output=True, text=True, encoding="utf-8",
                       errors="replace").stderr
    i = re.findall(r"I:\s+(-?[\d.]+) LUFS", r)
    p = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", r)
    return float(i[-1]), float(p[-1])


def _silenzi(f):
    r = subprocess.run(["ffmpeg", "-nostats", "-i", str(f), "-af",
                        "silencedetect=noise=-38dB:d=0.4", "-f", "null", "-"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace").stderr
    return re.findall(r"silence_start: ([\d.]+)", r), re.findall(r"silence_duration: ([\d.]+)", r)


def _coperture(g, uscita):
    """Primo e ultimo fotogramma di ogni copertura sopra la fascia dei sottotitoli."""
    guai = []
    for o in g.overlays():
        if o.get("kind") != "copertura":
            continue
        s = round(o["start_in_output"] * FPS)
        n = round(o["duration"] * FPS)
        for fot, dove, dentro in ((s, "primo", 0), (s + n - 1, "ultimo", n - 1)):
            cmd = ["ffmpeg", "-v", "error", "-i", uscita, "-vf", f"select=eq(n\\,{fot})",
                   "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "gray", "-"]
            a = subprocess.run([str(c) for c in cmd], capture_output=True).stdout
            cmd = ["ffmpeg", "-v", "error", "-i", g.dir / o["file"], "-vf", f"select=eq(n\\,{dentro})",
                   "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "gray", "-"]
            b = subprocess.run([str(c) for c in cmd], capture_output=True).stdout
            if len(a) != W * H or len(b) != W * H:
                continue
            x = np.frombuffer(a, np.uint8).reshape(H, W)[SAFE_TOP:SUB_TOP].astype(int)
            y = np.frombuffer(b, np.uint8).reshape(H, W)[SAFE_TOP:SUB_TOP].astype(int)
            d = float(np.abs(x - y).mean())
            if d > 6:
                guai.append(f"{o['name']}: {dove} fotogramma diverso dalla grafica ({d:.1f})")
    return guai


def _gettoni(ws):
    out = []
    for w in ws:
        t = unicodedata.normalize("NFKD", w["text"].lower().replace("’", "'"))
        t = "".join(c for c in t if not unicodedata.combining(c))
        for p in re.split(r"[\s'\-/]+", t):
            p = re.sub(r"[^\w]", "", p)
            if p:
                out.append(dict(g=p, w=w))
    return out


def ascolta(g, m, tl, uscita):
    """Nessun altro controllo sente che cosa dice il video: una frase monca passa tutti gli altri."""
    wav = g.verifica / "uscita.wav"
    sh(["ffmpeg", "-y", "-v", "error", "-i", g.master, "-vn", "-ac", "1", "-ar", "16000",
        "-c:a", "pcm_s16le", wav])
    sentite = solo_parole(scribe(wav)["words"])
    wav.unlink()
    attese = subs.fuori_tempo(parole.carica(g, m), tl)
    A, B = _gettoni(attese), _gettoni(sentite)
    sm = difflib.SequenceMatcher(None, [x["g"] for x in A], [x["g"] for x in B], autojunk=False)
    diff = []
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == "equal":
            continue
        a, b = " ".join(x["g"] for x in A[i1:i2]), " ".join(x["g"] for x in B[j1:j2])
        if op == "replace" and difflib.SequenceMatcher(None, a, b).ratio() >= 0.75:
            continue
        diff.append(f"{ {'delete': 'mancanti', 'insert': 'in piu', 'replace': 'diverse'}[op] }: "
                    f"attese [{a}] sentite [{b}]")
    return diff


def verifica(nome, ascolta_uscita=False):
    g = Girato(nome)
    m, tl = g.montaggio(), g.timeline()
    g.verifica.mkdir(exist_ok=True)
    uscita = g.pubblicare / f"{tl['slug']}.mp4"
    if not uscita.exists():
        raise SystemExit(f"manca {uscita.name}: prima `kit.py finale {nome}`")
    guai, ok = [], []

    d = durata(uscita)
    if abs(d - tl["totale"]) > 0.12:
        guai.append(f"durata {d:.2f} s contro {tl['totale']:.2f} della timeline")
    else:
        ok.append(f"durata {d:.2f} s")

    li, pk = _volume(uscita)
    if not -16.5 <= li <= -12.5:
        guai.append(f"volume {li:.1f} LUFS, atteso attorno a -14,5")
    if pk > -0.5:
        guai.append(f"picchi a {pk:.1f} dBFS: rischio di distorsione")
    if -16.5 <= li <= -12.5 and pk <= -0.5:
        ok.append(f"volume {li:.1f} LUFS, picchi {pk:.1f} dBFS")

    inizi, durate = _silenzi(g.master)
    fuori = [(float(a), float(b)) for a, b in zip(inizi, durate)]
    if fuori:
        guai += [f"silenzio di {b:.1f} s a {a:.1f} s" for a, b in fuori]
    else:
        ok.append("nessun silenzio sopra 0,4 s")

    aree = []
    # il titolo si controlla in copertina.py, sul solo testo: qui il fotogramma 0 e'
    # pieno di proposito, e la fascia scura sotto il titolo arriva in fondo
    if (g.dir / "sottotitoli.mov").exists():
        aree += alfa_mov(g.dir / "sottotitoli.mov", 10)
    if aree:
        guai += aree
    else:
        ok.append("sottotitoli e titolo dentro le aree")

    cop = _coperture(g, uscita)
    guai += cop
    if not cop and any(o.get("kind") == "copertura" for o in g.overlays()):
        ok.append("coperture da bordo a bordo")

    if ascolta_uscita:
        diff = ascolta(g, m, tl, uscita)
        guai += diff
        if not diff:
            ok.append("l'uscita dice esattamente le parole tenute")

    for r in ok:
        print(f"  ok      {r}")
    for r in guai:
        print(f"  CONTROLLA  {r}")
    (g.verifica / "esito.txt").write_text(
        "\n".join([f"ok: {r}" for r in ok] + [f"controlla: {r}" for r in guai]) + "\n", encoding="utf-8")
    return 1 if guai else 0
