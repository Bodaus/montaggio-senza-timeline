import React from 'react';
import {spring, useCurrentFrame, useVideoConfig} from 'remotion';

import {BRAND} from './brand';

/**
 * Pezzi che le sei coperture del 05/10 usano tutte: il tempo in secondi, la
 * molla per gli ingressi a scatto, la scheda e l'etichetta in maiuscoletto.
 */

export const useTempo = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const t = frame / fps;
  const molla = (at: number, cfg = {damping: 18, stiffness: 170, mass: 0.6}) =>
    Math.min(1, spring({frame: frame - Math.round(at * fps), fps, config: cfg}));
  return {t, molla};
};

/** Ingresso a scatto: sale di qualche pixel e si accende. */
export const entra = (k: number, dy = 24): React.CSSProperties => ({
  opacity: Math.min(1, k * 1.4),
  transform: `translateY(${((1 - k) * dy).toFixed(1)}px)`,
});

export const Scheda: React.FC<{
  x: number;
  y: number;
  w: number;
  h: number;
  bordo?: string;
  tratteggio?: boolean;
  fondo?: string;
  style?: React.CSSProperties;
  children?: React.ReactNode;
}> = ({x, y, w, h, bordo = BRAND.rule, tratteggio = false, fondo = BRAND.panel, style, children}) => (
  <div
    style={{
      position: 'absolute',
      left: x,
      top: y,
      width: w,
      height: h,
      borderRadius: 12,
      border: `${tratteggio ? 3 : 2}px ${tratteggio ? 'dashed' : 'solid'} ${bordo}`,
      background: fondo,
      boxSizing: 'border-box',
      display: 'flex',
      alignItems: 'center',
      padding: '0 28px',
      ...style,
    }}
  >
    {children}
  </div>
);

export const Maiuscoletto: React.FC<{
  x: number;
  y: number;
  colore?: string;
  corpo?: number;
  style?: React.CSSProperties;
  children: React.ReactNode;
}> = ({x, y, colore = BRAND.dim, corpo = 26, style, children}) => (
  <div
    style={{
      position: 'absolute',
      left: x,
      top: y,
      fontFamily: `"${BRAND.famMono}", sans-serif`,
      fontWeight: 600,
      fontSize: corpo,
      letterSpacing: '0.08em',
      textTransform: 'uppercase',
      color: colore,
      whiteSpace: 'nowrap',
      ...style,
    }}
  >
    {children}
  </div>
);
