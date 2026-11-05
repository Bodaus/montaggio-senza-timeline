"""Le sagome delle persone di un video: maschere, ritaglio e contorno.

    python sagome.py VIDEO --out CARTELLA [--modello multi|semplice] [--contorno PX] [--colore D4A63C]

Scrive in CARTELLA:
    persona/%04d.png    la persona (bianco = dentro), un PNG per fotogramma
    capelli/ viso/ vestiti/    solo col modello multi
    ritaglio.mov        il video con la trasparenza fuori dalle persone (ProRes 4444)
    contorno.mov        il bordo intorno alle persone, nel colore dato (ProRes 4444),
                        se --contorno > 0

Modelli MediaPipe in `modelli/`:
- `multi` (selfie_multiclass_256x256, 16 MB): sfondo, capelli, pelle del corpo,
  pelle del viso, vestiti, altro. Prende anche chi sta di lato: e' il default.
- `semplice` (selfie_segmenter, 0,25 MB): persona contro sfondo. Bordi simili,
  ma sulla prova di Wave perdeva la seconda persona.

La confidenza si ammorbidisce nel tempo (LISCIO) e il bordo e' una rampa stretta
intorno a 0,5: cosi' non trema. Sui capelli resta un po' morbido.
Serve `ffmpeg` sul PATH.
"""

import argparse
import shutil
import subprocess
from pathlib import Path

import cv2
import mediapipe as mp
import numpy as np
from mediapipe.tasks.python import BaseOptions, vision

QUI = Path(__file__).resolve().parent
LISCIO = 0.35
MODELLI = {"multi": "selfie_multiclass_256x256.tflite", "semplice": "selfie_segmenter.tflite"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--out", required=True)
    ap.add_argument("--modello", choices=MODELLI, default="multi")
    ap.add_argument("--contorno", type=int, default=9, help="spessore in px, 0 = niente")
    ap.add_argument("--colore", default="D4A63C")
    arg = ap.parse_args()
    out = Path(arg.out)

    seg = vision.ImageSegmenter.create_from_options(vision.ImageSegmenterOptions(
        base_options=BaseOptions(model_asset_path=str(QUI.parent / "strumenti" / "modelli" / MODELLI[arg.modello])),
        running_mode=vision.RunningMode.VIDEO, output_confidence_masks=True))
    classi = ["persona"] + (["capelli", "viso", "vestiti"] if arg.modello == "multi" else [])
    for c in classi + (["_contorno"] if arg.contorno else []):
        (out / c).mkdir(parents=True, exist_ok=True)
    rgb = tuple(int(arg.colore[i:i + 2], 16) for i in (0, 2, 4))

    cap = cv2.VideoCapture(arg.video)
    fps = cap.get(cv2.CAP_PROP_FPS)
    prec, k = {}, 0
    while True:
        ok, fr = cap.read()
        if not ok:
            break
        h, w = fr.shape[:2]
        cm = seg.segment_for_video(mp.Image(image_format=mp.ImageFormat.SRGB,
                                            data=cv2.cvtColor(fr, cv2.COLOR_BGR2RGB)),
                                   round(k * 1000 / fps)).confidence_masks
        if arg.modello == "multi":
            mappe = {"persona": 1.0 - cm[0].numpy_view(), "capelli": cm[1].numpy_view(),
                     "viso": cm[3].numpy_view(), "vestiti": cm[4].numpy_view()}
        else:
            mappe = {"persona": cm[0].numpy_view()}
        for nome, m in mappe.items():
            m = cv2.resize(np.squeeze(m).astype(np.float32), (w, h), interpolation=cv2.INTER_LINEAR)
            if nome in prec:
                m = (1 - LISCIO) * m + LISCIO * prec[nome]
            prec[nome] = m
            a = cv2.GaussianBlur(np.clip((m - 0.35) / 0.30, 0, 1), (0, 0), 1.5)
            cv2.imwrite(str(out / nome / f"{k:04d}.png"), (a * 255).astype(np.uint8))
            if nome == "persona" and arg.contorno:
                s = arg.contorno
                fuori = cv2.dilate(a, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * s + 1, 2 * s + 1)))
                bordo = cv2.GaussianBlur(np.clip(fuori - a, 0, 1), (0, 0), 1.2)
                rgba = np.zeros((h, w, 4), np.uint8)
                rgba[..., 0], rgba[..., 1], rgba[..., 2] = rgb[2], rgb[1], rgb[0]
                rgba[..., 3] = (bordo * 255).astype(np.uint8)
                cv2.imwrite(str(out / "_contorno" / f"{k:04d}.png"), rgba)
        k += 1

    r = f"{fps:.6f}"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", arg.video, "-framerate", r,
                    "-i", str(out / "persona" / "%04d.png"), "-filter_complex",
                    "[1:v]format=gray[m];[0:v][m]alphamerge,format=yuva444p10le[v]",
                    "-map", "[v]", "-c:v", "prores_ks", "-profile:v", "4", "-pix_fmt", "yuva444p10le",
                    str(out / "ritaglio.mov")], check=True)
    if arg.contorno:
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-framerate", r, "-i", str(out / "_contorno" / "%04d.png"),
                        "-c:v", "prores_ks", "-profile:v", "4", "-pix_fmt", "yuva444p10le",
                        str(out / "contorno.mov")], check=True)
        shutil.rmtree(out / "_contorno")
    print(f"{k} fotogrammi {w}x{h}, modello {arg.modello} -> {out}")


if __name__ == "__main__":
    main()
