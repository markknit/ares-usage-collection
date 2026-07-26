#!/usr/bin/env python3
import argparse,csv,hashlib,json,pathlib,re,shutil,subprocess,sys,tempfile
PAT=re.compile(r'^ARES_USAGE_([A-Z0-9_-]+)_((?:20\d{2}-Q[1-4]-(?:MID|END))|AUTO)_(20\d{2}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2})\.csv$')
def run(*cmd):return subprocess.run(cmd,text=True,capture_output=True,check=True)
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--remote',required=True);ap.add_argument('--archive',required=True);ap.add_argument('--state',default='processed.json');ap.add_argument('--report-command');a=ap.parse_args();statep=pathlib.Path(a.state);state=json.loads(statep.read_text()) if statep.exists() else {'sha256':{}};rows=run('rclone','lsf',a.remote,'--files-only').stdout.splitlines();processed=[];rejected=[]
 with tempfile.TemporaryDirectory() as td:
  for name in rows:
   m=PAT.match(name)
   if not m: rejected.append({'file':name,'reason':'invalid filename'});continue
   local=pathlib.Path(td)/name;run('rclone','copyto',f'{a.remote}/{name}',str(local));data=local.read_bytes();sha=hashlib.sha256(data).hexdigest()
   if sha in state['sha256']: run('rclone','deletefile',f'{a.remote}/{name}');continue
   if len(data)<10 or b',' not in data[:4096]:rejected.append({'file':name,'reason':'not a plausible CSV'});continue
   school,collection,stamp=m.groups();dest=f"{a.archive}/{collection}/{school}/{name}";run('rclone','copyto',str(local),dest);run('rclone','deletefile',f'{a.remote}/{name}');state['sha256'][sha]={'file':name,'school':school,'collection':collection};processed.append(name)
 statep.write_text(json.dumps(state,indent=2)+'\n')
 if processed and a.report_command: subprocess.run(a.report_command,shell=True,check=True)
 print(json.dumps({'processed':processed,'rejected':rejected},indent=2));return 2 if rejected else 0
if __name__=='__main__':
 try:sys.exit(main())
 except subprocess.CalledProcessError as e:print(e.stderr or str(e),file=sys.stderr);sys.exit(1)
