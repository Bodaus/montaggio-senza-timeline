import React from 'react';
import {fitText} from '@remotion/layout-utils';

import {BRAND} from './brand';

/**
 * L'impalcatura condivisa dalle coperture. Quello che prima stava in due posti
 * — il foglio di stile di Playwright e `occhiello()` di Manim, con due
 * tipografie leggermente diverse — qui sta in uno.
 *
 * Regole della casa, dal manuale: l'impalcatura c'e' dal primo fotogramma e non
 * entra in dissolvenza, gli eventi sono a scatto, e sotto y = SUB_TOP non si
 * disegna niente perche' li' passano i sottotitoli.
 */

export const MARGINE = 60;
export const LARGA = BRAND.w - MARGINE * 2;

/** L'intestazione: sopravvissuta all'occhiello, ma alla stessa altezza per
 *  tutte le coperture. Prima Manim la metteva a 220 e l'HTML a 60, e si vedeva
 *  passando dall'una all'altra.
 *
 *  Adesso attacca a `safeTop`, che e' dove finisce l'intestazione della
 *  piattaforma: sopra di li' un titolo c'e' ma non si legge. */
export const OCCHIELLO_Y = BRAND.safeTop;
export const TITOLO_Y = BRAND.safeTop + 52;

/** Sotto `subTop` non disegna nessuno: da li' in giu' passano i sottotitoli, e
 *  sotto `safeBottom` passa la didascalia della piattaforma. */
export const FONDO = BRAND.subTop;

export const Palco: React.FC<{children: React.ReactNode}> = ({children}) => (
  <div
    style={{
      position: 'absolute',
      inset: 0,
      background: BRAND.bg,
      color: BRAND.text,
      fontFamily: `"${BRAND.famText}", system-ui, sans-serif`,
      WebkitFontSmoothing: 'antialiased',
      overflow: 'hidden',
    }}
  >
    {children}
  </div>
);

export const Occhiello: React.FC<{children: string}> = ({children}) => (
  <div
    style={{
      position: 'absolute',
      left: MARGINE,
      top: OCCHIELLO_Y,
      fontFamily: `"${BRAND.famMono}", sans-serif`,
      fontWeight: 600,
      fontSize: 40,
      letterSpacing: '0.08em',
      textTransform: 'uppercase',
      color: BRAND.dim,
    }}
  >
    {children}
  </div>
);

/**
 * Il titolo si misura e si rimpicciolisce da solo se non ci sta in larghezza.
 *
 * In Manim un titolo a corpo 58 era uscito dal quadro e me ne ero accorto
 * guardando i fotogrammi. Qui la misura la fa il browser prima di disegnare,
 * quindi quel difetto non puo' piu' succedere: al massimo il titolo rimpicciolisce.
 */
export const Titolo: React.FC<{children: string; max?: number}> = ({
  children,
  max = 68,
}) => {
  const {fontSize} = fitText({
    text: children,
    withinWidth: LARGA,
    fontFamily: BRAND.famDisplay,
    fontWeight: String(BRAND.pesoTitolo),
    textTransform: 'none',
  });
  return (
    <div
      style={{
        position: 'absolute',
        left: MARGINE,
        top: TITOLO_Y,
        width: LARGA,
        fontFamily: `"${BRAND.famDisplay}", sans-serif`,
        fontWeight: BRAND.pesoTitolo,
        fontSize: Math.min(max, fontSize),
        lineHeight: 1.05,
      }}
    >
      {children}
    </div>
  );
};

/** Etichetta di sezione, sopra una cosa che si guarda. */
export const Etichetta: React.FC<{top: number; children: React.ReactNode}> = ({
  top,
  children,
}) => (
  <div
    style={{
      position: 'absolute',
      left: MARGINE,
      top,
      width: LARGA,
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'baseline',
      fontSize: 30,
      color: BRAND.dim,
    }}
  >
    {children}
  </div>
);

/** Riga di chiusura: la frase che la copertura sta dimostrando.
 *
 *  Sta nella parte bassa del quadro, dove a destra c'e' la colonna dei pulsanti
 *  della piattaforma: e' larga fino a `safeRight` e non fino al margine, cosi'
 *  una frase lunga va a capo prima di finirci sotto. */
export const Esito: React.FC<{
  top: number;
  forte: string;
  sotto?: string;
  mostraSotto?: boolean;
}> = ({top, forte, sotto, mostraSotto = true}) => (
  <div
    style={{
      position: 'absolute',
      left: MARGINE,
      top,
      width: BRAND.safeRight - MARGINE,
    }}
  >
    <div
      style={{
        fontFamily: `"${BRAND.famDisplay}", sans-serif`,
        fontWeight: BRAND.pesoTitolo,
        fontSize: 64,
        color: BRAND.accent,
        lineHeight: 1.05,
      }}
    >
      {forte}
    </div>
    {sotto && mostraSotto ? (
      <div style={{fontSize: 32, color: BRAND.dim, marginTop: 18}}>{sotto}</div>
    ) : null}
  </div>
);
