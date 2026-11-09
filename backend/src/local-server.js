import http from 'node:http';
import {handler} from './handler.js';
const port=Number(process.env.API_PORT||8787);
async function serve(req,res){
 const origin=req.headers.origin;
 if(origin&&!['http://127.0.0.1:5173','http://localhost:5173',`http://127.0.0.1:${port}`].includes(origin)){res.writeHead(403);return res.end('Origin denied');}
 if(req.headers.host!==`127.0.0.1:${port}`&&req.headers.host!==`localhost:${port}`){res.writeHead(403);return res.end('Host denied');}
 if(req.method==='POST'&&!/^application\/json(?:;|$)/i.test(req.headers['content-type']||'')){res.writeHead(415);return res.end('JSON required');}
 let body='';for await(const chunk of req){body+=chunk;if(Buffer.byteLength(body)>4_000_000){res.writeHead(413);return res.end('Request too large');}}
 const result=await handler({version:'2.0',rawPath:new URL(req.url,`http://127.0.0.1:${port}`).pathname,requestContext:{http:{method:req.method}},body,headers:req.headers});res.writeHead(result.statusCode,result.headers);res.end(result.body);
}
const server=http.createServer((req,res)=>{serve(req,res).catch(()=>{if(!res.headersSent)res.writeHead(500,{'Content-Type':'application/json'});res.end(JSON.stringify({error:'Request could not be completed.'}));});});
server.listen(port,'127.0.0.1',()=>console.log(JSON.stringify({service:'carewatch-local-api',host:'127.0.0.1',port})));
