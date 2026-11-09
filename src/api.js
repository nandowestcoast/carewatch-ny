export async function getData(name){
 const r=await fetch(`/api/${name}`,{cache:'no-store'});if(!r.ok)throw Error('Unable to load project data. Please try again.');return r.json();
}
export async function localRuntime(){try{const r=await fetch('/api/runtime',{cache:'no-store'});if(!r.ok)return {mode:'hosted-readonly',aiEnabled:false};return await r.json();}catch{return {mode:'hosted-readonly',aiEnabled:false};}}
export function downloadJson(value,filename){const url=URL.createObjectURL(new Blob([JSON.stringify(value,null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download=filename;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
