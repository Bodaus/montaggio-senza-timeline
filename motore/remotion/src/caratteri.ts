import {staticFile} from 'remotion';

import {BRAND} from './brand';

/**
 * I caratteri si caricano dai file di font/, non da quelli installati: cosi' vale
 * su ogni computer, e le larghezze misurate sono quelle disegnate. Se la misura
 * arriva prima del carattere le parole si sovrappongono e la pillola non le copre,
 * senza nessun errore: per questo `calculateMetadata` aspetta questa promessa.
 */
export const caratteriPronti: Promise<unknown> = Promise.all(
  BRAND.caratteri.map((c) =>
    new FontFace(c.famiglia, `url(${staticFile('font/' + c.file)})`, {weight: String(c.peso)})
      .load()
      .then((f) => document.fonts.add(f)),
  ),
);
