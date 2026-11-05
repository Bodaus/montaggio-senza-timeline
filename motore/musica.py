"""Una base musicale scritta sul montaggio, e il mix con la voce.

La base si scrive qui, nota per nota: nessuna licenza da gestire, e segue il video
invece di girarci sotto. Quattro accordi, piano elettrico, basso, batteria leggera:

- finche' dura il primo blocco: solo il tappeto;
- dal secondo blocco: entra tutto il ritmo;
- sull'ultimo blocco: via la batteria;
- sulla parola del timbro: un battito di silenzio con un colpo basso;
- in fondo: l'ultimo accordo che si spegne.

Sotto la voce si abbassa da sola, con una salita lenta, perche' il passaggio non si
senta. Con FluidSynth e la banca GeneralUser GS le note le suonano strumenti
campionati; senza, una sintesi semplice. Gli strumenti veri riempiono le frequenze
della voce, quindi vengono scavati attorno ai 2,5 kHz e abbassati di piu' sotto il
parlato: la prima prova era "troppo ingombrante".

    "musica": {"attiva": true, "bpm": 100}     in montaggio.json
"""

import hashlib
import shutil
import struct
import subprocess

import numpy as np
from scipy.signal import butter, lfilter, sosfiltfilt

from comune import STRUMENTI, sh

SR = 48000
BANCA = STRUMENTI / "campioni" / "GeneralUser-GS.sf2"
CACHE = STRUMENTI / "cache-note"
TICK = 960

L_EP, L_PAD, L_BASSO, L_CASSA, L_RIM, L_HAT = -14, -20, -13, -11, -26, -30
SOTTO_VOCE_DB = 8.0
TUTTA_DB = -6.0
CAMPIONI_DB = -2.0
TAGLIO_HZ = 500
SOTTO_VOCE_MEDIE_DB = 14.0
CONCA_DB = -4.0

ACCORDI = [([53, 57, 60, 64], 41), ([57, 60, 64, 67], 45), ([53, 57, 60, 62], 38), ([53, 57, 58, 62], 34)]


def db(x):
    return 10 ** (x / 20)


def nota(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def midi(f):
    return int(round(69 + 12 * np.log2(f / 440)))


def cerca_fluidsynth():
    trovati = sorted((STRUMENTI / "fluidsynth").rglob("fluidsynth.exe")) if (STRUMENTI / "fluidsynth").is_dir() else []
    return str(trovati[-1]) if trovati else shutil.which("fluidsynth")


def _vlq(n):
    out = [n & 0x7F]
    while n > 127:
        n >>= 7
        out.append((n & 0x7F) | 0x80)
    return bytes(reversed(out))


def _file_midi(programma, n, durata, velocita, canale, coda):
    ev = [(0, bytes([0xC0 | canale, programma])), (0, bytes([0x90 | canale, n, velocita])),
          (int(durata * TICK), bytes([0x80 | canale, n, 0])),
          (int(coda * TICK), bytes([0xB0 | canale, 110, 0])), (0, b"\xff\x2f\x00")]
    tr = b"".join(_vlq(dt) + e for dt, e in ev)
    return b"MThd" + struct.pack(">IHHH", 6, 0, 1, 480) + b"MTrk" + struct.pack(">I", len(tr)) + tr


class Strumenti:
    def __init__(self):
        self.fluid = cerca_fluidsynth() if BANCA.exists() else None
        self.veri = bool(self.fluid)

    def vera(self, programma, n, durata, velocita=80, batteria=False, coda=1.5):
        canale = 9 if batteria else 0
        chiave = f"{programma}-{n}-{durata:.3f}-{velocita}-{canale}-{coda:.2f}"
        wav = CACHE / (hashlib.md5(chiave.encode()).hexdigest()[:16] + ".wav")
        if not wav.exists():
            CACHE.mkdir(parents=True, exist_ok=True)
            mid = wav.with_suffix(".mid")
            mid.write_bytes(_file_midi(programma, n, durata, velocita, canale, coda))
            subprocess.run([self.fluid, "-ni", "-q", "-C", "0", "-g", "0.6", "-r", str(SR),
                            "-F", str(wav), str(BANCA), str(mid)], check=True, capture_output=True)
            mid.unlink()
        p = subprocess.run(["ffmpeg", "-v", "error", "-i", str(wav), "-ac", "1", "-f", "f32le", "-"],
                           capture_output=True, check=True).stdout
        return np.frombuffer(p, "<f4").astype(np.float64)[: int((durata + coda) * SR)]

    def ep(self, f, d):
        if self.veri:
            return self.vera(4, midi(f), d, 72, coda=1.0)
        t = np.arange(int(d * SR)) / SR
        env = (1 - np.exp(-t / 0.006)) * np.exp(-t / 0.95)
        s = (np.sin(2 * np.pi * f * t) + 0.35 * np.sin(4 * np.pi * f * t) * np.exp(-t / 0.3)
             + 0.10 * np.sin(6 * np.pi * f * t) * np.exp(-t / 0.12))
        return s * env * (1 + 0.07 * np.sin(2 * np.pi * 4.8 * t))

    def pad(self, f, d):
        if self.veri:
            return self.vera(89, midi(f), d, 60, coda=0.8)
        t = np.arange(int(d * SR)) / SR
        env = np.minimum(1, t / 0.5) * np.minimum(1, (d - t) / 0.6).clip(0)
        return sum(np.sin(2 * np.pi * f * (1 + x) * t + p)
                   for x, p in ((-0.003, 0), (0, 1.3), (0.004, 2.1))) / 3 * env

    def cassa(self):
        if self.veri:
            return self.vera(0, 36, 0.2, 90, batteria=True, coda=0.5)
        t = np.arange(int(0.32 * SR)) / SR
        f = 46 + 75 * np.exp(-t / 0.028)
        return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.16)

    def basso(self, f, d):
        if self.veri:
            return self.vera(33, midi(f), d, 85, coda=0.4)
        t = np.arange(int(d * SR)) / SR
        return (np.sin(2 * np.pi * f * t) + 0.2 * np.sin(4 * np.pi * f * t)) * (1 - np.exp(-t / 0.004)) * np.exp(-t / 0.4)

    def rim(self):
        return self.vera(0, 37, 0.1, 70, batteria=True, coda=0.4) if self.veri else rumore(0.12, 0.045, 1)

    def hat(self):
        return self.vera(0, 42, 0.05, 60, batteria=True, coda=0.3) if self.veri else rumore(0.05, 0.016, 2)


def rumore(d, tau, acuto):
    t = np.arange(int(d * SR)) / SR
    n = np.random.default_rng(7).standard_normal(len(t))
    for _ in range(acuto):
        n = np.diff(n, prepend=0)
    n /= np.abs(n).max()
    return n * np.exp(-t / tau)


def fruscio():
    """Un passaggio d'aria, sintetizzato: sotto gli effetti, senza licenze."""
    t = np.arange(int(0.42 * SR)) / SR
    n = np.random.default_rng(11).standard_normal(len(t))
    env = np.sin(np.pi * t / t[-1]) ** 2
    return sosfiltfilt(butter(2, (500, 5000), "band", fs=SR, output="sos"), n) * env


def colpo():
    """Il colpo basso del timbro."""
    t = np.arange(int(0.7 * SR)) / SR
    f = 42 + 90 * np.exp(-t / 0.03)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.22)


def metti(buf, x, t, livello):
    i = int(round(t * SR))
    if i >= len(buf) or i + len(x) <= 0:
        return
    a, b = max(0, i), min(len(buf), i + len(x))
    buf[a:b] += x[a - i:b - i] * db(livello) / max(1e-9, np.abs(x).max())


def base(st, durata, entra, cala, colpi, B):
    n = int(durata * SR) + SR
    ep_, pad_, ritmo = np.zeros(n), np.zeros(n), np.zeros(n)

    def battiti(da, a):
        k0, k1 = int(np.ceil((da - entra) / B)), int(np.floor((a - entra) / B))
        return [(k, entra + k * B) for k in range(k0, k1 + 1)]

    accordo = lambda k: ACCORDI[(k // 4) % 4]

    def tappeto(da, a):
        bb = battiti(da, a)
        for k, t in bb:
            if k % 4 == 0 or t == bb[0][1]:
                for m in accordo(k)[0]:
                    metti(pad_, st.pad(nota(m), min(a, t + 4 * B) - t + 0.5), t, L_PAD - 6)

    def piano(da, a, stacchi=(0, 1.5)):
        for k, t in battiti(da, a):
            if k % 4 == 0:
                for s in stacchi:
                    if t + s * B < a:
                        for j, m in enumerate(accordo(k)[0]):
                            metti(ep_, st.ep(nota(m), 1.6), t + s * B + 0.011 * j, L_EP - 6)

    def batteria(da, a):
        for k, t in battiti(da, a):
            if k % 4 in (0, 2):
                metti(ritmo, st.cassa(), t, L_CASSA)
                metti(ritmo, st.basso(nota(accordo(k)[1]), 0.9), t, L_BASSO)
            if k % 4 in (1, 3):
                metti(ritmo, st.rim(), t, L_RIM)
            if t + B / 2 < a:
                metti(ritmo, st.hat(), t + B / 2, L_HAT)

    fine_voce = durata - 0.4
    tappeto(0, entra + 0.1)
    piano(entra, cala + 0.2)
    batteria(entra, cala)
    piano(cala, fine_voce, stacchi=(0, 1.5, 3))
    for k, t in battiti(cala, fine_voce):
        if k % 4 in (0, 2):
            metti(ritmo, st.basso(nota(accordo(k)[1]), 0.9), t, L_BASSO - 3)
    tappeto(cala, durata)
    x = (ep_ + pad_ + ritmo)[:int(durata * SR)]
    t = np.arange(len(x)) / SR
    for c in colpi:                  # un battito di silenzio sul timbro
        x[(t > c - 0.02) & (t < c + B - 0.05)] = 0
    k = int(0.8 * SR)
    x[-k:] *= np.linspace(1, 0, k)
    return x


def leggi(path, ch=2):
    p = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-ac", str(ch), "-ar", str(SR),
                        "-f", "f32le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(p, "<f4").reshape(-1, ch).astype(np.float64)


def abbassa(mus, voce, quanto=SOTTO_VOCE_DB):
    """Musica giu' dove c'e' voce: attacco 150 ms, rilascio 700 ms."""
    v = np.pad(voce[:len(mus), 0], (0, max(0, len(mus) - len(voce))))
    win = int(0.02 * SR)
    rms = np.sqrt(np.convolve(v * v, np.ones(win) / win, "same"))
    parla = (rms > db(-42)).astype(float)
    gu = np.empty_like(parla)
    acc = 0.0
    ka, kr = np.exp(-1 / (0.15 * SR)), np.exp(-1 / (0.7 * SR))
    for i in range(0, len(parla), 48):
        x = parla[i]
        k = ka if x > acc else kr
        acc = (1 - k ** 48) * x + k ** 48 * acc
        gu[i:i + 48] = acc
    gu = db(-quanto * gu)
    return mus * (gu[:, None] if mus.ndim == 2 else gu)


def fai_spazio(mus, voce, rif):
    """La base campionata: stesso volume della sintetica, conca a 2,5 kHz, due bande sotto la voce."""
    mus = mus * np.sqrt(np.mean(rif ** 2) / max(1e-12, np.mean(mus[:, 0] ** 2))) * db(CAMPIONI_DB)
    banda = sosfiltfilt(butter(2, (1600, 4000), "band", fs=SR, output="sos"), mus, axis=0)
    mus = mus + (db(CONCA_DB) - 1) * banda
    bassi = sosfiltfilt(butter(4, TAGLIO_HZ, "low", fs=SR, output="sos"), mus, axis=0)
    return abbassa(bassi, voce) + abbassa(mus - bassi, voce, SOTTO_VOCE_MEDIE_DB)


def mix(g, m, tl):
    lav = g.dir / "_musica"
    lav.mkdir(exist_ok=True)
    voce = leggi(g.master)
    durata = len(voce) / SR
    bb = tl["blocks"]
    entra = bb[1]["out_start"] if len(bb) > 1 else min(2.0, durata / 4)
    cala = bb[-1]["out_start"] if len(bb) > 2 else durata * 0.8
    B = 60.0 / float((m.get("musica") or {}).get("bpm", 100))
    righe = g.overlays()
    colpi = [o["t_colpo"] for o in righe if o.get("t_colpo") is not None]
    st = Strumenti()
    x = base(st, durata, entra, cala, colpi, B)
    d = int(0.008 * SR)
    mus = np.stack([x, np.concatenate([np.zeros(d), x[:-d]])], 1)
    a = np.exp(-2 * np.pi * 5000 / SR)
    mus = lfilter([1 - a], [1, -a], mus, axis=0)
    if st.veri:
        sint = Strumenti()
        sint.veri = False
        mus = fai_spazio(mus, voce, base(sint, durata, entra, cala, colpi, B))
    else:
        mus = abbassa(mus, voce)
    mus = mus * db(TUTTA_DB)

    sfx = np.zeros(len(mus))
    for o in righe:
        if o.get("kind") in ("effetto", "alfa") and o.get("t_colpo") is None:
            metti(sfx, fruscio(), o["start_in_output"], -30)
    for c in colpi:
        metti(sfx, colpo(), c, -16)

    n = min(len(voce), len(mus))
    uscita = voce[:n] + mus[:n] + sfx[:n, None]
    grezzo = lav / "mix.f32"
    grezzo.write_bytes(uscita.astype("<f4").tobytes())
    wav = lav / "mix.wav"
    # -3 dBFS: con musica e colpi bassi l'AAC risale di ~1,4 dB
    sh(["ffmpeg", "-y", "-v", "error", "-f", "f32le", "-ar", SR, "-ac", 2, "-i", grezzo,
        "-af", "volume=1.3dB,alimiter=limit=0.708:attack=5:release=50:level=disabled",
        "-c:a", "pcm_s24le", wav])
    grezzo.unlink()
    print(f"  musica {'campionata' if st.veri else 'sintetica'}, {60 / B:.0f} bpm, "
          f"entra a {entra:.1f} s, cala a {cala:.1f} s")
    return wav
