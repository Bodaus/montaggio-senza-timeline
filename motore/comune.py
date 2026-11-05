"""Quello che serve a tutti: percorsi, stile, ffmpeg, il girato su disco."""

import json
import os
import platform
import shutil
import subprocess
from pathlib import Path

KIT = Path(__file__).resolve().parent.parent
MOTORE = KIT / "motore"
GIRATI = KIT / "girati"
STRUMENTI = KIT / "strumenti"
FONT = KIT / "font"

W, H, FPS = 1080, 1920, 25
FRAME = 1.0 / FPS

# La sorgente normalizzata. 1440x2560 lascia un margine di 1,33 sui ritagli senza
# ingrandire i pixel, e pesa un terzo del 4K del telefono.
SRC_W, SRC_H = 1440, 2560

# Aree di sicurezza su 1080x1920, le piu' strette fra Reels, TikTok e Shorts.
SAFE_TOP = 260
SAFE_BOTTOM = 1440
SAFE_LEFT = 60
SAFE_RIGHT = 880      # la colonna dei pulsanti: vale sotto y 1100
SUB_TOP = SAFE_BOTTOM - 200
MARGIN = 60
CIMA = 210            # le scritte che restano in campo possono salire fin qui


def marchio():
    return json.loads((KIT / "marchio.json").read_text(encoding="utf-8"))


def hex_rgb(s):
    s = s.lstrip("#")
    return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))


def font_file(peso="Bold"):
    return str(FONT / f"InstrumentSans-{peso}.ttf")


def sh(cmd, **kw):
    """Lancia un comando. Se fallisce dice cosa ha risposto: un errore muto costa ore."""
    r = subprocess.run([str(c) for c in cmd], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", **kw)
    if r.returncode:
        coda = (r.stderr or r.stdout or "").strip().splitlines()[-12:]
        raise SystemExit("comando fallito: " + " ".join(str(c) for c in cmd)[:300]
                         + "\n" + "\n".join(coda))
    return r


def durata(path):
    r = sh(["ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "csv=p=0", path])
    return float(r.stdout.strip())


def fotogrammi(path):
    r = sh(["ffprobe", "-v", "error", "-select_streams", "v:0", "-count_packets",
            "-show_entries", "stream=nb_read_packets", "-of", "csv=p=0", path])
    return int(r.stdout.strip().split(",")[0])


def _encoder(nome):
    try:
        r = subprocess.run(["ffmpeg", "-hide_banner", "-f", "lavfi", "-i",
                            "color=c=black:s=256x256:r=25:d=0.2", "-c:v", nome,
                            "-f", "null", "-"], capture_output=True)
        return r.returncode == 0
    except FileNotFoundError:
        return False


def codifica(pezzi=True):
    """La scheda video se c'e', altrimenti il processore."""
    if not hasattr(codifica, "scelto"):
        codifica.scelto = ("nvenc" if _encoder("h264_nvenc") else
                           "videotoolbox" if platform.system() == "Darwin"
                           and _encoder("h264_videotoolbox") else "x264")
    if codifica.scelto == "nvenc":
        return ["-c:v", "h264_nvenc", "-preset", "p5", "-tune", "hq", "-rc", "vbr",
                "-cq", "16" if pezzi else "21", "-b:v", "0", "-pix_fmt", "yuv420p"]
    if codifica.scelto == "videotoolbox":
        return ["-c:v", "h264_videotoolbox", "-q:v", "72" if pezzi else "62",
                "-pix_fmt", "yuv420p"]
    return ["-c:v", "libx264", "-crf", "16" if pezzi else "20",
            "-preset", "veryfast" if pezzi else "medium", "-pix_fmt", "yuv420p"]


def chiave_scribe():
    """Il primo valore non vuoto vince: una riga vuota non scherma la variabile d'ambiente."""
    env = KIT / ".env"
    if env.exists():
        for riga in env.read_text(encoding="utf-8").splitlines():
            riga = riga.strip()
            if riga.startswith("ELEVENLABS_API_KEY="):
                v = riga.split("=", 1)[1].strip().strip("\"'")
                if v:
                    return v
    return os.environ.get("ELEVENLABS_API_KEY", "").strip() or None


class Girato:
    """Una cartella in girati/. Tutto quello che esce si puo' cancellare e rifare."""

    def __init__(self, nome):
        self.nome = nome
        self.dir = GIRATI / nome
        if not self.dir.is_dir():
            esistenti = ", ".join(sorted(p.name for p in GIRATI.iterdir() if p.is_dir())) or "nessuno"
            raise SystemExit(f"girato {nome!r} non trovato. Esistenti: {esistenti}")
        self.video = self.dir / "girato.mov"
        self.grezzo = self.dir / "voce_grezza.wav"     # 16 kHz mono: decide i tagli
        self.voce = self.dir / "voce.wav"              # 48 kHz mono, con la catena
        self.parole_json = self.dir / "parole.json"
        self.parole_txt = self.dir / "parole.txt"
        self.montaggio_json = self.dir / "montaggio.json"
        self.timeline_json = self.dir / "timeline.json"
        self.inquadratura_json = self.dir / "inquadratura.json"
        self.overlays_json = self.dir / "sovrimpressioni.json"
        self.master = self.dir / "master.mov"
        self.clips = self.dir / "clips"
        self.grafiche = self.dir / "grafiche"
        self.verifica = self.dir / "verifica"
        self.pubblicare = self.dir / "pubblicare"

    def montaggio(self):
        if not self.montaggio_json.exists():
            raise SystemExit(f"manca {self.montaggio_json.name}: prima `kit.py bozza {self.nome}`, "
                             "oppure fallo scrivere all'agente")
        return json.loads(self.montaggio_json.read_text(encoding="utf-8"))

    def timeline(self):
        if not self.timeline_json.exists():
            raise SystemExit(f"manca la timeline: prima `kit.py taglia {self.nome}`")
        return json.loads(self.timeline_json.read_text(encoding="utf-8"))

    def inquadratura(self):
        if self.inquadratura_json.exists():
            return json.loads(self.inquadratura_json.read_text(encoding="utf-8"))
        return {"volto_x": 0.5, "testa_y": 0.16}

    def overlays(self):
        if self.overlays_json.exists():
            return json.loads(self.overlays_json.read_text(encoding="utf-8"))
        return []

    def salva_overlays(self, righe):
        self.overlays_json.write_text(json.dumps(righe, indent=2, ensure_ascii=False),
                                      encoding="utf-8")


def out_t(tl, t):
    """Secondo del girato -> secondo del video montato."""
    clips = tl["clips"]
    for c in clips:
        if c["a_start"] <= t <= c["a_start"] + c["real_dur"]:
            return c["out_start"] + (t - c["a_start"])
    vicino = min(clips, key=lambda c: min(abs(t - c["a_start"]),
                                          abs(t - c["a_start"] - c["real_dur"])))
    return vicino["out_start"] if t < vicino["a_start"] else vicino["out_start"] + vicino["real_dur"]


def blocco(tl, ident):
    for b in tl["blocks"]:
        if b["id"] == ident:
            return b
    raise SystemExit(f"blocco {ident!r} non trovato. Ci sono: "
                     + ", ".join(b["id"] for b in tl["blocks"]))


def serve(comando, consiglio):
    if not shutil.which(comando):
        raise SystemExit(f"manca {comando}: {consiglio}")
