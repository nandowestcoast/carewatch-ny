export const gradeColors={A:'#27785c',B:'#85a77c',C:'#d6af57',D:'#c77f55',F:'#b85959','N/A':'#9aa6a0'};
export function filterHospitals(hospitals,{query='',grade='All grades',county='All counties',system='All systems',issue='All measures'}={}) {
 const q=query.trim().toLowerCase();
 return hospitals.filter(h=>(!q||[h.name,h.city,h.county,h.system,h.zip,...h.languages].join(' ').toLowerCase().includes(q))&&(grade==='All grades'||h.grade===grade)&&(county==='All counties'||h.county===county)&&(system==='All systems'||h.system===system)&&(issue==='All measures'||h.checks.some(c=>c.key===issue&&c.status==='no')));
}
export function safeCell(v){let s=String(v??'');if(/^[\s]*[=+@-]/.test(s))s="'"+s;return '"'+s.replaceAll('"','""')+'"';}
export function toCsv(hospitals){const headers=['Hospital','City','Location county','System','CSSNY September 2025 grade','Recorded issues','Languages','Financial assistance URL','Source period'];return [headers,...hospitals.map(h=>[h.name,h.city,h.county,h.system,h.grade,h.noncompliantCount,h.languages.join('; '),h.assistanceUrl,'September 2025'])].map(row=>row.map(safeCell).join(',')).join('\r\n');}
export function sourceFor(h,monitor){return monitor?.sources?.[h.assistanceUrl]||null;}
export function formatDate(v,withTime=false){if(!v)return 'Not checked yet';const d=new Date(v);return isNaN(d)?'N/A':new Intl.DateTimeFormat('en-US',{month:'short',day:'numeric',year:'numeric',...(withTime?{hour:'numeric',minute:'2-digit',timeZone:'America/New_York'}:{})}).format(d);}
export function safeUrl(s){try{const u=new URL(s);return ['https:','http:'].includes(u.protocol)?u.href:null;}catch{return null;}}
