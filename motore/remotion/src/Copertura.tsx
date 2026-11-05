import React from 'react';

import {BRAND} from './brand';
import {entra, useTempo} from './Comuni';
import {FONDO, LARGA, MARGINE, Occhiello, Palco, Titolo} from './Scena';

/**
 * La copertura a piena inquadratura dei blocchi "grafica".
 *
 * Regole della casa: l'impalcatura c'e' dal primo fotogramma e senza dissolvenza
 * (titolo e caselle vuote); sulla parola arriva solo cio' che la frase rivela. Le
 * voci entrano a scatto, una alla volta, e mai due insieme. Sotto y = FONDO non si
 * disegna niente: li' passano i sottotitoli.
 */
export type Voce = {testo: string; t: number};
export type CoperturaProps = {
  dur: number;
  occhiello?: string;
  titolo: string;
  voci: Voce[];
  esito?: Voce | null;
};

const Y0 = 470;
const SPAZIO = 22;

export const Copertura: React.FC<CoperturaProps> = ({occhiello, titolo, voci, esito}) => {
  const {molla} = useTempo();
  const n = Math.max(1, voci.length);
  const altezzaEsito = esito ? 190 : 0;
  const disponibile = FONDO - Y0 - altezzaEsito;
  const alta = Math.min(170, Math.floor((disponibile - (n - 1) * SPAZIO) / n));
  const corpo = Math.min(58, Math.round(alta * 0.42));
  const kEsito = esito ? molla(esito.t - 0.2) : 0;

  return (
    <Palco>
      {occhiello ? <Occhiello>{occhiello}</Occhiello> : null}
      <Titolo>{titolo}</Titolo>

      {voci.map((v, i) => {
        const k = molla(v.t - 0.2);
        const y = Y0 + i * (alta + SPAZIO);
        return (
          <div
            key={i}
            style={{
              position: 'absolute',
              left: MARGINE,
              top: y,
              width: LARGA,
              height: alta,
              borderRadius: 14,
              boxSizing: 'border-box',
              border: `3px ${k > 0.05 ? 'solid' : 'dashed'} ${k > 0.05 ? BRAND.accent : BRAND.rule}`,
              background: BRAND.panel,
              display: 'flex',
              alignItems: 'center',
              gap: 26,
              padding: '0 32px',
              overflow: 'hidden',
            }}
          >
            <div
              style={{
                fontFamily: `"${BRAND.famMono}", monospace`,
                fontWeight: 600,
                fontSize: Math.round(corpo * 0.72),
                color: k > 0.05 ? BRAND.accent : BRAND.sign,
              }}
            >
              {i + 1}
            </div>
            <div
              style={{
                fontFamily: `"${BRAND.famDisplay}", sans-serif`,
                fontWeight: 600,
                fontSize: corpo,
                lineHeight: 1.12,
                color: BRAND.text,
                ...entra(k),
              }}
            >
              {v.testo}
            </div>
          </div>
        );
      })}

      {esito ? (
        <div
          style={{
            position: 'absolute',
            left: MARGINE,
            top: FONDO - altezzaEsito + 30,
            width: BRAND.safeRight - MARGINE,
            fontFamily: `"${BRAND.famDisplay}", sans-serif`,
            fontWeight: 600,
            fontSize: 62,
            lineHeight: 1.06,
            color: BRAND.accent,
            ...entra(kEsito, 30),
          }}
        >
          {esito.testo}
        </div>
      ) : null}
    </Palco>
  );
};
