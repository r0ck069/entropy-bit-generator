#!/usr/bin/env python3
"""
Genera da generatore_bit.py i casi di confronto per la pagina HTML (1500 sessioni casuali con rilanci e annullamenti,
300 stringhe per lo SHA-256, una griglia di configurazioni) e li scrive in un file JSON.
Uso:  python3 verifica/genera_casi.py  <file_json_di_uscita>
"""
import datetime, hashlib, importlib.util, json, random, sys
from pathlib import Path
sys.dont_write_bytecode = True      # non lasciare __pycache__ nel repository
RADICE = Path(__file__).resolve().parent.parent
sp = importlib.util.spec_from_file_location("gb", RADICE / "generatore_bit.py"); G = importlib.util.module_from_spec(sp); sp.loader.exec_module(G)
COD = {"dado": lambda v: format(v - 1, "02b"), "moneta": lambda v: "0" if v == "T" else "1", "tombola": lambda v: format(v - 1, "03b")}
def esito(r, t): return r.randint(1, 4) if t == "dado" else (r.choice("TC") if t == "moneta" else r.randint(1, 8))
casi, atteso = [], []
for seme in range(1500):
    r = random.Random(seme)
    nd, nm, nt = r.randint(0, 4), r.randint(0, 4), r.randint(0, 4)
    if nd + nm + nt == 0: nt = 1
    if r.random() < 0.2:
        d, ps = r.choice([0, 3, 5, 10, 25, 50]), r.choice([50, 51, 52, 55, 60]); prof = ("c", d, ps); P = G.Profilo("personalizzato", d / 100, ps / 100)
    else:
        k = r.choice("123"); prof = ("p", k); P = G.PROFILI[k]
    modo, soglia = r.choice([("entropia", 384), ("entropia", 320), ("bit", 480), ("bit", 40), ("nessuna", 0),
                             ("bit", 6), ("bit", 12), ("bit", 30), ("entropia", 10), ("entropia", 25)])
    S = G.Sessione(P, nd, nm, nt, modo, soglia); ops = []
    for _ in range(r.randint(0, 260)):
        x = r.random()
        if x < 0.70:
            t = S.slot()[0]; v = esito(r, t); S.aggiungi(t, str(v), COD[t](v)); ops.append(["e", t, str(v), COD[t](v)])
        elif x < 0.80:
            v = r.choice([5, 6]); S.rilancio(v); ops.append(["r", v])
        else:
            k2 = r.randint(1, 25); S.undo(k2); ops.append(["u", k2])
    sl = S.slot(); ok = S.soglia_raggiunta() if S.modo != "nessuna" else True
    reg = G.testo_registro(S, datetime.datetime(2026, 10, 2, 12, 0, 0), datetime.datetime(2026, 10, 2, 12, 30, 45), ok)
    casi.append({"prof": prof, "n": [nd, nm, nt], "modo": modo, "soglia": soglia, "ops": ops})
    atteso.append({"bits": S.bitstring(), "tot": S.total_bits(), "h": S.total_h(), "slot": [sl[0], sl[1], sl[2], sl[3]], "fine": S.fine_ciclo(),
                   "sogl": S.soglia_raggiunta(), "compl": S.completato(), "coer": S.coerente(), "conteggi": S.conteggi(),
                   "rilanci": len(S.rilanci), "reg": reg})
r = random.Random(7); sha_in = ["".join(r.choice("01") for _ in range(r.randint(0, 300))) for _ in range(300)]
sha_ok = [hashlib.sha256(x.encode()).hexdigest() for x in sha_in]
griglia = []
for k in "123":
    for nd, nm, nt in [(1, 1, 1), (2, 3, 1), (0, 5, 0), (4, 0, 2), (10, 10, 10), (20, 20, 20), (1, 0, 0)]:
        for modo, soglia in [("entropia", 320), ("entropia", 384), ("entropia", 416), ("bit", 480), ("bit", 1200), ("nessuna", 0)]:
            P = G.PROFILI[k]; r2 = G.bit_per_esecuzione(P, nd, nm, nt, modo, soglia)
            griglia.append({"k": k, "n": [nd, nm, nt], "modo": modo, "soglia": soglia,
                            "att": None if r2 is None else [r2[0], r2[1], G.ripetizioni_necessarie(1200, r2[1])],
                            "hc": G.h_ciclo(P, nd, nm, nt), "bc": G.bit_ciclo(nd, nm, nt)})
json.dump({"versione": G.VERSIONE, "casi": casi, "atteso": atteso, "sha_in": sha_in, "sha_ok": sha_ok, "griglia": griglia}, open(sys.argv[1], "w"))
print("casi generati: %d sessioni, %d stringhe SHA-256, %d configurazioni (versione %s)" % (len(casi), len(sha_in), len(griglia), G.VERSIONE))
