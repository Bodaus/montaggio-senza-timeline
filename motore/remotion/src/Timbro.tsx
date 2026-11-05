import React from 'react';

import {BRAND} from './brand';
import {useTempo} from './Comuni';

/**
 * Il timbro: una scritta che cade dall'alto, ruotata. Non ha bisogno della sagoma,
 * e dice la frase. Il girato sotto trema per un attimo: lo fa `effetti.py`.
 */
export type TimbroProps = {dur: number; t: number; testo: string; centro: {x: number; y: number}};

export const Timbro: React.FC<TimbroProps> = ({dur, t: quando, testo, centro}) => {
  const {t, molla} = useTempo();
  const k = molla(quando - 0.06, {damping: 11, stiffness: 260, mass: 0.5});
  if (t < quando - 0.08) return null;
  const via = 1 - Math.min(1, Math.max(0, (t - (dur - 0.35)) / 0.3));
  const corpo = Math.min(112, Math.floor(1180 / Math.max(6, testo.length)));
  return (
    <div
      style={{
        position: 'absolute',
        left: centro.x - 380,
        top: centro.y - 95,
        width: 760,
        height: 190,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        border: `10px solid ${BRAND.accent}`,
        borderRadius: 18,
        background: 'rgba(0,0,0,0.72)',
        color: BRAND.accent,
        fontFamily: `"${BRAND.famDisplay}", sans-serif`,
        fontWeight: 700,
        fontSize: corpo,
        letterSpacing: '0.04em',
        opacity: Math.min(1, k * 2.5) * via,
        transform: `rotate(-8deg) scale(${(2.2 - 1.2 * k).toFixed(3)})`,
        whiteSpace: 'nowrap',
      }}
    >
      {testo}
    </div>
  );
};
