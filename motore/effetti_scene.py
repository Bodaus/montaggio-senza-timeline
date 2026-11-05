"""Le scene di EffectCraft: script in stile After Effects, una per stile.

Si combinano sullo stesso tratto, con la persona ritagliata sopra i testi, cosi'
i testi le passano dietro. I valori fra %(...) li mette `effetti.py`.
"""

BASE = r"""
var W = 1080, H = 1920, FPS = 25, DUR = %(dur).4f;
var ACCENT = [%(acc)s], TEXT = [245/255, 245/255, 247/255], BG = [0, 0, 0];
var FONT = "%(font)s";
function importa(f) { return app.project.importFile(new ImportOptions(new File(f))); }
var comp = app.project.items.addComp("Effetto", W, H, 1, DUR, FPS);
var sfondo = comp.layers.add(importa("%(piano)s"));
function easeAll(prop, inf) {
  for (var k = 1; k <= prop.numKeys; k++) {
    try {
      prop.setInterpolationTypeAtKey(k, KeyframeInterpolationType.BEZIER);
      var v = prop.keyValue(k), dims = (v instanceof Array) ? v.length : 1, e = [];
      for (var d = 0; d < dims; d++) e.push(new KeyframeEase(0, inf));
      prop.setTemporalEaseAtKey(k, e, e);
    } catch (err) { writeLn("ease " + prop.name + ": " + err); }
  }
}
var tinta = sfondo.property("ADBE Effect Parade").addProperty("ADBE Tint");
tinta.property(3).setValue(0);
var sfoc = sfondo.property("ADBE Effect Parade").addProperty("ADBE Gaussian Blur 2");
sfoc.property(1).setValue(0);
var scuro = comp.layers.addSolid([0, 0, 0], "Scuro", W, H, 1);
scuro.transform.opacity.setValue(0);
function testo(s, corpo, pieno, colore) {
  var t = comp.layers.addText(s);
  var p = t.property("ADBE Text Properties").property("ADBE Text Document"), td = p.value;
  td.font = FONT; td.fontStyle = "Bold"; td.fontSize = corpo;
  td.justification = ParagraphJustification.LEFT_JUSTIFY;
  try { td.tracking = -10; } catch (e) {}
  if (pieno) { td.fillColor = colore; td.applyStroke = false; }
  else { td.applyFill = false; td.applyStroke = true; td.strokeColor = colore; td.strokeWidth = 11; }
  p.setValue(td);
  return t;
}
function misura(t) { var r = t.sourceRectAtTime(0, false); return {w: r.width, h: -r.top, x: r.left}; }
"""

NASTRO = r"""
// il nastro: una frase gigante che scorre dietro la testa, da destra a sinistra
var nt = testo(%(testo)s, %(corpo)d, %(pieno)s, ACCENT), nm = misura(nt);
var NB = Math.round(%(testa).1f + 0.55 * nm.h);           // meta' alta sopra la testa
var NDA = %(da).4f, NA = %(a).4f;
nt.transform.position.setValueAtTime(NDA, [120, NB]);
nt.transform.position.setValueAtTime(NA, [W - 120 - nm.w, NB]);
nt.transform.opacity.setValueAtTime(NDA, 0); nt.transform.opacity.setValueAtTime(NDA + 0.12, 100);
nt.transform.opacity.setValueAtTime(NA - 0.15, 100); nt.transform.opacity.setValueAtTime(NA, 0);
writeLn("nastro corpo %(corpo)d largo " + Math.round(nm.w) + ", base " + NB + ", cima " + Math.round(NB - nm.h));
"""

SALE = r"""
// una parola sola sale da dietro la testa; la testa ne copre al massimo un terzo
var st = testo(%(testo)s, %(corpo)d, %(pieno)s, ACCENT), sm = misura(st);
var SX = Math.round((W - sm.w) / 2 - sm.x), SB = Math.round(%(testa).1f + %(copre).3f * sm.h);
var SDA = %(da).4f, STORNA = %(torna).4f;
st.transform.position.setValueAtTime(SDA, [SX, SB + sm.h + 80]);
st.transform.position.setValueAtTime(SDA + 0.55, [SX, SB]);
if (STORNA > 0) {
  st.transform.position.setValueAtTime(STORNA, [SX, SB - 10]);
  st.transform.position.setValueAtTime(STORNA + 0.4, [SX, SB + sm.h + 80]);
  st.transform.opacity.setValueAtTime(STORNA + 0.25, 100); st.transform.opacity.setValueAtTime(STORNA + 0.4, 0);
} else {
  st.transform.position.setValueAtTime(DUR - 0.04, [SX, SB - 16]);
}
easeAll(st.transform.position, 85);
st.transform.opacity.setValueAtTime(SDA, 0); st.transform.opacity.setValueAtTime(SDA + 0.12, 100);
writeLn("sale corpo %(corpo)d largo " + Math.round(sm.w) + " alto " + Math.round(sm.h) + ", base " + SB + ", cima " + Math.round(SB - sm.h));
"""

SCHEDA = r"""
// la scheda: sale da dietro la testa e ci resta appoggiata (scura o d'accento)
var ACC = %(accento)s, CORPO = %(corpo)d, PAD = 26;
var kt = testo(%(testo)s, CORPO, true, ACC ? BG : ACCENT), km = misura(kt);
var SW = Math.round(km.w + 2 * PAD + (ACC ? 0 : 10)), SH = Math.round(CORPO * 1.08 + 2 * PAD - 8);
var fondo = comp.layers.addShape(); fondo.name = "Fondo scheda";
var cf = fondo.property("ADBE Root Vectors Group").addProperty("ADBE Vector Group").property("ADBE Vectors Group");
var rf = cf.addProperty("ADBE Vector Shape - Rect");
rf.property("ADBE Vector Rect Size").setValue([SW, SH]);
rf.property("ADBE Vector Rect Position").setValue([SW / 2, SH / 2]);
rf.property("ADBE Vector Rect Roundness").setValue(10);
var ff = cf.addProperty("ADBE Vector Graphic - Fill");
ff.property("ADBE Vector Fill Color").setValue(ACC ? ACCENT : BG); ff.property("ADBE Vector Fill Opacity").setValue(ACC ? 100 : 86);
if (!ACC) {
  var cb = fondo.property("ADBE Root Vectors Group").addProperty("ADBE Vector Group").property("ADBE Vectors Group");
  var rb = cb.addProperty("ADBE Vector Shape - Rect");
  rb.property("ADBE Vector Rect Size").setValue([8, SH]); rb.property("ADBE Vector Rect Position").setValue([4, SH / 2]);
  cb.addProperty("ADBE Vector Graphic - Fill").property("ADBE Vector Fill Color").setValue(ACCENT);
}
fondo.transform.anchorPoint.setValue([0, 0]);
var slitta = comp.layers.addNull(); slitta.name = "Scheda"; slitta.transform.anchorPoint.setValue([0, 0]);
fondo.parent = slitta; fondo.transform.position.setValue([0, 0]);
kt.parent = slitta; kt.transform.position.setValue([PAD + (ACC ? 0 : 10) - km.x, PAD + CORPO * 0.86]);
kt.moveBefore(fondo);
kt.transform.opacity.expression = "thisComp.layer(\"Fondo scheda\").transform.opacity";
var XS = Math.min(1020 - SW, Math.max(60, %(cx).1f - SW / 2));
var Y0 = %(testa).1f + 30, YF = Math.round(%(testa).1f - 0.75 * SH);
var KDA = %(da).4f, KTORNA = %(torna).4f;
if (%(ribalta)s) {
  // l'anta: la scheda e' gia' al suo posto e si gira in prospettiva intorno al
  // suo asse verticale; il centro della scheda sta sull'origine della slitta
  comp.renderer = "ADBE Advanced 3d";
  slitta.threeDLayer = true; fondo.threeDLayer = true; kt.threeDLayer = true;
  fondo.property("ADBE Material Options Group").property("ADBE Accepts Lights").setValue(0);
  kt.property("ADBE Material Options Group").property("ADBE Accepts Lights").setValue(0);
  fondo.transform.position.setValue([-SW / 2, -SH / 2, 0]);
  kt.transform.position.setValue([PAD + (ACC ? 0 : 10) - km.x - SW / 2, PAD + CORPO * 0.86 - SH / 2, -1]);
  slitta.transform.position.setValue([XS + SW / 2, YF + SH / 2, 0]);
  slitta.transform.yRotation.setValueAtTime(KDA, 92);
  slitta.transform.yRotation.setValueAtTime(KDA + 0.55, 0);
  if (KTORNA > 0) { slitta.transform.yRotation.setValueAtTime(KTORNA, 0); slitta.transform.yRotation.setValueAtTime(KTORNA + 0.35, -92); }
  easeAll(slitta.transform.yRotation, 85);
  fondo.transform.opacity.setValueAtTime(KDA, 0); fondo.transform.opacity.setValueAtTime(KDA + 0.1, 100);
  writeLn("scheda ruota " + SW + "x" + SH + " corpo " + CORPO + ", centro " + Math.round(XS + SW / 2) + "," + Math.round(YF + SH / 2));
} else {
slitta.transform.position.setValueAtTime(KDA, [XS, Y0]);
slitta.transform.position.setValueAtTime(KDA + 0.45, [XS, YF]);
if (KTORNA > 0) {
  slitta.transform.position.setValueAtTime(KTORNA, [XS, YF]);
  slitta.transform.position.setValueAtTime(KTORNA + 0.35, [XS, Y0]);
}
easeAll(slitta.transform.position, 85);
fondo.transform.opacity.setValueAtTime(KDA, 0); fondo.transform.opacity.setValueAtTime(KDA + 0.12, 100);
if (KTORNA > 0) { fondo.transform.opacity.setValueAtTime(KTORNA + 0.25, 100); fondo.transform.opacity.setValueAtTime(KTORNA + 0.35, 0); }
writeLn("scheda " + SW + "x" + SH + " corpo " + CORPO + ", x " + Math.round(XS) + ", sale a " + YF);
}
"""

ESTRUSO = r"""
// la parola in rilievo: estrusa, illuminata, sale da dietro la testa girando
comp.renderer = "ADBE Advanced 3d";
var xt = testo(%(testo)s, %(corpo)d, true, ACCENT), xm = misura(xt);
// bordo scuro spesso: accento pieno sulla libreria (libri colorati) si notava poco
// (utente, 18/10). Il filo sta dietro il pieno, quindi se ne vede meta'.
var xp = xt.property("ADBE Text Properties").property("ADBE Text Document"), xd = xp.value;
xd.applyStroke = true; xd.strokeColor = BG; xd.strokeWidth = %(bordo)d;
try { xd.strokeOverFill = false; } catch (e) { writeLn("estruso filo: " + e); }
xp.setValue(xd);
xm = misura(xt);
xt.threeDLayer = true;
var go = xt.property("geometryOptions");
go.property("extrusionDepth").setValue(70); go.property("bevelDepth").setValue(3); go.property("bevelStyle").setValue(2);
xt.transform.anchorPoint.setValue([xm.x + xm.w / 2, -xm.h / 2, 0]);
var XB = Math.round(%(testa).1f + %(copre).3f * xm.h - xm.h / 2);
var XDA = %(da).4f, XTORNA = %(torna).4f, XC = %(xc).1f;
xt.transform.position.setValueAtTime(XDA, [XC, XB + xm.h + 90, 0]);
xt.transform.position.setValueAtTime(XDA + 0.6, [XC, XB, 0]);
xt.transform.yRotation.setValueAtTime(XDA, -80);
xt.transform.yRotation.setValueAtTime(XDA + 0.6, -16);
xt.transform.yRotation.setValueAtTime(XTORNA > 0 ? XTORNA : DUR - 0.04, -6);
if (XTORNA > 0) {
  xt.transform.position.setValueAtTime(XTORNA, [XC, XB, 0]);
  xt.transform.position.setValueAtTime(XTORNA + 0.4, [XC, XB + xm.h + 90, 0]);
  xt.transform.yRotation.setValueAtTime(XTORNA + 0.4, 70);
  xt.transform.opacity.setValueAtTime(XTORNA + 0.3, 100); xt.transform.opacity.setValueAtTime(XTORNA + 0.4, 0);
}
easeAll(xt.transform.position, 85); easeAll(xt.transform.yRotation, 75);
xt.transform.opacity.setValueAtTime(XDA, 0); xt.transform.opacity.setValueAtTime(XDA + 0.12, 100);
var spot = comp.layers.addLight("Spot", [540, 960]); spot.lightType = LightType.SPOT;
var so = spot.property("ADBE Light Options Group");
so.property("ADBE Light Intensity").setValue(115); so.property("ADBE Light Cone Angle").setValue(120); so.property("ADBE Light Cone Feather 2").setValue(80);
spot.transform.position.setValue([120, 80, -900]); spot.transform.pointOfInterest.setValue([XC, XB, 0]);
var amb = comp.layers.addLight("Ambiente", [540, 960]); amb.lightType = LightType.AMBIENT;
amb.property("ADBE Light Options Group").property("ADBE Light Intensity").setValue(45);
writeLn("estruso corpo %(corpo)d largo " + Math.round(xm.w) + " alto " + Math.round(xm.h) + ", centro y " + XB);
"""

PROFONDITA = r"""
// la profondita': persona e sfondo vuoto su due piani, la camera si avvicina
comp.renderer = "ADBE Advanced 3d";
var cam = comp.layers.addCamera("Camera", [540, 960]);
var Z = cam.property("ADBE Camera Options Group").property("ADBE Camera Zoom").value;
var vuoto = comp.layers.add(importa("%(vuoto)s"));
vuoto.moveAfter(scuro);
vuoto.threeDLayer = true;
var D = 700, SC = (Z + D) / Z * 100 * 1.06;
vuoto.transform.position.setValue([540, 960, D]);
vuoto.transform.scale.setValue([SC, SC, 100]);
var bl = vuoto.property("ADBE Effect Parade").addProperty("ADBE Gaussian Blur 2");
persone.threeDLayer = true; contorno.threeDLayer = true;
var PDA = %(da).4f;
// tutto lo sfondo si sfoca insieme, come in "sfoca". Con la sfocatura fissa a 10
// il riempimento intorno alla testa restava una striscia impastata su una
// libreria quasi nitida: un'aura (utente, 18/10). Ora si parte dal girato vero
// (sfondo, identico al master) e si passa allo sfondo vuoto mentre entrambi si
// sfocano a 28: il riempimento sparisce nella sfocatura comune.
var PSF = 28;
bl.property(1).setValueAtTime(PDA, 0); bl.property(1).setValueAtTime(PDA + 0.7, PSF);
sfoc.property(1).setValueAtTime(PDA, 0); sfoc.property(1).setValueAtTime(PDA + 0.7, PSF);
vuoto.transform.opacity.setValueAtTime(PDA, 0); vuoto.transform.opacity.setValueAtTime(PDA + 0.35, 100);
scuro.transform.opacity.setValueAtTime(PDA, 0); scuro.transform.opacity.setValueAtTime(PDA + 0.7, 20);
easeAll(bl.property(1), 70); easeAll(sfoc.property(1), 70); easeAll(scuro.transform.opacity, 70);
// la camera resta dritta: il punto guardato le sta sempre davanti (con il punto
// sul volto si inclinava, vedeva i piani di sbieco e scopriva i bordi neri).
// Si avvicina al volto spostandosi verso di lui, del 17 per cento.
var FX = 540 + 0.17 * (%(cx).1f - 540) + 30, FY = 960 + 0.17 * (%(cy).1f - 960);
var tappe = [[0, 540, 960, -Z], [PDA, 540, 960, -Z], [DUR - 0.04, FX, FY, -Z + 0.17 * Z]];
for (var i = 0; i < tappe.length; i++) {
  var q = tappe[i];
  cam.transform.position.setValueAtTime(q[0], [q[1], q[2], q[3]]);
  cam.transform.pointOfInterest.setValueAtTime(q[0], [q[1], q[2], 0]);
}
easeAll(cam.transform.position, 60); easeAll(cam.transform.pointOfInterest, 60);
writeLn("profondita' zoom camera " + Math.round(Z) + ", sfondo a " + D + " scala " + Math.round(SC));
"""

PERSONA = r"""
var persone = comp.layers.add(importa("%(ritaglio)s"));
try {
  var ombra = persone.property("ADBE Effect Parade").addProperty("ADBE Drop Shadow");
  ombra.property("Opacity").setValue(45); ombra.property("Direction").setValue(160);
  ombra.property("Distance").setValue(18); ombra.property("Softness").setValue(36);
} catch (e) { writeLn("ombra: " + e); }
var contorno = comp.layers.add(importa("%(contorno)s"));
contorno.transform.opacity.setValue(0);
var strati = [sfondo, persone, contorno];
"""


FOLLA = r"""
// uno su venti (23/10): il quadro si spegne e si riempie di tue copie grigie;
// tu ti stringi nella tua casella, a colori e col filo accento
var FDA = %(da).4f, AX = %(ax).1f, AY = %(ay).1f, S = %(s).2f, COLS = 5, ROWS = 4, HI = 8;
function cella(i) { return [108 + 216 * (i %% COLS), 400 + 230 * Math.floor(i / COLS)]; }
var fondoF = comp.layers.addSolid(BG, "Fondo folla", W, H, 1);
fondoF.moveAfter(scuro);
fondoF.transform.opacity.setValueAtTime(FDA, 0); fondoF.transform.opacity.setValueAtTime(FDA + 0.3, 100);
var copie = [];
for (var i = 0; i < COLS * ROWS; i++) {
  if (i == HI) continue;
  var c = comp.layers.add(persone.source);
  var tg = c.property("ADBE Effect Parade").addProperty("ADBE Tint"); tg.property(3).setValue(100);
  c.transform.anchorPoint.setValue([AX, AY]);
  c.transform.position.setValue(cella(i));
  var t0 = FDA + 0.35 + 0.025 * i;
  c.transform.scale.setValueAtTime(t0, [0, 0]); c.transform.scale.setValueAtTime(t0 + 0.3, [S, S]);
  easeAll(c.transform.scale, 80);
  c.transform.opacity.setValueAtTime(t0, 0); c.transform.opacity.setValueAtTime(t0 + 0.12, 62);
  copie.push(c);
}
try { contorno.moveToBeginning(); persone.moveToBeginning(); contorno.moveToBeginning(); }
catch (e) { writeLn("folla ordine: " + e); }
var dove = cella(HI);
var lui = [persone, contorno];
for (var j = 0; j < lui.length; j++) {
  lui[j].transform.anchorPoint.setValue([AX, AY]);
  lui[j].transform.position.setValueAtTime(FDA, [AX, AY]); lui[j].transform.position.setValueAtTime(FDA + 0.5, dove);
  lui[j].transform.scale.setValueAtTime(FDA, [100, 100]); lui[j].transform.scale.setValueAtTime(FDA + 0.5, [S * 1.15, S * 1.15]);
  easeAll(lui[j].transform.position, 80); easeAll(lui[j].transform.scale, 80);
}
contorno.transform.opacity.setValueAtTime(FDA + 0.35, 0); contorno.transform.opacity.setValueAtTime(FDA + 0.6, 100);
writeLn("folla scala " + S + " copie " + copie.length + ", tu in " + dove);
"""

FUMETTO = r"""
// il fumetto (23/10): sullo scenario d'esempio l'immagine diventa un disegno
var UDA = %(da).4f, UA = %(a).4f;
var adjU = comp.layers.addSolid([1, 1, 1], "Fumetto", W, H, 1); adjU.adjustmentLayer = true;
var fxU = adjU.property("ADBE Effect Parade");
var cart = fxU.addProperty("Cartoon");
cart.property("Render").setValue(3); cart.property("Detail Radius").setValue(12); cart.property("Detail Threshold").setValue(14);
// Posterize mandava la maglia sul verde oliva e il viso sul rosa (tavola del
// 23/10): via, e i colori si spengono di un terzo con Tint
var spento = fxU.addProperty("ADBE Tint"); spento.property(3).setValue(35);
adjU.transform.opacity.setValueAtTime(UDA, 0); adjU.transform.opacity.setValueAtTime(UDA + 0.16, 100);
adjU.transform.opacity.setValueAtTime(UA - 0.16, 100); adjU.transform.opacity.setValueAtTime(UA, 0);
// l'etichetta su un fondo d'accento: a filo sulla libreria non si leggeva
var tag = testo("ESEMPIO", 50, true, BG), tm = misura(tag);
var pill = comp.layers.addSolid(ACCENT, "Etichetta", Math.round(tm.w + 44), 74, 1);
pill.transform.anchorPoint.setValue([0, 0]); pill.transform.position.setValue([60, 286]);
tag.moveToBeginning();
tag.transform.position.setValue([82 - tm.x, 286 + 37 + tm.h / 2]);
pill.transform.opacity.setValueAtTime(UDA, 0); pill.transform.opacity.setValueAtTime(UDA + 0.16, 100);
pill.transform.opacity.setValueAtTime(UA - 0.16, 100); pill.transform.opacity.setValueAtTime(UA, 0);
tag.transform.opacity.setValueAtTime(UDA, 0); tag.transform.opacity.setValueAtTime(UDA + 0.16, 100);
tag.transform.opacity.setValueAtTime(UA - 0.16, 100); tag.transform.opacity.setValueAtTime(UA, 0);
writeLn("fumetto da " + UDA + " a " + UA);
"""

VERTIGO = r"""
// vertigo (23/10): tu resti fermo, lo sfondo senza di te ti viene addosso
var VDA = %(da).4f, VX = %(cx).1f, VY = %(cy).1f;
var vuotoV = comp.layers.add(importa("%(vuoto)s"));
vuotoV.moveAfter(scuro);
vuotoV.transform.anchorPoint.setValue([VX, VY]); vuotoV.transform.position.setValue([VX, VY]);
vuotoV.transform.opacity.setValueAtTime(VDA, 0); vuotoV.transform.opacity.setValueAtTime(VDA + 0.08, 100);
vuotoV.transform.scale.setValueAtTime(VDA, [100, 100]); vuotoV.transform.scale.setValueAtTime(DUR - 0.04, [148, 148]);
easeAll(vuotoV.transform.scale, 45);
var blV = vuotoV.property("ADBE Effect Parade").addProperty("ADBE Gaussian Blur 2");
blV.property(1).setValueAtTime(VDA, 4); blV.property(1).setValueAtTime(DUR - 0.04, 16);
scuro.transform.opacity.setValueAtTime(VDA, 0); scuro.transform.opacity.setValueAtTime(DUR - 0.04, 28);
writeLn("vertigo da " + VDA);
"""

GLITCH = r"""
// glitch (23/10): per otto fotogrammi l'immagine si rompe, sulla parola
var GDA = %(da).4f;
var adjG = comp.layers.addSolid([1, 1, 1], "Glitch", W, H, 1); adjG.adjustmentLayer = true;
var gl = adjG.property("ADBE Effect Parade").addProperty("VR Digital Glitch");
var amp = gl.property("Master Amplitude"), evo = gl.property("Distortion Evolution");
amp.setValueAtTime(Math.max(0, GDA - 0.04), 0); amp.setValueAtTime(GDA, 170);
amp.setValueAtTime(GDA + 0.22, 150); amp.setValueAtTime(GDA + 0.34, 0);
evo.setValueAtTime(GDA, 0); evo.setValueAtTime(GDA + 0.34, 900);
var strG = [sfondo, persone, contorno];
for (var g = 0; g < strG.length; g++) {
  strG[g].transform.position.setValueAtTime(GDA, [540, 960]); strG[g].transform.position.setValueAtTime(GDA + 0.04, [556, 960]);
  strG[g].transform.position.setValueAtTime(GDA + 0.12, [528, 960]); strG[g].transform.position.setValueAtTime(GDA + 0.2, [540, 960]);
}
writeLn("glitch da " + GDA);
"""


def luce(prop, da, torna, pieno):
    """Chiavi d'ingresso (0,4 s) e di ritorno per una proprieta' che si accende."""
    s = f"{prop}.setValueAtTime({da:.4f}, 0); {prop}.setValueAtTime({da + 0.4:.4f}, {pieno});\n"
    if torna > 0:
        s += f"{prop}.setValueAtTime({torna:.4f}, {pieno}); {prop}.setValueAtTime({torna + 0.4:.4f}, 0);\n"
    return s + f"easeAll({prop}, 70);\n"


def scala(da, a, fino, cx, cy, inf=60):
    """Le tre immagini della persona scalano insieme intorno al volto."""
    return (f"for (var i = 0; i < strati.length; i++) {{\n"
            f"  strati[i].transform.anchorPoint.setValue([{cx:.1f}, {cy:.1f}]);\n"
            f"  strati[i].transform.position.setValue([{cx:.1f}, {cy:.1f}]);\n"
            f"  strati[i].transform.scale.setValueAtTime({da:.4f}, [100, 100]);\n"
            f"  strati[i].transform.scale.setValueAtTime({a:.4f}, [{fino}, {fino}]);\n"
            f"  easeAll(strati[i].transform.scale, {inf});\n}}\n")
