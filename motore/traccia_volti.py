"""Traccia i volti di un video, fotogramma per fotogramma, in un JSON.

    python traccia_volti.py VIDEO [--out volti.json] [--da S] [--a S] [--volti N]

MediaPipe Face Landmarker in modo VIDEO (`modelli/face_landmarker.task`). Per
ogni fotogramma: i volti con centro e riquadro in pixel del video, e un'identita'
tenuta per vicinanza fra un fotogramma e l'altro (un volto che sparisce e
riappare lontano prende un'identita' nuova: va riconosciuto a mano).

Il video conviene prepararlo prima nel formato della composizione (vedi
README): cosi' le coordinate sono gia' quelle della scena.

Il tempo si conta dal numero del fotogramma: la posizione in ms che restituisce
OpenCV non sempre cresce, e MediaPipe in modo VIDEO vuole tempi crescenti.
Riconosce bene i volti in primo piano (selfie, interviste); la folla lontana o di
spalle no (misurato sulle clip di Wave by Vento 2026: volti solo nei selfie).
"""

import argparse
import json
from pathlib import Path

import cv2
import mediapipe as mp
from mediapipe.tasks.python import BaseOptions, vision

QUI = Path(__file__).resolve().parent


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--out")
    ap.add_argument("--da", type=float, default=0.0)
    ap.add_argument("--a", type=float, default=1e9)
    ap.add_argument("--volti", type=int, default=4)
    arg = ap.parse_args()

    det = vision.FaceLandmarker.create_from_options(vision.FaceLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=str(QUI.parent / "strumenti" / "modelli" / "face_landmarker.task")),
        running_mode=vision.RunningMode.VIDEO, num_faces=arg.volti,
        min_face_detection_confidence=0.4, min_tracking_confidence=0.4))
    cap = cv2.VideoCapture(arg.video)
    fps = cap.get(cv2.CAP_PROP_FPS)
    n0 = round(arg.da * fps)
    cap.set(cv2.CAP_PROP_POS_FRAMES, n0)
    fot, prec, nuovo, k = [], {}, 0, 0
    w = h = 0
    while True:
        t = (n0 + k) / fps
        ok, fr = cap.read()
        if not ok or t > arg.a:
            break
        h, w = fr.shape[:2]
        r = det.detect_for_video(mp.Image(image_format=mp.ImageFormat.SRGB,
                                          data=cv2.cvtColor(fr, cv2.COLOR_BGR2RGB)), round(t * 1000))
        volti = []
        for L in r.face_landmarks:
            xs = [p.x * w for p in L]
            ys = [p.y * h for p in L]
            b = [min(xs), min(ys), max(xs), max(ys)]
            c = [(b[0] + b[2]) / 2, (b[1] + b[3]) / 2]
            presi = [v["id"] for v in volti]
            vicino = min(((vid, pc) for vid, pc in prec.items() if vid not in presi),
                         key=lambda kv: (kv[1][0] - c[0]) ** 2 + (kv[1][1] - c[1]) ** 2, default=None)
            if vicino and ((vicino[1][0] - c[0]) ** 2 + (vicino[1][1] - c[1]) ** 2) ** 0.5 < (b[2] - b[0]) * 0.6:
                vid = vicino[0]
            else:
                vid, nuovo = nuovo, nuovo + 1
            volti.append(dict(id=vid, c=[round(c[0], 1), round(c[1], 1)], box=[round(x, 1) for x in b]))
        prec = {v["id"]: v["c"] for v in volti}
        fot.append(dict(t=round(t - arg.da, 4), volti=volti))
        k += 1

    out = Path(arg.out) if arg.out else Path(arg.video).with_suffix(".volti.json")
    out.write_text(json.dumps(dict(video=str(arg.video), da=arg.da, fps=fps, w=w, h=h, fotogrammi=fot)))
    piste = {}
    for f in fot:
        for v in f["volti"]:
            piste.setdefault(v["id"], []).append(f["t"])
    print(f"{len(fot)} fotogrammi a {fps:.2f} fps -> {out}")
    for vid, ts in piste.items():
        print(f"  volto {vid}: {len(ts)} fotogrammi, da {min(ts):.2f} a {max(ts):.2f} s")


if __name__ == "__main__":
    main()
