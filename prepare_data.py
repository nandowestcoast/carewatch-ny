import json,re,datetime
from pathlib import Path
root=Path(__file__).parent
rows=json.load(open(root/'inputs/review-values.json'))['values']
cells=json.load(open(root/'inputs/review-hyperlinks.json'))['sheets'][0]['data'][0]['rowData']
for i,cell in enumerate(cells):
 values=cell.get('values',[{}]);url=values[0].get('hyperlink')
 if url:rows[i+2][13]=url
zipcodes={}
for line in open(root/'inputs/ny-postcodes.tsv'):
 p=line.rstrip('\n').split('\t')
 if len(p)>=11 and p[4]=='NY':
  zipcodes[p[1]]={'county':p[5], 'lat':float(p[9]),'lon':float(p[10]),'city':p[2]}
criteria=[
 ('application',17,'Application available','Materials','The review checks whether patients can find a financial assistance application on the hospital website.'),
 ('summary',18,'Plain-language summary','Materials','The review checks whether a summary is posted as a PDF or on the financial assistance page.'),
 ('policy',19,'Policy statement','Materials','The review checks whether the financial assistance policy is publicly posted.'),
 ('consistent',20,'Consistent documents','Materials','The review checks whether the posted materials give patients consistent information.'),
 ('serviceArea',21,'Primary service area','Access','The review checks the primary service area against the applicable service-area guidance. Hospital location alone does not establish the service area.'),
 ('deadline',22,'No application deadline','Access','The review checks whether the hospital imposes a time limit on applications for financial assistance.'),
 ('assets',24,'No asset checks','Access','The review checks for asset checks or asset documentation barriers in the materials.'),
 ('immigration',25,'No immigration barrier','Access','The review checks whether immigration status is mentioned as a barrier to assistance.'),
 ('uniform',29,'Uniform application','Application','The review checks whether the complete New York uniform application is used.'),
 ('contact',30,'Contact information','Application','The review checks whether the application provides contact information for help.'),
 ('tables',32,'Income & discount tables','Application','The review checks whether the application includes income and discount tables.'),
 ('fpl',33,'2025 poverty guidelines','Application','This historical check asks whether the 2025 federal poverty guidelines were used. It is not a verification of the current-year guidelines.'),
 ('maxFpl',34,'At least 400% FPL','Application','The review checks whether the maximum stated income threshold reaches at least 400% of the federal poverty level. Individual eligibility must be confirmed with the hospital.'),
 ('installments',35,'Installments capped at 5%','Application','The review checks whether installment payments are capped at 5% of monthly income.'),
 ('areaSummary',37,'Service area in summary','Summary','The review checks whether the summary describes the primary service area.'),
 ('apply',38,'How to apply','Summary','The review checks whether the summary explains how to apply for assistance.'),
 ('income',39,'Income eligibility explained','Summary','The review checks whether the summary explains income levels used to determine assistance.')]
def value(r,i):return str(r[i]).strip() if len(r)>i and r[i] is not None else ''
hospitals=[]
for i,r in enumerate(rows[2:]):
 if not r or not r[0]:continue
 checks=[]
 for key,col,title,group,description in criteria:
  raw=value(r,col)
  if key=='maxFpl':
   match=re.search(r'(\d+(?:\.\d+)?)\s*%',raw)
   status=('yes' if float(match[1])>=400 else 'no') if match else 'na'
  else: status={'yes':'yes','no':'no','y':'yes','n':'no'}.get(raw.lower(),'na')
  checks.append({'key':key,'title':title,'group':group,'description':description,'status':status,'raw':raw or 'N/A'})
 z=zipcodes.get(value(r,6)[:5],{})
 h={'id':value(r,11) or f'hospital-{i+1}','name':value(r,0),'address':value(r,2),'city':value(r,3),'zip':value(r,6),'system':value(r,12) or 'Independent / not recorded','assistanceUrl':value(r,13),'grade':value(r,14) or 'N/A','automaticFail':value(r,15).lower()=='true','noncompliantCount':int(value(r,16)) if value(r,16).isdigit() else None,'languages':[s.strip() for s in re.split(r',|;',value(r,27)) if s.strip()] or [],'phone':value(r,31),'maxFpl':value(r,34) or 'N/A','checks':checks,'notes': [{'label':label,'text':value(r,col)} for col,label in [(23,'Application timeframe'),(26,'Document inconsistencies'),(28,'Review notes'),(36,'Application notes'),(40,'Summary notes'),(42,'Additional findings')] if value(r,col) and value(r,col).upper()!='N/A'],'serviceCounties':[],**z}
 h.setdefault('county','Not mapped')
 hospitals.append(h)
state=json.load(open(root/'us-states.json'))
ny=next(f for f in state['features'] if f['properties']['name']=='New York')
(root/'public/data/new-york.json').write_text(json.dumps(ny))
summary={'source':'CSSNY September 2025 manual review','sourceUrl':'https://docs.google.com/spreadsheets/d/17S2EheUVVr1g911fPpBQJqRpy18pkUlaEEnvGM0LB1o/edit','baselinePeriod':'September 2025','importedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'directoryUrl':'https://profiles.health.ny.gov/directory/hospitals','directoryCount':218,'sourceCount':len({h['assistanceUrl'] for h in hospitals if h['assistanceUrl'].startswith(('https://','http://'))}),'hospitalCount':len(hospitals),'locationSource':'GeoNames US postal-code dataset; ZIP-code centroids, not exact hospital coordinates','locationSourceUrl':'https://download.geonames.org/export/zip/','lawUrl':'https://newyork.public.law/laws/n.y._public_health_law_section_2807-k','rubric':'Grades are imported from CSSNY. The standalone grading rubric was not supplied, so the app does not recalculate grades.','hospitals':hospitals}
(root/'public/data/baseline.json').write_text(json.dumps(summary,ensure_ascii=False))
(root/'public/data/monitor.json').write_text(json.dumps({'updatedAt':None,'sources':{},'events':[],'mode':'Awaiting first scheduled scan'}))
print(f'Imported {len(hospitals)} hospital records; {sum("lat" in h for h in hospitals)} ZIP centroids; {len(set(h["assistanceUrl"] for h in hospitals if h["assistanceUrl"].startswith("https://")))} distinct source pages')
