// Prova a tappeto la validazione dell'input della pagina con stringhe casuali e avversarie. Solo moduli standard di Node.js.
// Uso:  node verifica/prova_input.js <generatore_bit.html>
const fs = require("fs"), vm = require("vm");
const html = fs.readFileSync(process.argv[2], "utf8");
const blocco = html.match(/<script id="core-script">([\s\S]*?)<\/script>/)[1];
const a = blocco.indexOf('"use strict";'), b = blocco.indexOf("/* ------------------------------ interfaccia ------------------------------ */");
const ctx = vm.createContext({ TextEncoder, console, Date, Math, JSON, Array, Object, Number, String, Uint8Array, Uint32Array, DataView });
vm.runInContext(blocco.slice(a, b) + "\nthis.G = {Sessione, PROFILI, stato, processa};\n", ctx); const G = ctx.G;
const usaInnerHtml = /innerHTML|outerHTML|insertAdjacentHTML|document\.write|eval\(|new Function/.test(blocco);
function nuova(tipo) { const n = { dado: [1, 0, 0], moneta: [0, 1, 0], tombola: [0, 0, 1] }[tipo];
  const s = new G.Sessione(G.PROFILI["2"], n[0], n[1], n[2], "nessuna", 0); G.stato.s = s; G.stato.msg = ""; return s; }
const alfabeto = ["0","1","2","3","4","5","6","7","8","9"," ","\t","\n","\r","+","-",".","e","x","T","C","t","c","E","S","A","R","O","U","<",">","&","\"","'","/","\\","\u0663","\u0969","\uFF13","\u00B2","\u0660","\u200B","\u0000","%","#",";"];
let seed = 12345; const rnd = () => (seed = (seed * 1664525 + 1013904223) >>> 0) / 4294967296;
const valido = { dado: t => /^[0-9]+$/.test(t) && +t >= 1 && +t <= 6, tombola: t => /^[0-9]+$/.test(t) && +t >= 1 && +t <= 8,
  moneta: t => ["T", "0", "TESTA", "C", "1", "CROCE"].includes(t.toUpperCase()) };
const attesoBit = { dado: t => (+t - 1).toString(2).padStart(2, "0"), tombola: t => (+t - 1).toString(2).padStart(3, "0"),
  moneta: t => (["T", "0", "TESTA"].includes(t.toUpperCase()) ? "0" : "1") };
const fissi = ["03","3 "," 3","+3","3.0","1e0","0x3","","7","9","999","9".repeat(60),"-1","\u0663","\uFF13","<img src=x onerror=alert(1)>","T\n","t","tEsTa"," T","TESTA ","00","01","1;2","1,2","\u200B3","3\u0000"];
let prove = 0, accettati = 0, rifiutati = 0, errori = 0; const anomalie = [];
for (const tipo of ["dado", "moneta", "tombola"]) {
  const lista = fissi.slice();
  for (let i = 0; i < 60000; i++) { const n = 1 + Math.floor(rnd() * 7); let t = ""; for (let k = 0; k < n; k++) t += alfabeto[Math.floor(rnd() * alfabeto.length)]; lista.push(t); }
  for (const t of lista) {
    const s = nuova(tipo); prove++;
    try { G.processa(tipo, t); } catch (e) { errori++; anomalie.push(["eccezione", tipo, JSON.stringify(t), String(e)]); continue; }
    const agg = s.esiti.length, ril = s.rilanci ? s.rilanci.length : 0, v = valido[tipo](t), rilancio = tipo === "dado" && v && (+t === 5 || +t === 6);
    if (v && !rilancio) { if (agg !== 1 || s.bitstring() !== attesoBit[tipo](t)) anomalie.push(["valido convertito male", tipo, JSON.stringify(t)]); else accettati++; }
    else if (rilancio) { if (agg !== 0 || ril !== 1) anomalie.push(["rilancio errato", tipo, JSON.stringify(t)]); else accettati++; }
    else { if (agg !== 0) anomalie.push(["NON valido ma accettato", tipo, JSON.stringify(t)]); else rifiutati++; }
    if (!s.coerente()) anomalie.push(["incoerenza interna", tipo, JSON.stringify(t)]);
  }
}
console.log("prove: " + prove + " | validi accettati e convertiti bene: " + accettati + " | rifiutati: " + rifiutati + " | eccezioni: " + errori + " | anomalie: " + anomalie.length);
console.log("uso di innerHTML, eval o simili nella pagina: " + (usaInnerHtml ? "SI (da controllare)" : "nessuno"));
anomalie.slice(0, 8).forEach(x => console.log("  ", x.join(" | ")));
const tutto = anomalie.length === 0 && errori === 0 && !usaInnerHtml;
console.log(tutto ? "PROVA DELL'INPUT: TUTTO REGOLARE" : "PROVA DELL'INPUT: CI SONO ANOMALIE");
process.exit(tutto ? 0 : 1);
