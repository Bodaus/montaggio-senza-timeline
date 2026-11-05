"""Dal file del telefono a una sorgente che si comporta bene.

- immagine verticale 1440x2560 a 25 fotogrammi fissi: i telefoni girano a frequenza
  variabile, e su una frequenza variabile tagli e tracciamenti scivolano;
- `voce_grezza.wav`: serve solo a decidere i tagli, resta com'e';
- `voce.wav`: la voce che si sente, passata da una catena standard;
- `inquadratura.json`: dove stanno volto e testa, misurati, se MediaPipe c'e'.

La catena standard sostituisce i plugin a pagamento. Sono correzioni piccole e
sicure: via i rimbombi sotto i 90 Hz, un po' meno "scatola" a 250 Hz, un po' piu'
presenza a 3,2 kHz, un filo di riduzione del rumore, una compressione leggera. Il
volume finale lo decide il taglio, blocco per blocco.
"""

import json

from comune import FPS, SRC_H, SRC_W, STRUMENTI, Girato, durata, sh

CATENA = ("highpass=f=90,"
          "equalizer=f=250:t=q:w=1.0:g=-3,"
          "equalizer=f=3200:t=q:w=1.2:g=2.5,"
          "afftdn=nr=8:nf=-45:tn=1,"
          "acompressor=threshold=-22dB:ratio=2.5:attack=8:release=120:makeup=2dB")


def voce(g):
    sh(["ffmpeg", "-y", "-v", "error", "-i", g.video, "-vn", "-ac", "1", "-ar", "16000",
        "-c:a", "pcm_s16le", g.grezzo])
    sh(["ffmpeg", "-y", "-v", "error", "-i", g.video, "-vn", "-ac", "1", "-ar", "48000",
        "-af", CATENA, "-c:a", "pcm_f32le", g.voce])


def _hdr(sorgente):
    """Gli iPhone girano in HDR: senza conversione i colori escono slavati."""
    r = sh(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
            "stream=color_transfer", "-of", "csv=p=0", sorgente])
    return r.stdout.strip().split(",")[0] in ("arib-std-b67", "smpte2084")


TONI = ("zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,tonemap=hable:desat=0,"
        "zscale=t=bt709:m=bt709:r=tv,")


def normalizza(g, sorgente):
    toni = TONI if _hdr(sorgente) else ""
    if toni:
        print("  video HDR: lo converto")
    vf = (f"{toni}scale={SRC_W}:{SRC_H}:force_original_aspect_ratio=increase:flags=lanczos,"
          f"crop={SRC_W}:{SRC_H},fps={FPS},format=yuv420p")
    sh(["ffmpeg", "-y", "-v", "error", "-i", sorgente, "-vf", vf, "-fps_mode", "cfr",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "17",
        "-c:a", "pcm_s16le", "-ar", "48000", "-ac", "2", g.video])


def _cima(fr, seg, mp, alto, basso):
    """La cima dei capelli: il volto finisce alla fronte, la sagoma no."""
    import cv2
    import numpy as np
    h, w = fr.shape[:2]
    m = seg.segment(mp.Image(image_format=mp.ImageFormat.SRGB,
                             data=cv2.cvtColor(fr, cv2.COLOR_BGR2RGB))).confidence_masks
    persona = cv2.resize(1.0 - np.squeeze(m[0].numpy_view()), (w, h)) > 0.5
    righe = np.where(persona.any(axis=1))[0]
    return float(righe[0]) / h if len(righe) else alto - 0.3 * (basso - alto)


def inquadra(g):
    """Volto e cima della testa su dodici fotogrammi. Senza MediaPipe restano i valori medi."""
    try:
        import cv2
        import mediapipe as mp
        import numpy as np
        from mediapipe.tasks.python import BaseOptions, vision
    except ImportError:
        print("  inquadratura: MediaPipe assente, uso il centro del quadro")
        return
    modello = STRUMENTI / "modelli" / "face_landmarker.task"
    if not modello.exists():
        print("  inquadratura: modello dei volti assente, uso il centro del quadro")
        return
    det = vision.FaceLandmarker.create_from_options(vision.FaceLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=str(modello)), num_faces=1))
    seg = vision.ImageSegmenter.create_from_options(vision.ImageSegmenterOptions(
        base_options=BaseOptions(model_asset_path=str(STRUMENTI / "modelli" / "selfie_multiclass_256x256.tflite")),
        output_confidence_masks=True))
    d = durata(g.video)
    xs, ys = [], []
    cap = cv2.VideoCapture(str(g.video))
    for i in range(12):
        cap.set(cv2.CAP_PROP_POS_MSEC, 1000 * d * (i + 0.5) / 12)
        ok, fr = cap.read()
        if not ok:
            continue
        r = det.detect(mp.Image(image_format=mp.ImageFormat.SRGB,
                                data=cv2.cvtColor(fr, cv2.COLOR_BGR2RGB)))
        if r.face_landmarks:
            L = r.face_landmarks[0]
            xs.append(float(np.mean([p.x for p in L])))
            ys.append(_cima(fr, seg, mp, min(p.y for p in L), max(p.y for p in L)))
    cap.release()
    if not xs:
        print("  inquadratura: nessun volto trovato, uso il centro del quadro")
        return
    q = {"volto_x": round(float(np.median(xs)), 3), "testa_y": round(float(np.median(ys)), 3)}
    g.inquadratura_json.write_text(json.dumps(q, indent=2), encoding="utf-8")
    print(f"  inquadratura: volto a {q['volto_x']:.2f} della larghezza, "
          f"testa a {q['testa_y']:.2f} dell'altezza")


def prepara(nome, sorgente):
    g = Girato(nome)
    print("  immagine...")
    normalizza(g, sorgente)
    print("  voce...")
    voce(g)
    inquadra(g)
    print(f"  pronto: {durata(g.video):.1f} s")
