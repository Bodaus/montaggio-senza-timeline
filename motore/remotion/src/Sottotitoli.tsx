import React, {useMemo} from 'react';
import {interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {measureText} from '@remotion/layout-utils';

import {BRAND} from './brand';

/**
 * Sottotitoli a gruppi di due o tre parole, fermi, con un segnale che scorre.
 *
 * La via di mezzo fra la parola singola e la frase intera. Il gruppo resta
 * immobile al pixel per tutto il tempo in cui e' in campo; a muoversi e' solo il
 * segnale che dice quale parola sta suonando.
 *
 * **Perche' qui e non in ASS.** In libass ingrandire una parola dentro la riga
 * ricalcola la riga, e le vicine si spostano: la variante "scatto" ballava per
 * questo. Qui l'ingrandimento e' una `transform`, che non tocca l'impaginazione.
 * E le posizioni delle parole si misurano con lo stesso motore che le disegna,
 * quindi un evidenziatore puo' scorrere dall'una all'altra e cadere esatto.
 *
 * Le regole restano quelle di `subs.py`: le parole forti (numeri e quelle
 * scelte a mano) sono in accento sempre; il segnale della parola in voce e' un
 * altro segno, cosi' i due significati non si confondono.
 */

export type Parola = {testo: string; t: number; forte: boolean};
export type Gruppo = {a: number; b: number; parole: Parola[]};
export type Stile = 'barra' | 'pillola' | 'luce';
export type SottotitoliProps = {dur: number; stile: Stile; gruppi: Gruppo[]};

const FAM = BRAND.famDisplay;
const PESO = 700;
// **Centrato sull'area sicura, non sul fotogramma.** A destra la colonna dei
// pulsanti toglie 200 px: centrato sul fotogramma il gruppo avrebbe 680 px e il
// corpo verrebbe piccolo. Centrato fra 60 e 880 ne ha 820, e lo spostamento di
// 70 px verso sinistra non si nota.
const CENTRO = (BRAND.safeLeft + BRAND.safeRight) / 2;
const PAD_EM = 0.2; // quanto la pillola esce dalla parola, per lato (era 0,16: stretta)
// 22 px per lato: la pillola esce di PAD_EM dalla parola e l'ombra ancora un
// poco. Con 18 l'ombra sull'ultima parola del gruppo piu' largo ("si trova
// guardando", video 1) toccava la colonna dei pulsanti di un pixel.
const DISPONIBILE = BRAND.safeRight - BRAND.safeLeft - 2 * 30;
const MAX_CORPO = 100;
const INTERLINEA = 1.18;
// la riga finisce qui; sotto resta posto per la barra, e sotto la barra
// comincia la didascalia della piattaforma
const FONDO_RIGA = BRAND.safeBottom - 26;

// **La pillola sta sulle lettere, non sulla riga.** Misurato col font vero, in
// em dall'alto della riga (interlinea 1,18, Instrument Sans Bold): ascendenti e
// maiuscole da 0,23, linea di base a 0,95, gambe di g/p/q/y fino a 1,165. Una
// pillola centrata sulla riga lascia vuoto sopra e taglia le gambe: questa copre
// da 0,15 sopra le ascendenti a 0,13 sotto le gambe.
const PILLOLA_SU = 0.08;
const PILLOLA_GIU = 1.295;
// Il fondo della pillola, con la sua ombra, resta dentro l'area sicura: e' lei
// a scendere piu' in basso di tutto, quindi la riga si impagina da qui.
const FONDO_PILLOLA = BRAND.safeBottom - 24;
// in em; piu' largo del margine della pillola, se no la pillola tocca la
// parola accanto
const SPAZIO = 0.42;

const larga = (testo: string, corpo: number) =>
  measureText({text: testo, fontFamily: FAM, fontSize: corpo, fontWeight: String(PESO)})
    .width;

/** Dove sta ogni parola del gruppo, misurata col motore che la disegna. */
const impagina = (parole: Parola[], corpo: number) => {
  const ws = parole.map((p) => larga(p.testo, corpo));
  const xs: number[] = [];
  let x = 0;
  ws.forEach((w, i) => {
    xs.push(x);
    x += w + (i < ws.length - 1 ? SPAZIO * corpo : 0);
  });
  return {xs, ws, totale: x};
};

const contorno = (r: number) => {
  const passi = 16;
  const ombre: string[] = [];
  for (let i = 0; i < passi; i++) {
    const a = (i / passi) * Math.PI * 2;
    ombre.push(
      `${(Math.cos(a) * r).toFixed(1)}px ${(Math.sin(a) * r).toFixed(1)}px 0 ${BRAND.bg}`,
    );
  }
  ombre.push(`0 6px 18px rgba(0,0,0,0.55)`);
  return ombre.join(', ');
};

export const Sottotitoli: React.FC<SottotitoliProps> = ({stile, gruppi}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const t = frame / fps;

  // Un corpo solo per tutto il video, scelto sul gruppo piu' largo: un corpo
  // per gruppo farebbe cambiare dimensione al testo a ogni cambio, e si vede.
  const corpo = useMemo(() => {
    let peggiore = 1;
    for (const g of gruppi) peggiore = Math.max(peggiore, impagina(g.parole, 100).totale);
    return Math.min(MAX_CORPO, Math.floor((100 * DISPONIBILE) / peggiore));
  }, [gruppi]);

  const contornoTesto = useMemo(() => contorno(Math.max(3, corpo * 0.045)), [corpo]);

  const g = gruppi.find((x) => t >= x.a && t < x.b);
  if (!g) return null;

  const {xs, ws, totale} = impagina(g.parole, corpo);
  const sinistra = CENTRO - totale / 2;
  const alto = Math.min(FONDO_RIGA - corpo * INTERLINEA, FONDO_PILLOLA - corpo * PILLOLA_GIU);

  let k = 0;
  g.parole.forEach((p, i) => {
    if (t >= p.t) k = i;
  });

  // il segnale scivola dalla parola di prima a questa
  const inizioK = Math.round(g.parole[k].t * fps);
  const p =
    k === 0
      ? 1
      : spring({frame: frame - inizioK, fps, config: {damping: 200, stiffness: 300, mass: 0.45}});
  const xPrima = k === 0 ? xs[0] : xs[k - 1];
  const wPrima = k === 0 ? ws[0] : ws[k - 1];
  const xSegno = xPrima + (xs[k] - xPrima) * p;
  const wSegno = wPrima + (ws[k] - wPrima) * p;

  // il gruppo entra in tre fotogrammi, senza spostarsi
  const entrata = interpolate(t, [g.a, g.a + 0.12], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const pop =
    stile === 'luce'
      ? spring({frame: frame - inizioK, fps, config: {damping: 14, stiffness: 220, mass: 0.5}})
      : 1;

  // **La parola scura sta solo dove c'e' la pillola.** Prima la parola in voce
  // cambiava colore tutta insieme appena la pillola era arrivata a meta' strada:
  // mentre si allargava verso una parola lunga, la parte ancora fuori era scura
  // sul fondo scuro e spariva — "servirebbe…" senza "ro". Adesso le parole sono
  // chiare sotto, e sopra la pillola ne porta una copia scura ritagliata dalla
  // sua forma: a ogni fotogramma le lettere sono scure esattamente dove c'e'
  // ocra, anche a meta' corsa.
  const pillolaX = sinistra + xSegno - PAD_EM * corpo;
  const pillolaY = alto + corpo * PILLOLA_SU;

  return (
    <div style={{position: 'absolute', inset: 0, opacity: entrata}}>
      {g.parole.map((parola, i) => {
        const corrente = i === k;
        let colore = parola.forte ? BRAND.accent : BRAND.text;
        const opacita = 1;
        let trasforma = 'none';
        if (stile === 'luce') {
          // Spente col colore, non con l'opacita': abbassando l'opacita' si
          // spegneva anche il bordo scuro, e sulla maglia gialla diventava fango.
          // Anche le forti restano grigie finche' non arrivano: l'ocra si
          // accende quando la parola suona.
          if (i > k) colore = BRAND.dim;
          if (corrente) {
            const s = 1.1 - 0.1 * pop;
            trasforma = `translateY(${(-(1 - pop) * corpo * 0.08).toFixed(2)}px) scale(${s.toFixed(4)})`;
          }
        }
        return (
          <span
            key={i}
            style={{
              position: 'absolute',
              left: sinistra + xs[i],
              top: alto,
              fontFamily: `"${FAM}", sans-serif`,
              fontWeight: PESO,
              fontSize: corpo,
              lineHeight: INTERLINEA,
              whiteSpace: 'nowrap',
              color: colore,
              opacity: opacita,
              textShadow: contornoTesto,
              transform: trasforma,
              transformOrigin: '50% 85%',
            }}
          >
            {parola.testo}
          </span>
        );
      })}

      {stile === 'pillola' ? (
        <div
          style={{
            position: 'absolute',
            left: pillolaX,
            top: pillolaY,
            width: wSegno + 2 * PAD_EM * corpo,
            height: corpo * (PILLOLA_GIU - PILLOLA_SU),
            borderRadius: corpo * 0.26,
            background: BRAND.accent,
            boxShadow: `0 6px 18px rgba(0,0,0,0.45)`,
            overflow: 'hidden',
          }}
        >
          {g.parole.map((parola, i) => (
            <span
              key={i}
              style={{
                position: 'absolute',
                left: sinistra + xs[i] - pillolaX,
                top: alto - pillolaY,
                fontFamily: `"${FAM}", sans-serif`,
                fontWeight: PESO,
                fontSize: corpo,
                lineHeight: INTERLINEA,
                whiteSpace: 'nowrap',
                color: BRAND.on_accent,
              }}
            >
              {parola.testo}
            </span>
          ))}
        </div>
      ) : null}

      {stile === 'barra' ? (
        <div
          style={{
            position: 'absolute',
            left: sinistra + xSegno,
            top: alto + corpo * INTERLINEA + 6,
            width: wSegno,
            height: 9,
            borderRadius: 5,
            background: BRAND.accent,
            // sulla maglia gialla l'ocra da solo sparisce: il filo scuro
            // intorno lo stacca da qualunque fondo
            boxShadow: `0 0 0 3px ${BRAND.bg}`,
          }}
        />
      ) : null}
    </div>
  );
};
