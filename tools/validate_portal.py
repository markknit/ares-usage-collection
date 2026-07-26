#!/usr/bin/env python3
import json,pathlib,sys
root=pathlib.Path(__file__).resolve().parents[1];errors=[]
idx=json.loads((root/'public/schools/index.json').read_text())
for s in idx['schools']:
 p=root/'public/schools'/f"{s['code']}.json"
 if not p.exists():errors.append(f'missing {p}')
 else:
  j=json.loads(p.read_text())
  for k in ['code','name','wifi_ssid','local_server_url','collection_schedule_url','assets']:
   if k not in j:errors.append(f'{p}: missing {k}')
for p in ['public/index.html','public/setup.html','public/admin.html','public/api/test-file.php']:
 if not (root/p).exists():errors.append(f'missing {p}')
if errors:
 print('\n'.join(errors));sys.exit(1)
print(f'Portal validation passed for {len(idx["schools"])} schools.')
