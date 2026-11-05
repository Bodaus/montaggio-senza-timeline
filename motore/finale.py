"""Il video finito. L'ordine non si discute: effetti, coperture, titolo, sottotitoli.

I sottotitoli vanno per ultimi, o una grafica a piena inquadratura li copre e nessun
programma se ne lamenta. Le sovrimpressioni si spostano col loro `setpts`, altrimenti
si vede la meta' dell'animazione.

`eof_action=repeat`, mai `pass`: con `pass` l'ultimo fotogramma di una copertura non
regge fino al bordo e passa un fotogramma di volto. Un effetto invece finisce mezzo
fotogramma prima, perche' `between` include il bordo e `repeat` ripeterebbe l'ultimo:
stacco in ritardo e immagine ferma per 40 ms, in 13 effetti su 19.
"""

import comune
import musica
from comune import FPS, Girato, codifica, durata, sh


def finale(nome):
    g = Girato(nome)
    m, tl = g.montaggio(), g.timeline()
    g.pubblicare.mkdir(exist_ok=True)
    righe = sorted(g.overlays(), key=lambda o: (o.get("kind") != "effetto", o.get("kind") == "alfa"))
    cmd = ["ffmpeg", "-y", "-v", "error", "-i", g.master.name]
    for o in righe:
        cmd += ["-i", o["file"]]
    parti, ultimo = [], "0:v"
    for i, o in enumerate(righe, start=1):
        s = round(o["start_in_output"] * FPS) / FPS
        e = round((o["start_in_output"] + o["duration"]) * FPS) / FPS
        if o.get("kind") != "copertura":
            e -= 0.5 / FPS
        parti.append(f"[{i}:v]setpts=PTS-STARTPTS+{s}/TB[o{i}]")
        parti.append(f"[{ultimo}][o{i}]overlay=0:0:eof_action=repeat:"
                     f"enable='between(t,{s},{e})'[v{i}]")
        ultimo = f"v{i}"
    n = len(righe)
    if (g.dir / "apertura.mov").exists():
        n += 1
        cmd += ["-i", "apertura.mov"]
        parti.append(f"[{ultimo}][{n}:v]overlay=0:0:eof_action=pass[va]")
        ultimo = "va"
    if (g.dir / "sottotitoli.mov").exists():
        n += 1
        cmd += ["-i", "sottotitoli.mov"]
        parti.append(f"[{ultimo}][{n}:v]overlay=0:0:eof_action=pass[vout]")
    elif (g.dir / "sottotitoli.ass").exists():
        parti.append(f"[{ultimo}]subtitles=sottotitoli.ass:fontsdir=../../font[vout]")
    else:
        parti.append(f"[{ultimo}]null[vout]")

    dest = g.pubblicare / f"{tl['slug']}.mp4"
    muto = g.dir / "_senza_musica.mp4"
    cmd += ["-filter_complex", ";".join(parti), "-map", "[vout]", "-map", "0:a",
            *codifica(False), "-maxrate", "12M", "-bufsize", "24M", "-profile:v", "high",
            "-g", "50", "-keyint_min", "25", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
            "-movflags", "+faststart", muto]
    sh(cmd, cwd=g.dir)

    if (m.get("musica") or {}).get("attiva"):
        mix = musica.mix(g, m, tl)
        sh(["ffmpeg", "-y", "-v", "error", "-i", muto, "-i", mix, "-map", "0:v", "-map", "1:a",
            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-shortest",
            "-movflags", "+faststart", dest])
        muto.unlink()
    else:
        muto.replace(dest)
    print(f"  {dest.name}: {durata(dest):.2f} s, {dest.stat().st_size / 1e6:.1f} MB, "
          f"{len(righe)} sovrimpressioni")
    print(f"  in {dest.parent}")
