#!/usr/bin/env python3
"""A successful app build must contain the real bridge, not the fallback UI."""
from pathlib import Path
import subprocess,sys
app=Path(sys.argv[1]);directory=app/'Contents/MacOS' if (app/'Contents/MacOS').is_dir() else app
binary=directory/'kurtz.debug.dylib'
if not binary.exists():binary=directory/'kurtz'
symbols=subprocess.check_output(['nm','-g',str(binary)],text=True,stderr=subprocess.DEVNULL)
for symbol in ['_MCStart','_MCStatus','_MCStop','_MCFree']:
    if not any(line.split()[-1:]==[symbol] for line in symbols.splitlines()):raise SystemExit('Mutti transport missing from app binary: '+symbol)
print('PASS: app links the Mutti transport bridge')
