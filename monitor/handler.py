import datetime,hashlib,json,os,time,uuid
from pathlib import Path
import boto3
from botocore.exceptions import ClientError
from scanner import scan,safe_error
from state import retain_evidence
s3=boto3.client('s3')
BUCKET=os.environ['DATA_BUCKET']
REGISTRY=json.loads(Path(__file__).with_name('source-registry.json').read_text())
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def read(key,default=None):
 try:return json.loads(s3.get_object(Bucket=BUCKET,Key=key)['Body'].read())
 except ClientError as e:
  if e.response['Error']['Code'] in ('NoSuchKey','404'):return default
  raise
def write(key,data):s3.put_object(Bucket=BUCKET,Key=key,Body=json.dumps(data,ensure_ascii=False).encode(),ContentType='application/json',CacheControl='no-store',ServerSideEncryption='AES256')
def run_scan(event,context):
 baseline=read('site/data/baseline.json')
 sources=sorted({h['assistanceUrl'] for h in baseline['hospitals'] if h.get('assistanceUrl','').startswith(('https://','http://'))})
 state=read('private/state.json',{'nextIndex':0})
 monitor=read('site/data/monitor.json',{'sources':{},'events':[]})
 if not sources:return {'checked':0,'error':'No source URLs in baseline'}
 count=min(4,len(sources));start=state.get('nextIndex',0)%len(sources);checked=0
 for i in range(count):
  if context and context.get_remaining_time_in_millis()<45000:break
  url=sources[(start+i)%len(sources)];at=now();old=monitor['sources'].get(url,{})
  try:result,snapshots=scan(REGISTRY.get(url,{}).get('canonicalUrl',url))
  except Exception as e:result={'error':safe_error(e),'manualReview':True,'candidates':[],'documents':[]};snapshots=[]
  result,changed=retain_evidence(old,result,at)
  if snapshots and (changed or result.get('comparisonReset') or not old.get('contentHash')):
   sid=hashlib.sha256(url.encode()).hexdigest()[:20]
   for name,body,content_type in snapshots:
    key=f'private/snapshots/{sid}/{at.replace(":","-")}/{name}'
    s3.put_object(Bucket=BUCKET,Key=key,Body=body,ContentType=content_type,ServerSideEncryption='AES256')
  if changed or not old or result.get('error')!=old.get('error'):
   kind='error' if result.get('error') else 'changed' if changed else 'first_seen'
   monitor.setdefault('events',[]).insert(0,{'id':hashlib.sha256((url+at).encode()).hexdigest()[:16],'url':url,'at':at,'kind':kind})
  monitor['sources'][url]=result;checked+=1
 monitor['events']=monitor.get('events',[])[:100]
 monitor.update(updatedAt=now(),mode='Hourly rotating source checks',totalSources=len(sources),batchSize=4)
 write('site/data/monitor.json',monitor)
 write('site/api/monitor',monitor)
 write('private/state.json',{'nextIndex':(start+checked)%len(sources),'updatedAt':now()})
 print(json.dumps({'checked':checked,'totalSources':len(sources),'nextIndex':(start+checked)%len(sources)}))
 return {'checked':checked,'totalSources':len(sources)}


def handler(event,context):
 table=boto3.resource('dynamodb').Table(os.environ['LOCK_TABLE'])
 token=str(uuid.uuid4())
 try:
  table.put_item(Item={'id':'scan','expires':int(time.time())+360,'owner':token},ConditionExpression='attribute_not_exists(id) OR expires < :now',ExpressionAttributeValues={':now':int(time.time())})
 except ClientError as e:
  if e.response['Error']['Code']=='ConditionalCheckFailedException':return {'checked':0,'skipped':'Another scan holds the lease'}
  raise
 try:return run_scan(event,context)
 finally:
  table.delete_item(Key={'id':'scan'},ConditionExpression='#owner = :owner',ExpressionAttributeNames={'#owner':'owner'},ExpressionAttributeValues={':owner':token})
