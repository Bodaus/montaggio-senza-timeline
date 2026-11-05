"""Dal girato e da `montaggio.json` a un master senza grafiche.

Ogni blocco e' estratto a pezzi e i pezzi si uniscono senza ricodificare: gli
intermedi sono PCM in MOV, mai AAC in MP4, perche' il concat perde il priming
dell'AAC e il parlato finisce 45 ms dietro la sua immagine.

**Il taglio lo decide il suono, non la trascrizione.** Scribe dice quale frase e'
quale. Dove comincia e dove finisce il suono lo dice l'inviluppo: fidarsi di Scribe
e' andata male in tutte e due le direzioni, mangiando l'attacco di "quattro" e
lasciando dentro 620 ms di vuoto. Le pause sopra GAP_MAX si tolgono: erano un aiuto
al taglio, non recitazione.

Campi di un blocco in montaggio.json:
    id, inizio, fine (secondi del girato; `fine` e' nominale, viene agganciato al suono)
    tipo       "volto" o "grafica": sui blocchi grafica si legge, vanno coperti
    zoom       "largo", "medio", "stretto" o un numero
    pause      true: niente tagli dentro il blocco
    centrato   true: ritaglio al centro del quadro invece che sul volto
    prima      secondo da cui parte il quadro, prima di parlare (un'entrata)
    dopo       secondo in cui finisce il quadro, dopo aver parlato (un'uscita)
    fermo      secondi di immagine ferma in coda: nasconde l'occhio che torna al copione
"""

import json
import shutil
import subprocess
import wave

import numpy as np

import parole
from comune import FPS, FRAME, H, SRC_H, SRC_W, W, Girato, codifica, fotogrammi, sh

ZOOM = {"largo": 1.08, "medio": 1.18, "stretto": 1.30}
TESTA_USCITA = 0.17       # dove cade la cima della testa nell'uscita, in frazione d'altezza

PAD_TESTA = 0.050
PAD_CODA = 0.100          # a meta' frase
PAD_CODA_FINE = 0.220     # dopo . ? !: una frase finita vuole aria
GAP_MAX = 0.35            # sopra, il vuoto si toglie
MIN_RUN = 0.30            # sotto, il pezzo si fonde col precedente: mai buttato
SCARTO_INTERNO = 1.045    # il salto dentro un blocco si nasconde con uno scarto di scala
RELEASE = 0.060           # il decadimento dell'ultima sillaba

ISOLA_UNISCI = 120        # ms: una consonante occlusiva chiude per circa tanto
ISOLA_FINE = 600          # ms: oltre mezzo secondo la frase e' finita
ISOLA_MIN = 250           # ms: sotto questa durata un'isola non fa una parola
GUARDA_INDIETRO = 0.35    # quanto si risale per trovare un attacco vero

VOLUME = -14.5            # LUFS, un guadagno per blocco
SOFFITTO = 0.841          # -1,5 dBFS: l'AAC risale di qualche decimo


def leggi_grezzo(path):
    with wave.open(str(path)) as w:
        x = np.frombuffer(w.readframes(w.getnframes()), "<i2").astype(np.float64) / 32768.0
    return x


def inviluppo(path):
    """RMS a passo 1 ms."""
    x = leggi_grezzo(path)
    hop, win = 16, 160
    n = (len(x) - win) // hop
    fr = np.lib.stride_tricks.sliding_window_view(x, win)[np.arange(n) * hop]
    return np.sqrt((fr ** 2).mean(axis=1))


def soglia_parlato(env):
    """La soglia va misurata a ogni girato: e' assoluta rispetto a quella sorgente.

    A meta' strada, in scala logaritmica, fra il fondo della stanza e il parlato. Sui
    girati in cui era stata scelta a mano (0,002 e 0,003) questo conto cade fra 0,002
    e 0,0025. Il fondo ha un minimo perche' un file ripulito ha il silenzio digitale,
    e la meta' strada verso lo zero non vuol dire niente. Si puo' forzare con "soglia"
    in montaggio.json: se gli attacchi prendono un respiro si alza, se le code
    spariscono si abbassa.
    """
    fondo = max(float(np.percentile(env, 30)), 0.0001)
    voce = float(np.percentile(env, 92))
    return float(np.clip(np.sqrt(fondo * voce), 0.002, 0.03))


def misura_guadagno(g, ident, pezzi):
    """Un guadagno per blocco, misurato sul solo parlato che ci finisce."""
    tmp = g.dir / "_volume"
    if tmp.exists():
        shutil.rmtree(tmp)
    tmp.mkdir()
    righe = []
    for i, (a, d) in enumerate(pezzi):
        out = tmp / f"{i:03d}.wav"
        sh(["ffmpeg", "-y", "-v", "error", "-ss", f"{a:.4f}", "-i", g.voce, "-t", f"{d:.4f}",
            "-af", "pan=stereo|c0=c0|c1=c0", "-c:a", "pcm_s24le", out])
        righe.append(f"file '{out.name}'\n")
    elenco = tmp / "elenco.txt"
    elenco.write_text("".join(righe), encoding="utf-8")
    tutto = tmp / "tutto.wav"
    sh(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", elenco,
        "-c", "copy", tutto])
    p = subprocess.run(["ffmpeg", "-v", "info", "-i", str(tutto), "-af",
                        "loudnorm=print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    blob = p.stderr[p.stderr.rindex("{"):]
    stats = json.loads(blob[:blob.index("}") + 1])
    shutil.rmtree(tmp)
    ingresso = float(stats["input_i"])
    if not np.isfinite(ingresso):
        return 0.0
    return round(min(24.0, VOLUME - ingresso), 2)


def _isole(seg, soglia):
    forti = np.flatnonzero(seg > soglia)
    if not len(forti):
        return forti, []
    rotture = np.flatnonzero(np.diff(forti) > ISOLA_UNISCI)
    inizi = np.concatenate(([0], rotture + 1))
    fini = np.concatenate((rotture, [len(forti) - 1]))
    return forti, list(zip(inizi, fini))


def tronconi(env, t0, t1, soglia, sentite=()):
    """I tronconi di parlato dentro [t0, t1], letti sull'inviluppo.

    Un'isola breve e isolata e' un tonfo in cucina, a meno che Scribe non ci abbia
    sentito una parola: un "Ora" staccato di 0,9 s e' stato scartato cosi', senza
    nessun errore.
    """
    lo, hi = max(0, int(t0 * 1000)), min(len(env), int(t1 * 1000))
    seg = env[lo:hi]
    if not len(seg):
        return []
    forti, isole = _isole(seg, soglia)
    if not isole:
        return []
    tieni = []
    for k, (a, b) in enumerate(isole):
        breve = (forti[b] - forti[a]) < ISOLA_MIN
        prima = forti[a] - forti[isole[k - 1][1]] if k else 10 ** 9
        dopo = forti[isole[k + 1][0]] - forti[b] if k + 1 < len(isole) else 10 ** 9
        if breve and min(prima, dopo) > ISOLA_FINE:
            ta, tb = (lo + int(forti[a])) / 1000.0, (lo + int(forti[b])) / 1000.0
            if not any(ta - 0.05 <= (s + e) / 2 <= tb + 0.05 for s, e in sentite):
                continue
        tieni.append((a, b))
    if not tieni:
        return []
    runs = [list(tieni[0])]
    for a, b in tieni[1:]:
        if forti[a] - forti[runs[-1][1]] <= GAP_MAX * 1000:
            runs[-1][1] = b
        else:
            runs.append([a, b])
    return [((lo + int(forti[a])) / 1000.0, (lo + int(forti[b])) / 1000.0 + RELEASE)
            for a, b in runs]


def spezza(ws, inizio, fine, env, soglia):
    """(inizio, fine, chiude_frase) dei pezzi di un blocco, senza i vuoti."""
    dentro = [w for w in ws if float(w["start"]) >= inizio - 0.02 and float(w["end"]) <= fine + 0.02]
    t0 = min(inizio, float(dentro[0]["start"])) if dentro else inizio
    grezzi = tronconi(env, t0 - GUARDA_INDIETRO, fine, soglia,
                      [(float(w["start"]), float(w["end"])) for w in dentro])
    # via la coda della presa precedente, entrata solo perche' si guarda indietro
    grezzi = [r for r in grezzi if r[1] > t0]
    # il "guardare indietro" non entra mai nella parola che precede
    prima = [float(w["end"]) for w in ws if float(w["start"]) < t0 - 0.01]
    if prima:
        grezzi = [r for r in grezzi if r[0] >= max(prima) - 0.01]
    grezzi = grezzi or [(t0, fine)]

    def fine_frase(t):
        visti = [w for w in dentro if float(w["start"]) <= t + 0.05]
        return visti[-1]["text"].rstrip().endswith((".", "?", "!")) if visti else True

    uniti = []
    for a, b in grezzi:
        eos = fine_frase(b)
        if uniti and b - a < MIN_RUN:
            uniti[-1] = (uniti[-1][0], b, eos)      # tieni la pausa, tieni la parola
        else:
            uniti.append((a, b, eos))
    while len(uniti) > 1 and uniti[0][1] - uniti[0][0] < MIN_RUN:
        uniti[1] = (uniti[0][0], uniti[1][1], uniti[1][2])
        uniti.pop(0)
    return uniti


def ritaglio(zoom, q, centrato=False, testa=TESTA_USCITA):
    w, h = round(SRC_W / zoom), round(SRC_H / zoom)
    w -= w % 2
    h -= h % 2
    if centrato:
        x, y = (SRC_W - w) / 2, (SRC_H - h) / 2
    else:
        x = q["volto_x"] * SRC_W - w / 2
        y = q["testa_y"] * SRC_H - testa * h
    x = max(0, min(SRC_W - w, round(x)))
    y = max(0, min(SRC_H - h, round(y)))
    return w, h, x - x % 2, y - y % 2


def grado(g, m):
    """Un filo di contrasto, e la luminosita' solo se e' davvero fuori.

    Si misura, non si guarda: a occhio il grezzo sembra sempre piu' inciso di quello
    che e'. Un volto sotto YAVG 72 esce "poco luminoso" per chiunque lo guardi.
    """
    if m.get("colore"):
        return m["colore"]
    r = sh(["ffmpeg", "-v", "info", "-i", g.video, "-vf",
            "fps=1,scale=270:480,signalstats,metadata=print:key=lavfi.signalstats.YAVG:file=-",
            "-f", "null", "-"])
    ys = [float(x.split("=")[1]) for x in r.stdout.splitlines() if "YAVG" in x]
    y = float(np.median(ys)) if ys else 100.0
    gamma = 1.0
    if y < 72:          # per ffmpeg uscita = ingresso ^ (1/gamma)
        gamma = float(np.clip(np.log(y / 255) / np.log(84 / 255), 1.0, 1.4))
    elif y > 150:
        gamma = float(np.clip(np.log(y / 255) / np.log(130 / 255), 0.8, 1.0))
    print(f"  luminosita' media {y:.0f}, gamma {gamma:.2f}")
    return f"eq=contrast=1.03:saturation=1.04:gamma={gamma:.3f}"


def estrai(g, c, guadagno, vgrado, q, out):
    d = c["dur"]
    w, h, x, y = ritaglio(c["zoom"], q, c["centrato"], c["testa"])
    c["crop"] = [w, h, x, y]
    vf = f"crop={w}:{h}:{x}:{y},scale={W}:{H}:flags=lanczos,{vgrado},format=yuv420p"
    if c["fermo"] > 0:
        # fps= prima di tpad regge tutto: senza, tpad non allunga niente e non lo dice
        vf += (f",trim=end={d - c['fermo']:.4f},setpts=PTS-STARTPTS,fps={FPS},"
               f"tpad=stop_mode=clone:stop_duration={c['fermo']:.4f}")
    # la voce e' mono: si duplica PRIMA del guadagno, se no ffmpeg la abbassa di 3 dB
    # dopo il limitatore
    af = (f"pan=stereo|c0=c0|c1=c0,volume={guadagno}dB,"
          f"alimiter=limit={SOFFITTO}:attack=5:release=50:level=disabled,"
          f"afade=t=in:st=0:d=0.03,afade=t=out:st={d - 0.03:.3f}:d=0.03")
    sh(["ffmpeg", "-y", "-v", "error",
        "-ss", f"{c['a_start']:.4f}", "-i", g.video,
        "-ss", f"{c['a_start']:.4f}", "-i", g.voce,
        "-t", f"{d:.4f}", "-map", "0:v:0", "-map", "1:a:0",
        "-vf", vf, "-af", af, "-r", str(FPS), "-fps_mode", "cfr",
        *codifica(True), "-c:a", "pcm_s16le", "-ar", "48000", "-ac", "2", out])


def taglia(nome):
    g = Girato(nome)
    m = g.montaggio()
    ws = parole.carica(g, m)
    env = inviluppo(g.grezzo)
    soglia = float(m.get("soglia") or soglia_parlato(env))
    q = g.inquadratura()
    vgrado = grado(g, m)
    print(f"  soglia del parlato {soglia:.4f}")

    def pezzi_di(s):
        rs = spezza(ws, s["inizio"], s["fine"], env, soglia)
        if s.get("pause"):
            return [(rs[0][0], rs[-1][1], rs[-1][2])]
        return rs

    if g.clips.exists():
        shutil.rmtree(g.clips)
    g.clips.mkdir()
    clips, blocks, t = [], [], 0.0
    for s in m["blocchi"]:
        pezzi = pezzi_di(s)
        spans = [(a - PAD_TESTA, (b + (PAD_CODA_FINE if e else PAD_CODA)) - (a - PAD_TESTA))
                 for a, b, e in pezzi]
        guadagno = misura_guadagno(g, s["id"], spans)
        z = s.get("zoom", "medio")
        z = ZOOM.get(z, z) if isinstance(z, str) else z
        inizio_blocco, tolti = t, 0.0
        for i, (a, b, eos) in enumerate(pezzi):
            coda = PAD_CODA_FINE if eos else PAD_CODA
            if i:
                tolti += a - pezzi[i - 1][1] - coda - PAD_TESTA
            a0 = a - PAD_TESTA
            if i == 0 and s.get("prima") is not None:
                a0 = s["prima"]
            a1 = b + coda
            if i == len(pezzi) - 1 and s.get("dopo") is not None:
                a1 = max(a1, s["dopo"])
            a0 = max(0.0, a0)
            d = round((a1 - a0) / FRAME) * FRAME
            scarto = SCARTO_INTERNO if i % 2 else 1.0
            fermo = s.get("fermo", 0.0) if i == len(pezzi) - 1 else 0.0
            c = dict(id=f"{s['id']}{chr(97 + i) if len(pezzi) > 1 else ''}",
                     parent=s["id"], zoom=round(z * scarto, 4),
                     centrato=bool(s.get("centrato")),
                     testa=s.get("testa", TESTA_USCITA),
                     a_start=round(a0, 4), dur=d, fermo=round(min(fermo, coda), 4))
            f = g.clips / f"{c['id']}.mov"
            estrai(g, c, guadagno, vgrado, q, f)
            c["real_dur"] = fotogrammi(f) / FPS
            c["out_start"] = round(t, 3)
            c["file"] = f.name
            t += c["real_dur"]
            clips.append(c)
        blocks.append(dict(id=s["id"], tipo=s.get("tipo", "volto"), guadagno_db=guadagno,
                           out_start=round(inizio_blocco, 3),
                           dur=round(t - inizio_blocco, 3), pezzi=len(pezzi)))
        nota = f"  via {tolti:.2f} s di pause" if tolti > 0.05 else ""
        print(f"  {s['id']:<5} {t - inizio_blocco:5.2f} s  {len(pezzi)} pezzi  "
              f"{guadagno:+6.2f} dB{nota}")

    elenco = g.clips / "elenco.txt"
    elenco.write_text("".join(f"file '{c['file']}'\n" for c in clips), encoding="utf-8")
    sh(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", elenco,
        "-c", "copy", g.master])
    g.timeline_json.write_text(json.dumps(
        dict(titolo=m["titolo"], slug=m["slug"], fps=FPS, size=[W, H], soglia=soglia,
             grado=vgrado, totale=round(t, 3), blocks=blocks, clips=clips),
        indent=1, ensure_ascii=False),
        encoding="utf-8")
    print(f"  master: {t:.2f} s")
