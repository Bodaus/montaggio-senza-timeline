import React from 'react';
import {fitText} from '@remotion/layout-utils';

import {BRAND} from './brand';

/**
 * Occhiello e titolo della copertina, con lo sfumato che li regge.
 *
 * Lo usa `Apertura.tsx`, che rende copertina il fotogramma 0 del video. Il JPG
 * da caricare a mano si ricava da quello stesso fotogramma: la copertina e' una
 * sola, caricata o presa in automatico dalla piattaforma.
 */

export type RigaTitolo = {testo: string; accento?: boolean}[];

const X = BRAND.safeLeft;
// Fino a `safeRight` e non al margine destro: il titolo sta sotto y 1100, dove a
// destra c'e' la colonna dei pulsanti. Col titolo del terzo video non si vedeva,
// perche' era piu' stretto; "la mappa sbagliata." ci finiva sotto di 37 px.
const LARGA = BRAND.safeRight - BRAND.safeLeft;
const INTERLINEA = 1.04;

export const BloccoTitolo: React.FC<{
  occhiello: string;
  titolo: RigaTitolo[];
  fondo: number; // dove finisce l'ultima riga del titolo
  maxCorpo: number;
  inizioSfumato: number; // da qui in giu' lo sfumato scende verso il fondo
  soloTesto?: boolean;
}> = ({occhiello, titolo, fondo, maxCorpo, inizioSfumato, soloTesto = false}) => {
  // Un corpo solo per tutte le righe, deciso dalla piu' larga: righe di corpi
  // diversi in un titolo di due righe si leggono come due titoli.
  const corpo = Math.min(
    maxCorpo,
    ...titolo.map(
      (r) =>
        fitText({
          text: r.map((p) => p.testo).join(''),
          withinWidth: LARGA,
          fontFamily: BRAND.famDisplay,
          fontWeight: String(BRAND.pesoTitolo),
        }).fontSize,
    ),
  );
  const alto = fondo - titolo.length * corpo * INTERLINEA;
  const altoOcchiello = alto - 62;
  // lo sfumato e' pieno al 93% quando comincia l'occhiello e del tutto pieno
  // un poco piu' sotto: il testo non sta mai sopra la maglia gialla
  // lo sfumato parte sempre almeno 220 px sopra l'occhiello: con un titolo corto a
  // corpo pieno l'occhiello cadeva sul suo inizio e il passaggio diventava una riga
  const inizio = Math.min(inizioSfumato, altoOcchiello - 220);
  const spanPieno = Math.max(1, BRAND.h - inizio);
  const quasi = Math.max(0, Math.min(100, ((altoOcchiello - 10 - inizio) / spanPieno) * 100));
  const pieno = Math.min(100, quasi + 10);

  return (
    <>
      {soloTesto ? null : (
        <div
          style={{
            position: 'absolute',
            left: 0,
            right: 0,
            top: inizio,
            bottom: 0,
            background: `linear-gradient(to bottom, rgba(0,0,0,0) 0%, rgba(0,0,0,0.93) ${quasi.toFixed(1)}%, ${BRAND.bg} ${pieno.toFixed(1)}%)`,
          }}
        />
      )}
      <div
        style={{
          position: 'absolute',
          left: X,
          top: altoOcchiello,
          fontFamily: `"${BRAND.famMono}", sans-serif`,
          fontWeight: 600,
          fontSize: 36,
          letterSpacing: '0.08em',
          color: BRAND.dim,
        }}
      >
        {occhiello}
      </div>
      <div
        style={{
          position: 'absolute',
          left: X,
          top: alto,
          width: LARGA,
          fontFamily: `"${BRAND.famDisplay}", sans-serif`,
          fontWeight: BRAND.pesoTitolo,
          fontSize: corpo,
          lineHeight: INTERLINEA,
          color: BRAND.text,
          whiteSpace: 'nowrap',
        }}
      >
        {titolo.map((riga, i) => (
          <div key={i}>
            {riga.map((p, j) => (
              <span key={j} style={{color: p.accento ? BRAND.accent : BRAND.text}}>
                {p.testo}
              </span>
            ))}
          </div>
        ))}
      </div>
    </>
  );
};
