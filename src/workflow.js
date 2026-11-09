export function isStale(source,now=Date.now()){const last=source?.lastSuccessfulAt||(!source?.error?source?.checkedAt:null);return !last||!Number.isFinite(Date.parse(last))||now-Date.parse(last)>26*3600000;}
export function monitoringHealth(hospitals,monitor,now=Date.now()){
 const urls=[...new Set(hospitals.map(h=>h.assistanceUrl).filter(u=>/^https?:/.test(u)))];
 const rows=urls.map(url=>({url,...(monitor.sources?.[url]||{})}));
 return {total:urls.length,attempted:rows.filter(s=>s.checkedAt).length,successful:rows.filter(s=>s.checkedAt&&!s.error).length,errors:rows.filter(s=>s.error).length,manual:rows.filter(s=>s.manualReview||s.error||s.changed).length,changed:rows.filter(s=>s.changed).length,stale:rows.filter(s=>isStale(s,now)).length};
}
export function citationId(c){return JSON.stringify([c.topic,c.url,c.page||null,c.quote]);}
export function validateReview(raw,hospitals){
 if(!raw||typeof raw!=='object'||Array.isArray(raw))throw Error('Invalid review record.');
 const h=hospitals.find(h=>h.id===raw.hospitalId);if(!h)throw Error('Unknown hospital in review file.');
 const string=(key,max,required=true)=>{const v=raw[key];if(typeof v!=='string'||v.length>max||(required&&!v.trim()))throw Error(`Invalid ${key}.`);return v.trim();};
 const record={id:string('id',100),hospitalId:h.id,sourceUrl:h.assistanceUrl,sourceHash:string('sourceHash',128),reviewer:string('reviewer',60),decision:string('decision',16),reason:string('reason',2000),reviewedAt:string('reviewedAt',50),criterion:string('criterion',60),evidenceUrl:string('evidenceUrl',2000),quote:string('quote',2000,false),page:raw.page??null,evidenceAt:string('evidenceAt',50),scope:'evidence-review',baselineUnchanged:true,synthetic:raw.synthetic===true||/^SYN-/.test(raw.reviewer)};
 if(!['confirm','reject','unclear'].includes(record.decision)||!h.checks.some(c=>c.key===record.criterion))throw Error('Invalid review decision or check.');
 if(!/^https:\/\//.test(record.evidenceUrl)||!Number.isFinite(Date.parse(record.reviewedAt))||!Number.isFinite(Date.parse(record.evidenceAt)))throw Error('Invalid citation or review date.');
 if(record.page!==null&&(!Number.isInteger(record.page)||record.page<1||record.page>10000))throw Error('Invalid PDF page.');
 return record;
}
export function importReviews(value,hospitals){
 if(!value||value.schemaVersion!==1||value.kind!=='carewatch-evidence-reviews'||!Array.isArray(value.records)||value.records.length>5000)throw Error('Use a CareWatch review export (up to 5,000 records).');
 return value.records.map(r=>validateReview(r,hospitals));
}
export function mergeReviews(a,b){return [...new Map([...a,...b].map(r=>[r.id,r])).values()].sort((x,y)=>y.reviewedAt.localeCompare(x.reviewedAt));}
export function exportReviews(records){return {schemaVersion:1,kind:'carewatch-evidence-reviews',exportedAt:new Date().toISOString(),records};}
export function effectiveEvidence(source){return source?.error?(source.lastGoodEvidence||null):source;}
export function hasCurrentReview(h,source,records){const e=effectiveEvidence(source);return !!e?.contentHash&&records.some(r=>r.hospitalId===h.id&&r.sourceHash===e.contentHash);}
export function createRubricDraft(hospital){return {schemaVersion:1,status:'awaiting-partner-approval',version:null,approvedBy:null,approvedAt:null,approvalSource:null,gradeThresholds:null,automaticFailRules:null,criteria:hospital.checks.map(({key,title,description})=>({key,title,description,legalCitation:null,weight:null})),note:'Checks imported from the historical spreadsheet. Not a legal rubric. Never calculate a current grade from this draft.'};}
