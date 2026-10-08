#!/usr/bin/env python3
"""Fetch exactly the reviewed public transport source for clean CI builds."""
from pathlib import Path
import json,subprocess,sys
lock=json.loads(Path(__file__).with_name('source.json').read_text())
target=Path(sys.argv[1]).resolve()
if target.exists():raise SystemExit('Choose a new source checkout directory')
subprocess.run(['git','clone','--filter=blob:none','--no-checkout',lock['repository'],str(target)],check=True)
subprocess.run(['git','-C',str(target),'checkout','--detach',lock['commit']],check=True)
print(target/lock['path'])
