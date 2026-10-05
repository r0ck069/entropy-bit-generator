// Confronta la logica della pagina generatore_bit.html con quella del programma Python, in Node.js (solo moduli standard).
// Uso:  node verifica/confronto_pagina.js <generatore_bit.html> <casi.json>
const fs = require("fs"), vm = require("vm");
const html = fs.readFileSync(process.argv[2], "utf8");
const blocco = html.match(/<script id="core-script">([\s\S]*?)<\/script>/)[1];
const a = blocco.indexOf('"use strict";');
const b = blocco.indexOf("/* ------------------------------ interfaccia ------------------------------ */");
const c = blocco.indexOf("/* ------------------------------ controlli all'avvio ---------------------- */");
const d = blocco.indexOf("function mostraControlli()");
if ([a, b, c, d].some(x => x < 0)) { console.log("marcatori del codice non trovati: la pagina e' cambiata?"); process.exit(1); }
const codice = blocco.slice(a, b) + "\nfunction render(){}\n" + blocco.slice(c, d) +
  "\nthis.G = {Profilo, PROFILI, Sessione, testoRegistro, sha256Testo, bitPerEsecuzione, ripetizioniNecessarie, hCiclo, bitCiclo, eseguiControlli, ORDINE_FONTI, VERSIONE};\n";
const ctx = vm.createContext({ TextEncoder, console, Date, Math, JSON, Array, Object, Number, String, Uint8Array, Uint32Array, DataView });
vm.runInContext(codice, ctx); const G = ctx.G;
const D = JSON.parse(fs.readFileSync(process.argv[3], "utf8"));
console.log("versione pagina:", G.VERSIONE, "| versione programma:", D.versione, "| ordine fonti:", G.ORDINE_FONTI.join(","));
let fallito = G.VERSIONE !== D.versione;
if (fallito) console.log("  DIVERSE le versioni");
const ris = G.eseguiControlli();
console.log("controlli della pagina in Node.js: " + ris.filter(r => r.ok).length + " su " + ris.length + " superati");
ris.filter(r => !r.ok).forEach(r => { console.log("  FALLITO: " + r.nome); fallito = true; });
let diff = 0, regUguali = 0, concluse = 0;
const norm = o => JSON.stringify(Object.keys(o).sort().map(k => [k, Object.keys(o[k]).sort().map(j => [j, o[k][j]])]));
D.casi.forEach((cs, i) => {
  const prof = cs.prof[0] === "p" ? G.PROFILI[cs.prof[1]] : new G.Profilo("personalizzato", cs.prof[1] / 100, cs.prof[2] / 100);
  const s = new G.Sessione(prof, cs.n[0], cs.n[1], cs.n[2], cs.modo, cs.soglia);
  for (const op of cs.ops) { if (op[0] === "e") s.aggiungi(op[1], op[2], op[3]); else if (op[0] === "r") s.rilancio(op[1]); else s.undo(op[1]); }
  const sl = s.slot(), okS = s.modo !== "nessuna" ? s.sogliaRaggiunta() : true;
  const reg = G.testoRegistro(s, new Date(2026, 9, 2, 12, 0, 0), new Date(2026, 9, 2, 12, 30, 45), okS, false);
  const at = D.atteso[i];
  const uguali = s.bitstring() === at.bits && s.totalBits() === at.tot && Math.abs(s.totalH() - at.h) < 1e-9 &&
    JSON.stringify([sl.tipo, sl.i, sl.n, sl.ciclo]) === JSON.stringify(at.slot) && s.fineCiclo() === at.fine &&
    s.sogliaRaggiunta() === at.sogl && s.completato() === at.compl && s.coerente() === at.coer &&
    norm(s.conteggi()) === norm(at.conteggi) && s.rilanci.length === at.rilanci;
  if (!uguali) diff++;
  if (reg === at.reg) regUguali++;
  if (s.completato()) concluse++;
});
console.log("sessioni casuali confrontate con il programma Python: " + D.casi.length + " (di cui " + concluse + " concluse) | differenze: " + diff +
  " | testo del registro identico: " + regUguali + " su " + D.casi.length);
let shaOk = 0; D.sha_in.forEach((x, i) => { if (G.sha256Testo(x) === D.sha_ok[i]) shaOk++; });
console.log("SHA-256 uguale a quello di Python: " + shaOk + " su " + D.sha_in.length);
let gd = 0;
D.griglia.forEach(g => { const p = G.PROFILI[g.k]; const r = G.bitPerEsecuzione(p, g.n[0], g.n[1], g.n[2], g.modo, g.soglia);
  const att = r === null ? null : [r[0], r[1], G.ripetizioniNecessarie(1200, r[1])];
  if (JSON.stringify(att) !== JSON.stringify(g.att) || Math.abs(G.hCiclo(p, g.n[0], g.n[1], g.n[2]) - g.hc) > 1e-12 || G.bitCiclo(g.n[0], g.n[1], g.n[2]) !== g.bc) gd++; });
console.log("giri, bit e ripetizioni su " + D.griglia.length + " configurazioni: differenze " + gd);
const tutto = !fallito && diff === 0 && gd === 0 && regUguali === D.casi.length && shaOk === D.sha_in.length;
console.log(tutto ? "CONFRONTO PAGINA-PROGRAMMA: TUTTO UGUALE" : "CONFRONTO PAGINA-PROGRAMMA: CI SONO DIFFERENZE");
process.exit(tutto ? 0 : 1);
