import React from 'react';
import {AbsoluteFill, Img, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';

import {BRAND} from './brand';
import {BloccoTitolo, RigaTitolo} from './BloccoTitolo';

/**
 * L'apertura del video: il titolo della copertina sopra la frase d'aggancio.
 *
 * **Il fotogramma 0 e' la copertina.** Instagram e TikTok, per documentazione
 * delle loro API, se non gliene carichi una prendono il primo fotogramma;
 * LinkedIn anche, e dopo non si cambia. Cosi' la copertina giusta c'e' anche
 * quando nessuno la carica: pubblicando da un programmatore di post, o
 * dimenticandosene.
 *
 * Il titolo resta mentre la frase d'aggancio si dice e ne prende il posto nei
 * sottotitoli, perche' dice la stessa cosa. Nessun ingresso in dissolvenza: il
 * primo fotogramma deve averlo pieno. Esce in dissolvenza su `sfuma` secondi.
 *
 * Solo sul fotogramma 0 sotto il titolo c'e' `immagine`: il volto migliore del
 * blocco, con la stessa inquadratura. Dura 40 ms e cade prima che si apra
 * bocca, quindi a guardare il video non si vede; e' quello che la piattaforma
 * prende.
 */

export type AperturaProps = {
  dur: number;
  immagine: string;
  occhiello: string;
  titolo: RigaTitolo[];
  sfuma: number;
  soloTesto?: boolean;
};

export const Apertura: React.FC<AperturaProps> = ({
  dur,
  immagine,
  occhiello,
  titolo,
  sfuma,
  soloTesto = false,
}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const t = frame / fps;
  const alfa = Math.max(0, Math.min(1, (dur - t) / sfuma));

  return (
    <AbsoluteFill>
      {frame === 0 && !soloTesto ? (
        <Img
          src={staticFile(immagine)}
          style={{position: 'absolute', left: 0, top: 0, width: BRAND.w, height: BRAND.h}}
        />
      ) : null}
      <AbsoluteFill style={{opacity: alfa}}>
        <BloccoTitolo
          occhiello={occhiello}
          titolo={titolo}
          // 18/10: piu' basso e piu' piccolo, lo sfumato parte da 1180 e non da
          // 1080: copriva bocca e mento (segnalato dall'utente)
          fondo={BRAND.safeBottom - 12}  // le discendenti di "pezzi." scendevano a 1450
          maxCorpo={84}
          inizioSfumato={1180}
          soloTesto={soloTesto}
        />
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
