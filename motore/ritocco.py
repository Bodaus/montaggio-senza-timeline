"""Ritocco leggero del volto per le copertine: meno pallido, meno occhiaie.

Nato il 18/10 sulla copertina del reel S43 (C): girato la sera, stanco, luce
dall'alto e un poco verde sulla pelle. L'utente: "modificherei l'immagine in
modo da farmi sembrare meno cadavere". Solo un fotogramma fermo: sul video non
si usa (cambierebbe la persona fra un'inquadratura e l'altra).

Cosa fa, tutto in Lab e tutto dentro maschere sfumate:
- **pelle** (classi "viso" e "pelle del corpo" di selfie_multiclass): toni medi
  un poco piu' chiari, piu' rosso e piu' caldo, la grana appena ammorbidita
  (filtro bilaterale, conserva i bordi: barba e sopracciglia restano);
- **occhiaie** (mezzaluna sotto la palpebra inferiore, dai punti del face
  landmarker): schiarite e meno viola;
- **occhi**: un filo piu' chiari;
- tutta l'immagine: un poco piu' calda e piu' viva (vibranza: spinge i colori
  spenti, lascia stare quelli gia' saturi).

    python ritocco.py dentro.png fuori.png [--forza 1.0] [--confronto prima_dopo.png]

`--forza` scala tutto (0,5 = meta', 1,5 = di piu'). Gira nel venv dei volti
(`podcast/tools/.venv-volti`), come sagome.py e traccia_volti.py.
"""

import argparse
from pathlib import Path

import cv2
import mediapipe as mp
import numpy as np
from mediapipe.tasks.python import BaseOptions, vision

QUI = Path(__file__).resolve().parent
MODELLI = QUI.parent / "strumenti" / "modelli"

# palpebra inferiore, dall'angolo esterno all'interno (indici del face mesh)
PALPEBRA_SOTTO = ([33, 7, 163, 144, 145, 153, 154, 155, 133],
                  [263, 249, 390, 373, 374, 380, 381, 382, 362])
OCCHIO = ([33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246],
          [362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387, 386, 385, 384, 398])


def maschere(rgb):
    h, w = rgb.shape[:2]
    im = mp.Image(image_format=mp.ImageFormat.SRGB, data=np.ascontiguousarray(rgb))
    seg = vision.ImageSegmenter.create_from_options(vision.ImageSegmenterOptions(
        base_options=BaseOptions(model_asset_path=str(MODELLI / "selfie_multiclass_256x256.tflite")),
        output_confidence_masks=True))
    cm = seg.segment(im).confidence_masks
    m = lambda i: cv2.resize(cm[i].numpy_view().astype(np.float32), (w, h), interpolation=cv2.INTER_LINEAR)
    pelle = np.clip(m(3) + 0.6 * m(2), 0, 1)

    det = vision.FaceLandmarker.create_from_options(vision.FaceLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=str(MODELLI / "face_landmarker.task")), num_faces=1))
    r = det.detect(im)
    if not r.face_landmarks:
        raise SystemExit("nessun volto nel fotogramma")
    pt = np.array([[p.x * w, p.y * h] for p in r.face_landmarks[0]], np.float32)

    occhi = np.zeros((h, w), np.float32)
    occhiaie = np.zeros((h, w), np.float32)
    for sotto, tutto in zip(PALPEBRA_SOTTO, OCCHIO):
        cv2.fillPoly(occhi, [pt[tutto].astype(np.int32)], 1.0)
        bordo = pt[sotto]
        largo = float(np.linalg.norm(bordo[0] - bordo[-1]))
        giu = bordo + np.array([0, 0.42 * largo], np.float32)
        # la mezzaluna si stringe verso gli angoli
        centro = bordo[:, 0].mean()
        giu[:, 0] = centro + (giu[:, 0] - centro) * 0.85
        cv2.fillPoly(occhiaie, [np.vstack([bordo, giu[::-1]]).astype(np.int32)], 1.0)
        s = 0.14 * largo
    occhi = cv2.GaussianBlur(occhi, (0, 0), 3)
    occhiaie = cv2.GaussianBlur(occhiaie, (0, 0), s) * (1 - occhi)
    pelle = cv2.GaussianBlur(pelle, (0, 0), 4) * (1 - occhi)
    return pelle, occhiaie, occhi


def ritocca(bgr, forza=1.0):
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    pelle, occhiaie, occhi = maschere(rgb)
    f = forza

    # grana della pelle, appena (il bilaterale tiene i bordi)
    liscio = cv2.bilateralFilter(bgr, 9, 28, 7)
    a = (0.35 * f * pelle)[..., None]
    bgr = (bgr * (1 - a) + liscio * a).astype(np.float32)

    lab = cv2.cvtColor(np.clip(bgr, 0, 255).astype(np.uint8), cv2.COLOR_BGR2LAB).astype(np.float32)
    L, A, B = lab[..., 0], lab[..., 1], lab[..., 2]
    medi = np.sin(np.pi * np.clip(L / 255, 0, 1))          # 0 ai neri e ai bianchi
    # la barba e i peli scuri stanno nella maschera "viso": si toccano solo i
    # toni della pelle (la prima prova faceva la barba rossiccia)
    chiara = np.clip((L - 70) / 50, 0, 1)
    pelle = pelle * chiara
    L += f * (12 * pelle + 14 * occhiaie * chiara) * medi + f * 6 * occhi * medi
    A += f * (2.5 * pelle + 1.0 * occhiaie)                 # un filo piu' rosa, meno grigio-verde
    B += f * (1.5 * pelle + 2.5 * occhiaie + 0.8)           # appena piu' caldo; occhiaie meno viola
    lab = np.clip(np.dstack([L, A, B]), 0, 255).astype(np.uint8)
    bgr = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)

    # vibranza: i colori spenti si accendono di piu' di quelli gia' saturi
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV).astype(np.float32)
    s = hsv[..., 1] / 255
    hsv[..., 1] = np.clip(255 * (s + f * 0.08 * s * (1 - s) * 2), 0, 255)
    return cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("dentro")
    ap.add_argument("fuori")
    ap.add_argument("--forza", type=float, default=1.0)
    ap.add_argument("--confronto", help="png col prima e il dopo affiancati")
    a = ap.parse_args()
    prima = cv2.imread(a.dentro)
    dopo = ritocca(prima, a.forza)
    cv2.imwrite(a.fuori, dopo)
    if a.confronto:
        cv2.imwrite(a.confronto, np.hstack([prima, np.full((prima.shape[0], 16, 3), 40, np.uint8), dopo]))
    d = np.abs(dopo.astype(int) - prima.astype(int)).mean()
    print(f"ritocco forza {a.forza}: scarto medio {d:.1f}/255")


if __name__ == "__main__":
    main()
