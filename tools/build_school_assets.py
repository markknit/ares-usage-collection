#!/usr/bin/env python3
import argparse,json,pathlib,re,sys

def code(v):
 v=re.sub(r'[^A-Za-z0-9_-]+','_',v.strip()).strip('_').upper()
 if not v: raise ValueError('invalid school code')
 return v

def main():
 p=argparse.ArgumentParser();p.add_argument('--root',default=str(pathlib.Path(__file__).resolve().parents[1]));p.add_argument('--code',required=True);p.add_argument('--name',required=True);p.add_argument('--ssid',default='ARES2');p.add_argument('--server',default='http://ares.local');a=p.parse_args();root=pathlib.Path(a.root);c=code(a.code)
 school={'code':c,'name':a.name,'wifi_ssid':a.ssid,'local_server_url':a.server,'collection_schedule_url':a.server.rstrip('/')+'/tracker/collection_schedule.json','assets':{'roundsync_apk':'assets/downloads/roundsync-approved.apk','roundsync_config':'assets/downloads/ARES-RoundSync-Config.zip','automation_config':f'assets/downloads/ARES-{c}-Automation.macro'}}
 d=root/'public'/'schools';d.mkdir(parents=True,exist_ok=True);(d/f'{c}.json').write_text(json.dumps(school,indent=2)+'\n')
 idx=d/'index.json';data=json.loads(idx.read_text()) if idx.exists() else {'schools':[]};data['schools']=[s for s in data['schools'] if s['code']!=c]+[{'code':c,'name':a.name,'wifi_ssid':a.ssid}];data['schools'].sort(key=lambda x:x['name']);idx.write_text(json.dumps(data,indent=2)+'\n')
 print(f'Created {d/f"{c}.json"}');print(f'Automation asset expected: public/assets/downloads/ARES-{c}-Automation.macro')
if __name__=='__main__':
 try: main()
 except Exception as e: print(e,file=sys.stderr);sys.exit(1)
