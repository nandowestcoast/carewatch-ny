"""Bounded public-document monitor. All passages require human verification."""
import hashlib,html,ipaddress,json,re,socket,ssl,urllib.parse,urllib.request,urllib.robotparser
from html.parser import HTMLParser
from io import BytesIO
from pypdf import PdfReader
USER_AGENT='CareWatchNY-ResearchPrototype/1.0 (public financial-assistance policy monitor)'
TOPICS=[('Income eligibility',r'(?:400\s*%|400\s*percent|four hundred percent|federal poverty)'),('Installment payments',r'(?:5\s*%|five percent|installment)'),('Application timeframe',r'(?:\b240\b|\b120\b|deadline|time limit|days (?:after|from))'),('Primary service area',r'(?:primary service area|count(?:y|ies))'),('Language access',r'(?:Spanish|Chinese|Bengali|translation|translated|language assistance)')]
class UnsafeUrl(ValueError):pass
def validate_url(url,allowed_hosts):
 p=urllib.parse.urlsplit(url)
 if p.scheme!='https' or p.username or p.password or p.port not in (None,443):raise UnsafeUrl('Only public HTTPS sources are allowed')
 host=(p.hostname or '').lower().rstrip('.')
 if host not in allowed_hosts:raise UnsafeUrl('Source host is outside this hospital’s approved source host')
 addresses=socket.getaddrinfo(host,443,type=socket.SOCK_STREAM)
 if not addresses or any(not ipaddress.ip_address(a[4][0]).is_global for a in addresses):raise UnsafeUrl('Private or reserved source address blocked')
 return url
class SafeRedirect(urllib.request.HTTPRedirectHandler):
 def __init__(self,hosts):self.hosts=hosts
 def redirect_request(self,req,fp,code,msg,headers,newurl):
  validate_url(newurl,self.hosts)
  return super().redirect_request(req,fp,code,msg,headers,newurl)
def fetch(url,hosts,limit=2_000_000):
 validate_url(url,hosts)
 opener=urllib.request.build_opener(SafeRedirect(hosts),urllib.request.HTTPSHandler(context=ssl.create_default_context()))
 req=urllib.request.Request(url,headers={'User-Agent':USER_AGENT,'Accept':'text/html,application/pdf;q=0.9,*/*;q=0.5'})
 with opener.open(req,timeout=12) as response:
  content=response.read(limit+1)
  if len(content)>limit:raise ValueError('Document exceeds the configured size limit; manual review required')
  return content,dict(response.headers),response.geturl(),response.status
class Page(HTMLParser):
 def __init__(self):super().__init__();self.parts=[];self.links=[];self.skip=0;self.anchor=None
 def handle_starttag(self,tag,attrs):
  if tag in ('script','style','noscript','nav','footer'):self.skip+=1
  if tag in ('p','div','br','li','h1','h2','h3','td'):self.parts.append('\n')
  if tag=='a':
   a=dict(attrs);self.anchor={'href':a.get('href',''),'title':''}
 def handle_endtag(self,tag):
  if tag in ('script','style','noscript','nav','footer') and self.skip:self.skip-=1
  if tag=='a' and self.anchor:self.links.append(self.anchor);self.anchor=None
 def handle_data(self,text):
  if not self.skip:self.parts.append(text)
  if self.anchor:self.anchor['title']+=text
 def text(self):return re.sub(r'[ \t]+',' ',html.unescape(' '.join(self.parts))).strip()
def candidates(text,url,page=None):
 text=re.sub(r'\s+',' ',text)
 result=[]
 for topic,pattern in TOPICS:
  m=re.search(pattern,text,re.I)
  if m:
   start=max(0,m.start()-130);end=min(len(text),m.end()+220)
   result.append({'topic':topic,'quote':text[start:end].strip(),'url':url,**({'page':page} if page else {})})
 return result
def scan(url,approved_hosts=None):
 # Existing public source links may use http; attempt secure transport only.
 target=re.sub(r'^http:','https:',url,flags=re.I)
 host=urllib.parse.urlsplit(target).hostname.lower();hosts={host}
 # Allow the commonplace bare/www redirect, but never arbitrary domains.
 hosts.add(host[4:] if host.startswith('www.') else 'www.'+host)
 for extra in (approved_hosts or []):
  if re.fullmatch(r'[a-z0-9.-]+',extra):hosts.add(extra)
 robot=urllib.robotparser.RobotFileParser();robot.parse([])
 try:
  robot_url=urllib.parse.urlunsplit(('https',host,'/robots.txt','',''))
  body,_,_,_=fetch(robot_url,hosts,500_000)
  robot=urllib.robotparser.RobotFileParser();robot.parse(body.decode('utf-8','replace').splitlines())
  if not robot.can_fetch(USER_AGENT,target):return {'error':'Source robots.txt disallows this monitor; manual review required','manualReview':True,'candidates':[],'documents':[]},[]
 except urllib.error.HTTPError as e:
  if e.code in (401,403):return {'error':'Source robots.txt access denied; manual review required','manualReview':True,'candidates':[],'documents':[]},[]
 except Exception:
  # Conservative: an unreachable robots endpoint is not treated as permission.
  return {'error':'Unable to verify robots.txt; manual review required','manualReview':True,'candidates':[],'documents':[]},[]
 body,headers,final,status=fetch(target,hosts)
 parser=Page();parser.feed(body.decode('utf-8','replace'));text=parser.text()
 result={'url':url,'finalUrl':final,'httpStatus':status,'lastModified':headers.get('Last-Modified') or headers.get('last-modified'),'textLength':len(text),'candidates':candidates(text,final),'documents':[],'skippedDocuments':[],'manualReview':False}
 snapshots=[('page',body,'text/html')]
 private_passages=[{'quote':text[j:j+1000],'url':final,'page':None} for j in range(0,min(len(text),20000),1000)]
 hashes=[hashlib.sha256(text.encode()).hexdigest()]
 robots_cache={host:robot}
 def document_allowed(href):
  doc_host=urllib.parse.urlsplit(href).hostname
  if doc_host not in robots_cache:
   doc_robot=urllib.robotparser.RobotFileParser();doc_robot.parse([])
   try:
    rb,_,_,_=fetch('https://'+doc_host+'/robots.txt',hosts,500_000);doc_robot.parse(rb.decode('utf-8','replace').splitlines())
   except urllib.error.HTTPError as e:
    if e.code not in (404,410):return False
   except Exception:return False
   robots_cache[doc_host]=doc_robot
  return robots_cache[doc_host].can_fetch(USER_AGENT,href)
 seen=set()
 relevant=lambda link:bool(re.search(r'financial|assistance|charity|application|discount|(?:\bfap\b)',link['href']+' '+link['title'],re.I))
 for link in sorted(parser.links,key=lambda item:not relevant(item)):
  href=urllib.parse.urljoin(final,link['href']);href=urllib.parse.urldefrag(href)[0]
  if not re.search(r'\.pdf(?:\?|$)',href,re.I) or href in seen:continue
  seen.add(href)
  reason=('Not a financial-assistance document match' if not relevant(link) else 'External host needs manual approval' if urllib.parse.urlsplit(href).hostname not in hosts else 'Two-PDF per-scan limit reached' if len(result['documents'])>=2 else None)
  if reason:
   result['skippedDocuments'].append({'url':href,'title':link['title'].strip()[:200],'reason':reason+'; not retrieved'})
   continue
  doc={'url':href,'title':link['title'].strip()[:200] or 'Linked PDF'}
  try:
   if not document_allowed(href):raise ValueError('Document robots.txt disallows or cannot verify this monitor; manual review required')
   blob,_,_,_=fetch(href,hosts,8_000_000)
   if not blob.startswith(b'%PDF-'):raise ValueError('Source did not return a PDF; manual review required')
   reader=PdfReader(BytesIO(blob));doc['pages']=len(reader.pages)
   passages=[];pieces=[]
   for i,page in enumerate(reader.pages[:60]):
    t=(page.extract_text() or '')[:15000];pieces.append(t)
    private_passages.extend({'quote':t[j:j+1000],'url':href,'page':i+1} for j in range(0,len(t),1000))
    if len(passages)<8:passages.extend(candidates(t,href,i+1))
   doc['textLength']=sum(map(len,pieces));doc['manualReview']=doc['textLength']<100 or len(reader.pages)>60
   doc['contentHash']=hashlib.sha256(blob).hexdigest();hashes.append(doc['contentHash'])
   result['candidates'].extend(passages[:8]);snapshots.append((f'pdf-{len(result["documents"])}',blob,'application/pdf'))
  except Exception as e:doc['error']=safe_error(e);doc['manualReview']=True
  result['documents'].append(doc)
 result['candidates']=result['candidates'][:18]
 result['manualReview']=len(text)<100 or any(d.get('manualReview') for d in result['documents']) or any(not d['reason'].startswith('Not a financial-assistance') for d in result['skippedDocuments'])
 result['contentHash']=hashlib.sha256('|'.join(hashes).encode()).hexdigest()
 snapshots.append(('evidence-passages',json.dumps({'sourceHash':result['contentHash'],'passages':private_passages[:300]}).encode(),'application/json'))
 return result,snapshots
def safe_error(e):
 if isinstance(e,urllib.error.HTTPError):return f'HTTP {e.code}; manual source review required'
 if isinstance(e,urllib.error.URLError):return 'Network or TLS fetch failure; manual source review required'
 if isinstance(e,(ValueError,UnsafeUrl)):return str(e)[:200]
 return f'{type(e).__name__}; manual source review required'
