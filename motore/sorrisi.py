"""Il fotogramma della copertina: quello in cui sorridi di piu', guardando in camera.

Solo nei blocchi "volto", e senza l'ultimo 0,6 s di ogni frase: nei blocchi coperti
da grafica si legge dallo schermo, e la ricerca su tutto il girato sceglieva proprio
quei sorrisi, con gli occhi sul copione.

Una risata a bocca aperta e' la copertina migliore: la bocca aperta toglie punti
solo se non sorridi, cioe' se stai parlando.
"""

import math
import os
import subprocess

import numpy as np

from comune import STRUMENTI

os.environ.setdefault("GLOG_minloglevel", "3")
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")

FW, FH = 608, 1080


def _punti(b, m):
    yaw = math.degrees(math.atan2(-m[2, 0], math.hypot(m[2, 1], m[2, 2])))
    sorriso = (b["mouthSmileLeft"] + b["mouthSmileRight"]) / 2
    occhi = 1 - max(b["eyeBlinkLeft"], b["eyeBlinkRight"])
    return sorriso * min(1, occhi / 0.6) - 0.3 * b["jawOpen"] * (1 - sorriso) - max(0, abs(yaw) - 35) / 60


def _cerca(video, crop, tratti, passo):
    import mediapipe as mp
    w, h, x, y = crop
    opz = mp.tasks.vision.FaceLandmarkerOptions(
        base_options=mp.tasks.BaseOptions(model_asset_path=str(STRUMENTI / "modelli" / "face_landmarker.task")),
        output_face_blendshapes=True, output_facial_transformation_matrixes=True, num_faces=1)
    punti = {}
    with mp.tasks.vision.FaceLandmarker.create_from_options(opz) as fl:
        for da, a in tratti:
            raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{da:.3f}", "-t", f"{a - da:.3f}",
                                  "-i", str(video), "-vf",
                                  f"fps={1 / passo},crop={w}:{h}:{x}:{y},scale={FW}:{FH}",
                                  "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                                 capture_output=True, check=True).stdout
            for i, f in enumerate(np.frombuffer(raw, np.uint8).reshape(-1, FH, FW, 3)):
                r = fl.detect(mp.Image(image_format=mp.ImageFormat.SRGB, data=np.ascontiguousarray(f)))
                if r.face_blendshapes:
                    b = {c.category_name: c.score for c in r.face_blendshapes[0]}
                    punti[round(da + i * passo, 2)] = _punti(b, np.array(r.facial_transformation_matrixes[0]))
    return punti


def candidati(g, m, crop, quanti=6):
    """I momenti migliori, in secondi del girato. Lista vuota se MediaPipe non c'e'."""
    try:
        import mediapipe  # noqa: F401
    except ImportError:
        return []
    if not (STRUMENTI / "modelli" / "face_landmarker.task").exists():
        return []
    tratti = [(s["inizio"], s["fine"] - 0.6) for s in m["blocchi"]
              if s.get("tipo", "volto") == "volto" and s["fine"] - s["inizio"] > 0.8]
    grossi = _cerca(g.video, crop, tratti, 0.5)
    migliori = sorted(grossi, key=grossi.get, reverse=True)[:quanti]
    # a mezzo secondo il sorriso pieno cade spesso fra due campioni
    fini = _cerca(g.video, crop, [(t - 0.5, t + 0.5) for t in migliori], 0.1)
    fini.update(grossi)
    scelti = []
    for t in sorted(fini, key=fini.get, reverse=True):
        if all(abs(t - s["t"]) >= 2.0 for s in scelti):
            scelti.append(dict(t=t, punti=round(fini[t], 2)))
        if len(scelti) == quanti:
            break
    return scelti
