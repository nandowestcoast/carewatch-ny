// Explicit operator confirmation is required; only public, non-sensitive documents.
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import {basename,join} from 'node:path';
import {createHash} from 'node:crypto';
import {awsCall} from '../backend/src/ai.js';
const args=process.argv.slice(2);if(!args.includes('--public-document')||!args.find(a=>!a.startsWith('--'))){console.error('Usage: node scripts/ocr.mjs PUBLIC_FILE --public-document. Never use patient documents.');process.exit(1);}
const file=args.find(a=>!a.startsWith('--')),buffer=await readFile(file);if(buffer.length>5_000_000)throw Error('Use one public page under 5 MB.');
const isPdf=buffer.subarray(0,5).toString()==='%PDF-',isPng=buffer.subarray(0,8).equals(Buffer.from([137,80,78,71,13,10,26,10])),isJpeg=buffer[0]===255&&buffer[1]===216;
if(!isPdf&&!isPng&&!isJpeg)throw Error('Only PDF, PNG, or JPEG files are allowed. PDFs must be single-page; Textract also validates this.');
const key=createHash('sha256').update(buffer).digest('hex');const cache=join('.local','ocr-cache');await mkdir(cache,{recursive:true});const output=join(cache,key+'.json');try{await readFile(output);console.log(JSON.stringify({cached:true,output}));process.exit(0);}catch{}
const result=await awsCall('textract','detect-document-text',{Document:{Bytes:buffer.toString('base64')}},{binary:true});
const lines=(result.Blocks||[]).filter(b=>b.BlockType==='LINE').map(b=>({text:b.Text,page:b.Page||1,confidence:b.Confidence}));await writeFile(output,JSON.stringify({kind:'public-document-ocr',sourceFile:basename(file),sourceHash:key,lines,humanReviewRequired:true}),{mode:0o600});console.log(JSON.stringify({pageCount:result.DocumentMetadata?.Pages,lineCount:lines.length,output}));
