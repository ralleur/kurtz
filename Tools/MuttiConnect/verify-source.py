#!/usr/bin/env python3
"""Only link the reviewed transport tree, even if the server docs advance later."""
from pathlib import Path
import json, os, subprocess, sys
lock=json.loads(Path(__file__).with_name('source.json').read_text())
source=Path(sys.argv[1]).resolve()
def git(*args):return subprocess.check_output(['git','-C',str(source),*args],text=True).strip()
try:
    root=Path(git('rev-parse','--show-toplevel'))
    relative=str(source.relative_to(root))
    expected=git('rev-parse',lock['commit']+':'+lock['path'])
    actual=git('rev-parse','HEAD:'+relative)
    dirty=git('status','--porcelain','--',str(source))
except (ValueError,subprocess.CalledProcessError):
    raise SystemExit('Mutti source checkout/pinned commit missing; see Tools/MuttiConnect/source.json')
if actual!=expected or dirty:
    if os.environ.get('MUTTI_ALLOW_DIRTY')!='1':raise SystemExit('Mutti transport differs from the reviewed source pin. Use MUTTI_ALLOW_DIRTY=1 only for local development.')
    print('Mutti: building explicitly unpinned development sources',file=sys.stderr)
print('Mutti transport source:',lock['commit'])
