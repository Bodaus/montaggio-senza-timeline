import React from 'react';
import {Composition} from 'remotion';

import {BRAND} from './brand';
import {caratteriPronti} from './caratteri';
import {Apertura} from './Apertura';
import {Copertura} from './Copertura';
import {Sottotitoli} from './Sottotitoli';
import {Timbro} from './Timbro';

/**
 * Le composizioni del kit. Durata e battute non stanno qui: arrivano come
 * proprieta' dal motore Python. I valori qui sotto servono solo allo studio
 * (`npm run studio`). L'id non puo' contenere trattini bassi.
 */
const metadati = async ({props}: {props: {dur: number}}) => {
  await caratteriPronti;
  return {durationInFrames: Math.max(1, Math.round(props.dur * BRAND.fps))};
};

const base = {width: BRAND.w, height: BRAND.h, fps: BRAND.fps, durationInFrames: 200};

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="sottotitoli"
        component={Sottotitoli}
        {...base}
        calculateMetadata={metadati}
        defaultProps={{
          dur: 3,
          stile: 'pillola' as const,
          gruppi: [{a: 0, b: 3, parole: [{testo: 'Arriva', t: 0, forte: true}, {testo: 'a pezzi', t: 0.6, forte: false}]}],
        }}
      />
      <Composition
        id="apertura"
        component={Apertura}
        {...base}
        calculateMetadata={metadati}
        defaultProps={{
          dur: 2,
          immagine: 'apertura.png',
          occhiello: 'OCCHIELLO',
          titolo: [[{testo: 'Un titolo'}], [{testo: 'su due righe.', accento: true}]],
          sfuma: 0.2,
          soloTesto: false,
        }}
      />
      <Composition
        id="copertura"
        component={Copertura}
        {...base}
        calculateMetadata={metadati}
        defaultProps={{
          dur: 8,
          occhiello: 'IL CONTO',
          titolo: 'Quello che conta davvero',
          voci: [
            {testo: 'Prima voce', t: 1},
            {testo: 'Seconda voce', t: 2.5},
            {testo: 'Terza voce', t: 4},
          ],
          esito: {testo: 'La frase che resta', t: 6},
        }}
      />
      <Composition
        id="timbro"
        component={Timbro}
        {...base}
        calculateMetadata={metadati}
        defaultProps={{dur: 3, t: 1, testo: 'GIA\' PAGATO', centro: {x: 540, y: 1030}}}
      />
    </>
  );
};
