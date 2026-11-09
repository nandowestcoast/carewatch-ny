import {readFile,writeFile,mkdir,rename,readdir} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import {join} from 'node:path';
import {createHash} from 'node:crypto';
import {importReviews,exportReviews,mergeReviews,createRubricDraft} from '../../src/workflow.js';
import {extractEvidence} from './ai.js';
const ROOT=fileURLToPath(new URL('../../',import.meta.url));
const DATA=join(ROOT,'public/data'),LOCAL=join(ROOT,'.local');
const headers={'Content-Type':'application/json','Cache-Control':'no-store','X-Content-Type-Options':'nosniff','X-Frame-Options':'DENY','Referrer-Policy':'no-referrer'};
const response=(statusCode,body)=>({statusCode,headers,body:JSON.stringify(body)});
let writing=Promise.resolve();
async function data(name){return JSON.parse(await readFile(join(DATA,name+'.json'),'utf8'));}
export async function handler(event){
 const path=event.rawPath,method=event.requestContext?.http?.method||'GET';
 try{
  if(method==='GET'&&['/api/baseline','/api/new-york','/api/monitor'].includes(path))return response(200,await data(path.slice(5)));
  if(method==='GET'&&path==='/api/runtime')return response(200,{mode:'local',aiEnabled:process.env.AI_ENABLED==='true',modelId:process.env.MODEL_ID||'us.amazon.nova-lite-v1:0',storage:'local files',sourcesPerAction:1,maxAttempts:3});
  if(method==='GET'&&path==='/api/rubric'){const b=await data('baseline');return response(200,createRubricDraft(b.hospitals[0]));}
  if(path==='/api/reviews'&&method==='GET'){try{return response(200,JSON.parse(await readFile(join(LOCAL,'reviews.json'),'utf8')));}catch{return response(200,exportReviews([]));}}
  if(path==='/api/reviews'&&method==='POST'){
   const baseline=await data('baseline');const records=importReviews(JSON.parse(event.body||''),baseline.hospitals);await mkdir(LOCAL,{recursive:true});
   const task=writing.catch(()=>{}).then(async()=>{let old=[];try{old=importReviews(JSON.parse(await readFile(join(LOCAL,'reviews.json'),'utf8')),baseline.hospitals);}catch{}const all=mergeReviews(old,records);if(all.length>5000)throw Error('Review limit reached. Export records before continuing.');const temp=join(LOCAL,'reviews.tmp');await writeFile(temp,JSON.stringify(exportReviews(all),null,2),{mode:0o600});await rename(temp,join(LOCAL,'reviews.json'));return all;});writing=task;
   return response(200,exportReviews(await task));
  }
  if(path==='/api/ai/extract'&&method==='POST'){
   const input=JSON.parse(event.body||'');if(typeof input.hospitalId!=='string'||input.confirmPublic!==true)throw Error('Choose a public hospital source and confirm it is public data.');
   const baseline=await data('baseline'),h=baseline.hospitals.find(h=>h.id===input.hospitalId);if(!h)throw Error('Unknown hospital.');const monitor=await data('monitor'),s=monitor.sources[h.assistanceUrl];if(!s||s.error)throw Error('This source needs a successful fetch before AI review.');
   let passages=[];const folder=join(LOCAL,'snapshots',createHash('sha256').update(h.assistanceUrl).digest('hex').slice(0,20));
   try{const versions=(await readdir(folder)).sort().reverse();for(const version of versions){const cached=JSON.parse(await readFile(join(folder,version,'evidence-passages.json'),'utf8'));if(cached.sourceHash===s.contentHash){passages=cached.passages.filter(p=>typeof p.quote==='string'&&/^https:\/\//.test(p.url));break;}}}catch{}
   return response(200,await extractEvidence(s,join(LOCAL,'ai-cache'),passages));
  }
  return response(404,{error:'Route unavailable in this mode.'});
 }catch(e){console.log(JSON.stringify({route:path,errorName:e.name}));return response(400,{error:e.code?'Local service could not complete the request. Check the server configuration.':e instanceof SyntaxError?'Invalid JSON request.':e.message.length<220?e.message:'Request could not be completed.'});}
}
