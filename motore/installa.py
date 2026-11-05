"""Installa quello che manca e dice se tutto funziona, a semafori.

    BASE       Python, FFmpeg, trascrizione: tagli e sottotitoli semplici
    GRAFICHE   Node e Remotion: sottotitoli a pillola, coperture, copertina
    EFFETTI    MediaPipe, EffectCraft, strumenti campionati

Se il terzo resta rosso si lavora con i primi due: il video esce lo stesso.
"""

import hashlib
import os
import platform
import shutil
import subprocess
import sys
import tarfile
import urllib.request
import zipfile
from pathlib import Path

from comune import FONT, KIT, STRUMENTI

EC_VERSIONE = "0.21.1"
EC_BASE = f"https://github.com/storytold/effectcraft/releases/download/v{EC_VERSIONE}/"
MODELLI = {
    "face_landmarker.task": "https://storage.googleapis.com/mediapipe-models/face_landmarker/"
                            "face_landmarker/float16/1/face_landmarker.task",
    "selfie_multiclass_256x256.tflite": "https://storage.googleapis.com/mediapipe-models/image_segmenter/"
                                        "selfie_multiclass_256x256/float32/latest/selfie_multiclass_256x256.tflite",
}
BANCA_URL = "https://raw.githubusercontent.com/mrbumpy409/GeneralUser-GS/main/GeneralUser-GS.sf2"
BANCA_SHA = "9575028c7a1f589f5770fccc8cff2734566af40cd26ed836944e9a5152688cfe"
FLUID_WIN = ("https://github.com/FluidSynth/fluidsynth/releases/download/v2.6.2/"
             "fluidsynth-v2.6.2-win10-x64-cpp11.zip")


def _scarica(url, dest):
    dest.parent.mkdir(parents=True, exist_ok=True)
    print(f"  scarico {dest.name}...")
    req = urllib.request.Request(url, headers={"User-Agent": "montaggio-kit"})
    with urllib.request.urlopen(req, timeout=600) as r, open(dest, "wb") as f:
        shutil.copyfileobj(r, f)


def _sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for pezzo in iter(lambda: f.read(1 << 20), b""):
            h.update(pezzo)
    return h.hexdigest()


def _sistema():
    s, m = platform.system(), platform.machine().lower()
    if s == "Windows":
        return f"effectcraft-{EC_VERSIONE}-windows-{'arm64' if 'arm' in m else 'x64'}-portable.zip"
    if s == "Darwin":
        return f"effectcraft-cli-{EC_VERSIONE}-macos-universal.zip"
    return f"effectcraft-{EC_VERSIONE}-linux-{'aarch64' if 'arm' in m or 'aarch' in m else 'x86_64'}.tar.gz"


def _effectcraft():
    import effetti
    if effetti.cerca_effectcraft():
        return
    nome = _sistema()
    tmp = STRUMENTI / "_scarico"
    arch, somme = tmp / nome, tmp / "SHA256SUMS.txt"
    _scarica(EC_BASE + nome, arch)
    _scarica(EC_BASE + "SHA256SUMS.txt", somme)
    attesa = next((r.split()[0] for r in somme.read_text().splitlines() if r.strip().endswith(nome)), None)
    if attesa != _sha(arch):
        shutil.rmtree(tmp)
        raise SystemExit(f"{nome}: impronta diversa da quella pubblicata, non lo installo")
    dest = STRUMENTI / "effectcraft" / f"{EC_VERSIONE}"
    dest.mkdir(parents=True, exist_ok=True)
    if nome.endswith(".zip"):
        with zipfile.ZipFile(arch) as z:
            z.extractall(dest)
    else:
        with tarfile.open(arch) as t:
            t.extractall(dest, filter="data")
    shutil.rmtree(tmp)
    for f in dest.rglob("effectcraft-cli"):
        f.chmod(0o755)


def _modelli():
    for nome, url in MODELLI.items():
        f = STRUMENTI / "modelli" / nome
        if not f.exists():
            _scarica(url, f)


def _musica():
    import musica
    if not musica.BANCA.exists():
        _scarica(BANCA_URL, musica.BANCA)
        if _sha(musica.BANCA) != BANCA_SHA:
            musica.BANCA.unlink()
            raise SystemExit("GeneralUser GS: impronta inattesa, non la tengo")
    if musica.cerca_fluidsynth():
        return
    if platform.system() == "Windows":
        z = STRUMENTI / "_fluid.zip"
        _scarica(FLUID_WIN, z)
        with zipfile.ZipFile(z) as a:
            a.extractall(STRUMENTI / "fluidsynth")
        z.unlink()
    else:
        print("  FluidSynth manca: su Mac `brew install fluid-synth`, su Linux dal gestore "
              "di pacchetti. Senza, la musica esce con la sintesi semplice.")


def _font():
    """Chromium, libass ed EffectCraft cercano i caratteri per nome: vanno installati."""
    file = sorted(FONT.glob("*.ttf"))
    s = platform.system()
    if s == "Windows":
        dest = Path(os.environ["LOCALAPPDATA"]) / "Microsoft" / "Windows" / "Fonts"
        dest.mkdir(parents=True, exist_ok=True)
        import winreg
        chiave = winreg.CreateKey(winreg.HKEY_CURRENT_USER,
                                  r"Software\Microsoft\Windows NT\CurrentVersion\Fonts")
        for f in file:
            d = dest / f.name
            if not d.exists():
                shutil.copy(f, d)
            winreg.SetValueEx(chiave, f"{f.stem} (TrueType)", 0, winreg.REG_SZ, str(d))
    else:
        dest = Path.home() / ("Library/Fonts" if s == "Darwin" else ".local/share/fonts/kit-montaggio")
        dest.mkdir(parents=True, exist_ok=True)
        for f in file:
            shutil.copy(f, dest / f.name)
        if s == "Linux" and shutil.which("fc-cache"):
            subprocess.run(["fc-cache", "-f"], capture_output=True)


def _remotion():
    import ponte_remotion as P
    npm = "npm.cmd" if os.name == "nt" else "npm"
    if not shutil.which(npm):
        print("  Node manca: installalo da nodejs.org (versione LTS), poi rilancia")
        return
    if not (P.PROGETTO / "node_modules" / "remotion").is_dir():
        print("  installo Remotion (un paio di minuti)...")
        subprocess.run([npm, "ci", "--no-audit", "--no-fund"], cwd=P.PROGETTO, check=True)
    print("  scarico il browser di Remotion, se manca...")
    subprocess.run([P.NPX, "remotion", "browser", "ensure"], cwd=P.PROGETTO, check=False,
                   capture_output=True)


def installa():
    if not (KIT / ".venv").exists():
        print("Ambiente Python...")
        subprocess.run([sys.executable, "-m", "venv", str(KIT / ".venv")], check=True)
        py = KIT / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        subprocess.run([str(py), "-m", "pip", "install", "-q", "-r", str(KIT / "requirements.txt")],
                       check=True)
        sys.exit(subprocess.run([str(py), str(KIT / "kit.py"), "installa"]).returncode)
    print("Caratteri...")
    _font()
    print("Modelli dei volti...")
    _modelli()
    print("Grafiche...")
    _remotion()
    print("Effetti...")
    _effectcraft()
    print("Musica...")
    _musica()
    env = KIT / ".env"
    if not env.exists():
        env.write_text("ELEVENLABS_API_KEY=\n", encoding="utf-8")
        print("Creato .env: incolla la tua chiave ElevenLabs dopo l'uguale.")
    print()
    controlla()


def _ok(cond, testo, consiglio=""):
    print(f"   [{'ok' if cond else ' X'}] {testo}" + ("" if cond or not consiglio else f": {consiglio}"))
    return bool(cond)


def controlla():
    from comune import chiave_scribe
    base = grafiche = extra = True

    print("\nBASE, per tagliare e sottotitolare")
    base &= _ok(sys.version_info >= (3, 10), f"Python {sys.version.split()[0]}", "serve la 3.10 o piu'")
    ff = shutil.which("ffmpeg")
    base &= _ok(ff and shutil.which("ffprobe"), "FFmpeg",
                "Windows: winget install Gyan.FFmpeg; Mac: brew install ffmpeg")
    if ff:
        r = subprocess.run(["ffmpeg", "-hide_banner", "-filters"], capture_output=True, text=True,
                           encoding="utf-8", errors="replace").stdout
        base &= _ok(" subtitles " in r, "FFmpeg con i sottotitoli (libass)", "serve una versione completa")
        c = subprocess.run(["ffmpeg", "-hide_banner", "-encoders"], capture_output=True, text=True,
                           encoding="utf-8", errors="replace").stdout
        base &= _ok("prores_ks" in c, "FFmpeg con ProRes", "serve una versione completa")
    try:
        import numpy  # noqa: F401
        import PIL  # noqa: F401
        import scipy  # noqa: F401
        n = True
    except ImportError:
        n = False
    base &= _ok(n, "librerie Python", "lancia python kit.py installa")
    base &= _ok(chiave_scribe(), "chiave ElevenLabs", "scrivila nel file .env")

    print("\nGRAFICHE, per pillola, coperture e copertina")
    import ponte_remotion as P
    grafiche &= _ok(shutil.which("npx.cmd" if os.name == "nt" else "npx"), "Node", "installalo da nodejs.org")
    grafiche &= _ok(P.disponibile(), "Remotion", "lancia python kit.py installa")

    print("\nEFFETTI E MUSICA")
    try:
        import cv2  # noqa: F401
        import mediapipe  # noqa: F401
        n = True
    except ImportError:
        n = False
    extra &= _ok(n, "MediaPipe")
    extra &= _ok((STRUMENTI / "modelli" / "face_landmarker.task").exists()
                 and (STRUMENTI / "modelli" / "selfie_multiclass_256x256.tflite").exists(), "modelli dei volti")
    import effetti
    ec = effetti.cerca_effectcraft()
    extra &= _ok(ec, f"EffectCraft {EC_VERSIONE}", "lancia python kit.py installa")
    import musica
    _ok(musica.cerca_fluidsynth() and musica.BANCA.exists(), "strumenti campionati (facoltativi)",
        "senza, la musica usa la sintesi semplice")

    print("\n" + "\n".join((f"{'VERDE' if v else 'ROSSO'}  {n}"
                            for n, v in (("base", base), ("grafiche", grafiche), ("effetti", extra)))))
    return 0 if base else 1
