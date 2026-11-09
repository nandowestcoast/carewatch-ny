"""Small bounded local scan. No AWS resources required. Public roster URLs only."""
import argparse,datetime,hashlib,json,sys,time
from pathlib import Path
from scanner import scan,safe_error
from state import retain_evidence
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--limit',type=int,default=4,choices=range(1,6));p.add_argument('--refresh-live',action='store_true',help='Read current public monitoring JSON over TLS before scanning')
a=p.parse_args();baseline=json.loads((ROOT/'public/data/baseline.json').read_text());path=ROOT/'public/data/monitor.json';monitor=json.loads(path.read_text())
if a.refresh_live:
 import urllib.request
 with urllib.request.urlopen('https://dwt8kng927tzh.cloudfront.net/data/monitor.json',timeout=25) as r:monitor=json.load(r)
local=ROOT/'.local';local.mkdir(exist_ok=True);cursor=local/'cursor.json';start=json.loads(cursor.read_text()).get('nextIndex',0) if cursor.exists() else 0
registry=json.loads((ROOT/'monitor/source-registry.json').read_text())
urls=sorted({h['assistanceUrl'] for h in baseline['hospitals'] if h['assistanceUrl'].startswith('https://')});approvals={}
if (local/'approved-hosts.json').exists():approvals=json.loads((local/'approved-hosts.json').read_text())
for i in range(a.limit):
 url=urls[(start+i)%len(urls)];at=datetime.datetime.now(datetime.timezone.utc).isoformat();old=monitor['sources'].get(url,{})
 try:result,snapshots=scan(registry.get(url,{}).get('canonicalUrl',url),approvals.get(url,[]))
 except Exception as e:result={'error':safe_error(e),'manualReview':True,'candidates':[],'documents':[]};snapshots=[]
 result,changed=retain_evidence(old,result,at);monitor['sources'][url]=result
 folder=local/'snapshots'/hashlib.sha256(url.encode()).hexdigest()[:20]/at.replace(':','-');folder.mkdir(parents=True,exist_ok=True)
 for name,body,mime in snapshots:(folder/(name+('.pdf' if mime=='application/pdf' else '.json' if mime=='application/json' else '.html'))).write_bytes(body)
 if changed or not old or old.get('error')!=result.get('error'):monitor.setdefault('events',[]).insert(0,{'id':hashlib.sha256((url+at).encode()).hexdigest()[:16],'url':url,'at':at,'kind':'error' if result.get('error') else 'changed' if changed else 'first_seen'})
 print(json.dumps({'sourceNumber':i+1,'status':'fetch-error' if result.get('error') else 'retrieved','candidateCount':len(result.get('candidates',[]))}))
monitor.update(updatedAt=datetime.datetime.now(datetime.timezone.utc).isoformat(),mode='Local bounded scan',totalSources=len(urls),batchSize=a.limit);monitor['events']=monitor.get('events',[])[:100];path.write_text(json.dumps(monitor,ensure_ascii=False));cursor.write_text(json.dumps({'nextIndex':(start+a.limit)%len(urls)}))
