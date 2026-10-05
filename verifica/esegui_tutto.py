#!/usr/bin/env python3
"""
Lancia tutte le prove del repository, nell'ordine: programma, poi confronto pagina-programma e prova dell'input (Node.js).
Uso, dalla cartella del repository:   python3 verifica/esegui_tutto.py
Servono Python 3.7 o superiore e (per la pagina HTML) Node.js; senza Node.js le prove sulla pagina vengono saltate e lo dice.
Esito 0 se nessun passo fallisce (i passi saltati sono dichiarati); esito 1 se anche uno solo fallisce.
"""
import os, shutil, subprocess, sys, tempfile
from pathlib import Path
RADICE = Path(__file__).resolve().parent.parent
V = RADICE / "verifica"
passi = []
def esegui(nome, comando):
    print("\n" + "=" * 70 + "\n" + nome + "\n" + "=" * 70, flush=True)
    r = subprocess.run(comando, cwd=RADICE, env=dict(os.environ, PYTHONUTF8="1"))
    passi.append((nome, r.returncode == 0))
esegui("1) Prove sul programma (Python)", [sys.executable, str(V / "prove_programma.py")])
node = shutil.which("node")
if node:
    with tempfile.TemporaryDirectory() as d:
        casi = os.path.join(d, "casi.json")
        esegui("2) Generazione dei casi dal programma", [sys.executable, str(V / "genera_casi.py"), casi])
        esegui("3) Confronto pagina-programma (Node.js)", [node, str(V / "confronto_pagina.js"), str(RADICE / "generatore_bit.html"), casi])
    esegui("4) Prova dell'input della pagina (Node.js)", [node, str(V / "prova_input.js"), str(RADICE / "generatore_bit.html")])
else:
    print("\nNode.js non trovato: salto le prove sulla pagina HTML (passi 2, 3 e 4).")
    passi.append(("2-4) Prove sulla pagina HTML (richiedono Node.js)", None))
print("\n" + "=" * 70 + "\nRIEPILOGO\n" + "=" * 70)
for nome, ok in passi:
    print(("OK       " if ok else "SALTATO  " if ok is None else "FALLITO  ") + nome)
sys.exit(0 if all(ok is not False for _, ok in passi) and any(ok for _, ok in passi) else 1)
