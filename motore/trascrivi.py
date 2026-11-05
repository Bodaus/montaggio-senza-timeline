"""Trascrizione parola per parola con ElevenLabs Scribe, in cache.

Non si ripaga due volte: se `parole.json` c'e', non si chiama niente.

**Ogni token piu' lungo di 1,2 s si ritrascrive da solo.** Scribe a volte nasconde
un tratto intero dentro un token: una volta ne ha messi quattordici secondi in un
"quelle", e il video e' uscito con una frase monca senza nessun errore.
"""

import json
import urllib.error
import urllib.request
import uuid
from pathlib import Path

from comune import Girato, chiave_scribe, sh

ENDPOINT = "https://api.elevenlabs.io/v1/speech-to-text"
MODELLO = "scribe_v1"
LINGUA = "ita"
TOKEN_SOSPETTO = 1.2


def _multipart(campi, file):
    confine = uuid.uuid4().hex
    corpo = bytearray()
    for k, v in campi.items():
        corpo += (f'--{confine}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n'
                  f"{v}\r\n").encode()
    corpo += (f'--{confine}\r\nContent-Disposition: form-data; name="file"; '
              f'filename="{file.name}"\r\nContent-Type: audio/wav\r\n\r\n').encode()
    corpo += file.read_bytes()
    corpo += f"\r\n--{confine}--\r\n".encode()
    return bytes(corpo), f"multipart/form-data; boundary={confine}"


def scribe(file):
    chiave = chiave_scribe()
    if not chiave:
        raise SystemExit("manca la chiave ElevenLabs: scrivila nel file .env del kit, "
                         "riga ELEVENLABS_API_KEY=...")
    corpo, tipo = _multipart({"model_id": MODELLO, "language_code": LINGUA,
                              "timestamps_granularity": "word", "diarize": "false"}, file)
    req = urllib.request.Request(ENDPOINT, data=corpo, method="POST",
                                 headers={"xi-api-key": chiave, "Content-Type": tipo,
                                          "User-Agent": "montaggio-kit"})
    try:
        with urllib.request.urlopen(req, timeout=900) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        # il corpo dice quale campo non gli piace; senza si tira a indovinare
        raise SystemExit(f"Scribe: HTTP {e.code} {e.reason}\n"
                         f"{e.read().decode('utf-8', 'replace')[:800]}")


def solo_parole(ws):
    return [w for w in ws if w.get("type", "word") == "word" and w.get("text", "").strip()]


def ritrascrivi_sospetti(g, dati):
    ws = dati["words"]
    sospetti = [w for w in solo_parole(ws) if float(w["end"]) - float(w["start"]) > TOKEN_SOSPETTO]
    for w in sospetti:
        a, b = max(0.0, float(w["start"]) - 1.0), float(w["end"]) + 1.0
        pezzo = g.dir / "_pezzo.wav"
        sh(["ffmpeg", "-y", "-v", "error", "-ss", f"{a:.3f}", "-t", f"{b - a:.3f}",
            "-i", g.grezzo, "-c:a", "pcm_s16le", pezzo])
        nuove = solo_parole(scribe(pezzo)["words"])
        pezzo.unlink()
        print(f"  token lungo {w['text']!r} ({float(w['end']) - float(w['start']):.1f} s): "
              f"ritrascritto, {len(nuove)} parole")
        ws = [x for x in ws if float(x["end"]) <= a or float(x["start"]) >= b]
        ws += [dict(x, start=round(a + float(x["start"]), 3), end=round(a + float(x["end"]), 3))
               for x in nuove]
    ws.sort(key=lambda x: float(x["start"]))
    dati["words"] = ws
    return dati


def scrivi_testo(g, dati):
    """Il testo con i tempi, frase per frase: e' quello che l'agente legge per decidere i tagli."""
    righe, cur = [], []
    for w in solo_parole(dati["words"]):
        cur.append(w)
        if w["text"].rstrip().endswith((".", "?", "!")):
            righe.append(cur)
            cur = []
    if cur:
        righe.append(cur)
    testo = [f"[{float(r[0]['start']):7.2f} -> {float(r[-1]['end']):7.2f}]  "
             + " ".join(x["text"].strip() for x in r) for r in righe]
    g.parole_txt.write_text("\n".join(testo) + "\n", encoding="utf-8")


def trascrivi(nome, forza=False):
    g = Girato(nome)
    if g.parole_json.exists() and not forza:
        dati = json.loads(g.parole_json.read_text(encoding="utf-8"))
        print(f"  cache: {len(solo_parole(dati['words']))} parole, Scribe non richiamato")
    else:
        print(f"  invio {g.grezzo.stat().st_size / 1e6:.0f} MB a Scribe...")
        dati = ritrascrivi_sospetti(g, scribe(Path(g.grezzo)))
        g.parole_json.write_text(json.dumps(dati, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"  {len(solo_parole(dati['words']))} parole")
    scrivi_testo(g, dati)
    print(f"  testo con i tempi in {g.parole_txt.name}")
