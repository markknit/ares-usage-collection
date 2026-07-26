#!/usr/bin/env python3
import json,pathlib,subprocess,sys
root=pathlib.Path(__file__).resolve().parents[1]
subprocess.run([sys.executable,str(root/'tools/validate_portal.py')],check=True)
for page in ['index.html','setup.html','admin.html','troubleshooting.html']:
 t=(root/'public'/page).read_text()
 assert '<!doctype html>' in t.lower()
idx=json.loads((root/'public/schools/index.json').read_text());assert idx['schools']
print('Static portal tests passed.')
