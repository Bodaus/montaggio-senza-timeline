"""Le grafiche rese con Remotion, chiamate dal motore Python.

Palette e misure non si riscrivono in TypeScript: `brand.ts` si genera a ogni resa
da marchio.json e comune.py. Due elenchi di colori tenuti a mano divergono in
silenzio. Durate e battute arrivano come proprieta'.
"""

import json
import os
import shutil
import tempfile
from pathlib import Path

import comune
from comune import FPS, H, MOTORE, W, durata, hex_rgb, marchio, sh

PROGETTO = MOTORE / "remotion"
NPX = "npx.cmd" if os.name == "nt" else "npx"
SOVRA = 2       # le coperture si rendono al doppio e si riducono: bordi puliti


def disponibile():
    return (PROGETTO / "node_modules" / "remotion").is_dir() and bool(shutil.which(NPX))


def _mix(a, b, q):
    ra, rb = hex_rgb(a), hex_rgb(b)
    return "#%02X%02X%02X" % tuple(round(x + (y - x) * q) for x, y in zip(ra, rb))


PESI = {"Regular": 400, "Medium": 500, "SemiBold": 600, "Bold": 700}


def _caratteri():
    """I font di font/: Nome-Peso.ttf. Si copiano dove Remotion li serve."""
    from fontTools.ttLib import TTFont
    dest = PROGETTO / "public" / "font"
    dest.mkdir(parents=True, exist_ok=True)
    fuori = []
    for f in sorted(comune.FONT.glob("*.ttf")):
        if not (dest / f.name).exists():
            shutil.copy(f, dest / f.name)
        nomi = TTFont(f)["name"]
        fam = nomi.getDebugName(16) or nomi.getDebugName(1)
        fuori.append(dict(famiglia=fam, file=f.name, peso=PESI.get(f.stem.split("-")[-1], 400)))
    return fuori


def _brand():
    m = marchio()
    dati = dict(
        w=W, h=H, fps=FPS, famDisplay=m["font"], famText=m["font"], famMono=m["font_etichette"],
        pesoTitolo=400, subTop=comune.SUB_TOP, margin=comune.MARGIN, titleY=240,
        safeTop=comune.SAFE_TOP, safeBottom=comune.SAFE_BOTTOM,
        safeLeft=comune.SAFE_LEFT, safeRight=comune.SAFE_RIGHT,
        bg=m["fondo"], panel=m["pannello"], text=m["testo"], dim=m["testo_spento"],
        accent=m["accento"], on_accent=m["testo_su_accento"],
        rule=_mix(m["fondo"], m["testo"], 0.22), sign=_mix(m["fondo"], m["testo"], 0.35),
        acc_bg=_mix(m["fondo"], m["accento"], 0.10), caratteri=_caratteri())
    (PROGETTO / "src" / "brand.ts").write_text(
        "// Generato da ponte_remotion.py: non si modifica a mano.\n"
        f"export const BRAND = {json.dumps(dati, indent=2, ensure_ascii=False)} as const;\n",
        encoding="utf-8")


def _con_props(props):
    fh = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8")
    json.dump(props, fh, ensure_ascii=False)
    fh.close()
    return fh.name


def _rendi(comp, props, extra, dest):
    _brand()
    p = _con_props(props)
    try:
        sh([NPX, "remotion", "render", "src/index.ts", comp, str(dest), f"--props={p}",
            "--log=error", *extra], cwd=PROGETTO)
    finally:
        Path(p).unlink(missing_ok=True)


def alfa(comp, props, dest):
    """Una grafica con canale alfa: ProRes 4444, che ffmpeg sovrappone senza sapere da dove viene."""
    _rendi(comp, props, ["--codec=prores", "--prores-profile=4444", "--image-format=png",
                         "--pixel-format=yuva444p10le"], dest)
    return durata(dest)


def opaca(comp, props, dest):
    """Una copertura piena, resa al doppio: la riduzione fa da antialiasing vero."""
    alto = Path(dest).with_suffix(".alto.mp4")
    try:
        _rendi(comp, props, [f"--scale={SOVRA}", "--codec=h264", "--crf=12"], alto)
        sh(["ffmpeg", "-y", "-v", "error", "-i", alto, "-vf", f"scale={W}:{H}:flags=lanczos",
            "-c:v", "libx264", "-crf", "16", "-preset", "fast", "-pix_fmt", "yuv420p",
            "-r", str(FPS), dest])
    finally:
        alto.unlink(missing_ok=True)
    return durata(dest)


def fermo(comp, props, dest, frame=0):
    _brand()
    p = _con_props(props)
    try:
        sh([NPX, "remotion", "still", "src/index.ts", comp, str(dest), f"--props={p}",
            f"--frame={frame}", "--image-format=png", "--log=error"], cwd=PROGETTO)
    finally:
        Path(p).unlink(missing_ok=True)
