import {spawnSync} from 'node:child_process';
import {mkdir,readFile,writeFile} from 'node:fs/promises';
import {createRubricDraft} from '../src/workflow.js';
const result=spawnSync(process.execPath,['node_modules/vite/bin/vite.js','build'],{stdio:'inherit'});if(result.status!==0)process.exit(result.status||1);
await mkdir('dist/api',{recursive:true});for(const name of ['baseline','monitor','new-york'])await writeFile('dist/api/'+name,await readFile('dist/data/'+name+'.json'));
await writeFile('dist/api/runtime',JSON.stringify({mode:'hosted-readonly',aiEnabled:false,storage:'browser; export for sharing'}));
const data=JSON.parse(await readFile('dist/data/baseline.json','utf8'));await writeFile('dist/api/rubric',JSON.stringify(createRubricDraft(data.hospitals[0])));
