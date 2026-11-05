"""La copertina e' il fotogramma 0, e il JPG da caricare e' quello stesso fotogramma.

Instagram, TikTok e LinkedIn, se non carichi niente, prendono il primo fotogramma.
Quindi la copertina giusta deve stare li', senza allungare il video:

- occhiello e titolo restano sopra la frase d'aggancio per circa due secondi, al
  posto dei sottotitoli;
- solo il fotogramma 0 porta il volto in cui sorridi di piu', cercato con MediaPipe.
  Dura 40 ms e cade prima che tu apra bocca: non si vede, e la piattaforma prende
  quello.

In montaggio.json:
    "copertina": {
      "occhiello": "IL TEMA IN MAIUSCOLO",
      "titolo": [[{"testo": "Prima riga"}], [{"testo": "seconda in accento.", "accento": true}]],
      "sorgente_t": 33.5,     facoltativo: il secondo del girato, per scegliere a mano
      "ritocco": 0.8          facoltativo: pelle meno grigia, occhiaie piu' chiare
    }
"""

import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw

import comune
import ponte_remotion
import sorrisi
import sottotitoli as subs
import taglio
import verifiche
from comune import H, MOTORE, SAFE_BOTTOM, SAFE_RIGHT, SAFE_TOP, W, Girato, hex_rgb, marchio, sh

SFUMA = 0.2
DURATA_TITOLO = 2.0
GRIGLIA = (240, 1680)     # la griglia del profilo mostra solo questa fascia, in 3:4


def _inquadratura(g, m):
    s = m["blocchi"][0]
    z = s.get("zoom", "medio")
    z = taglio.ZOOM.get(z, z) if isinstance(z, str) else z
    return taglio.ritaglio(z, g.inquadratura(), s.get("centrato", False),
                           s.get("testa", taglio.TESTA_USCITA))


def _fotogramma(g, crop, vgrado, t, dest, scala=None):
    w, h, x, y = crop
    vf = f"crop={w}:{h}:{x}:{y},scale={W}:{H}:flags=lanczos,{vgrado}"
    if scala:
        vf += f",scale={scala}"
    sh(["ffmpeg", "-y", "-v", "error", "-ss", f"{t:.3f}", "-i", g.video, "-frames:v", "1",
        "-vf", vf, dest])


def _foglio(g, crop, vgrado, cand, scelto):
    """Le alternative affiancate, col secondo da mettere in `sorgente_t`."""
    acc = hex_rgb(marchio()["accento"])
    pezzi = []
    for i, c in enumerate(cand):
        f = g.verifica / f"_c{i}.png"
        _fotogramma(g, crop, vgrado, c["t"], f, "270:480")
        im = Image.open(f).convert("RGB")
        im.load()
        f.unlink()
        d = ImageDraw.Draw(im)
        d.rectangle((0, 440, 270, 480), fill=(0, 0, 0))
        d.text((8, 452), f"{'SCELTO ' if c['t'] == scelto else ''}{c['t']:.2f}  ({c['punti']:+.2f})",
               fill=acc if c["t"] == scelto else (230, 230, 230))
        pezzi.append(im)
    t = Image.new("RGB", (274 * len(pezzi), 480), (40, 40, 40))
    for i, im in enumerate(pezzi):
        t.paste(im, (274 * i, 0))
    t.save(g.verifica / "copertina_candidati.jpg", quality=88)


def _prova(g, im):
    zona = im.copy()
    d = ImageDraw.Draw(zona, "RGBA")
    d.rectangle((0, 0, W, SAFE_TOP), fill=(255, 0, 0, 80))
    d.rectangle((0, SAFE_BOTTOM, W, H), fill=(255, 0, 0, 80))
    d.rectangle((SAFE_RIGHT, 1100, W, SAFE_BOTTOM), fill=(255, 0, 0, 60))
    griglia = im.crop((0, GRIGLIA[0], W, GRIGLIA[1]))
    w = 360
    t = Image.new("RGB", (w * 3 + 40, 640), (40, 40, 40))
    t.paste(im.resize((w, 640)), (0, 0))
    t.paste(zona.resize((w, 640)), (w + 20, 0))
    gr = griglia.resize((w, int(w * 4 / 3)))
    t.paste(gr, (2 * w + 40, (640 - gr.height) // 2))
    t.save(g.verifica / "copertina_prova.png")


def copertina(nome):
    g = Girato(nome)
    m, tl = g.montaggio(), g.timeline()
    g.verifica.mkdir(exist_ok=True)
    g.pubblicare.mkdir(exist_ok=True)
    c = m.get("copertina") or {}
    titolo = [r for r in c.get("titolo", []) if any(p.get("testo") for p in r)]
    vgrado = tl.get("grado", "eq=contrast=1.03")
    crop = _inquadratura(g, m)

    # il volto
    if c.get("sorgente_t") is not None:
        scelto = float(c["sorgente_t"])
    else:
        cand = sorrisi.candidati(g, m, crop)
        if cand:
            scelto = cand[0]["t"]
            _foglio(g, crop, vgrado, cand, scelto)
        else:
            scelto = m["blocchi"][0]["inizio"]

    if not ponte_remotion.disponibile():
        f = g.pubblicare / f"{tl['slug']}-copertina.jpg"
        _fotogramma(g, crop, vgrado, scelto, f)
        subs.rendi_ass(g)
        (g.dir / "apertura.mov").unlink(missing_ok=True)
        (g.dir / "sottotitoli.mov").unlink(missing_ok=True)
        print("  Remotion assente: copertina senza titolo")
        return

    (g.dir / "sottotitoli.ass").unlink(missing_ok=True)
    if not titolo:
        subs.rendi_pillola(g)
        (g.dir / "apertura.mov").unlink(missing_ok=True)
        print("  copertina senza titolo: `copertina` vuota in montaggio.json")
        return

    gruppi = subs.gruppi(g, m, tl)
    fine = next((x["a"] for x in gruppi if x["a"] >= DURATA_TITOLO), None)
    if fine is None:
        fine = min(DURATA_TITOLO, tl["totale"])

    pubblico = ponte_remotion.PROGETTO / "public"
    pubblico.mkdir(exist_ok=True)
    png = pubblico / "apertura.png"
    _fotogramma(g, crop, vgrado, scelto, png)
    if c.get("ritocco"):
        r = subprocess.run([sys.executable, str(MOTORE / "ritocco.py"), str(png), str(png),
                            "--forza", str(c["ritocco"]),
                            "--confronto", str(g.verifica / "copertina_ritocco.png")],
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        if r.returncode:
            raise SystemExit(r.stdout + r.stderr)

    props = dict(occhiello=c.get("occhiello", ""), titolo=titolo, dur=round(fine, 3),
                 immagine="apertura.png", sfuma=SFUMA)

    # solo il testo: dentro l'area sicura, perche' sta nel video, e nella griglia 3:4
    prova = g.dir / "_titolo.png"
    ponte_remotion.fermo("apertura", dict(props, soloTesto=True), prova)
    alfa = np.array(Image.open(prova).convert("RGBA"))[:, :, 3] > verifiche.SOGLIA_ALFA
    prova.unlink()
    fuori = verifiche.tocca("titolo", alfa, verifiche.zone())
    ys, _ = np.nonzero(alfa)
    if len(ys) and (ys.min() < GRIGLIA[0] or ys.max() > GRIGLIA[1]):
        fuori.append(f"esce dal ritaglio 3:4: y {ys.min()}-{ys.max()}")
    if fuori:
        raise SystemExit("titolo fuori dalle aree:\n  " + "\n  ".join(fuori))

    ponte_remotion.alfa("apertura", props, g.dir / "apertura.mov")
    subs.rendi_pillola(g, da=fine)

    piena = g.dir / "_apertura0.png"
    ponte_remotion.fermo("apertura", props, piena)
    im = Image.open(piena).convert("RGB")
    im.load()
    piena.unlink()
    im.save(g.pubblicare / f"{tl['slug']}-copertina.jpg", quality=93, subsampling=0)
    _prova(g, im)
    print(f"  volto a {scelto:.2f} s del girato, titolo fino a {fine:.2f} s: dentro le aree")
