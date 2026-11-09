import test from 'node:test';
import assert from 'node:assert/strict';
import {handler} from '../backend/src/handler.js';
const event=(path,method='GET',body)=>({version:'2.0',rawPath:path,requestContext:{http:{method}},body:body?JSON.stringify(body):undefined});
test('local API serves baseline without cloud credentials',async()=>{const r=await handler(event('/api/baseline'));assert.equal(r.statusCode,200);assert.equal(JSON.parse(r.body).hospitals.length,212);assert.equal(r.headers['Referrer-Policy'],'no-referrer');});
test('local API keeps AI off by default and rubric unapproved',async()=>{const r=await handler(event('/api/runtime'));assert.equal(JSON.parse(r.body).aiEnabled,false);const rubric=await handler(event('/api/rubric'));assert.equal(JSON.parse(rubric.body).status,'awaiting-partner-approval');});
test('AI rejects unconfirmed inputs without making a model call',async()=>{const r=await handler(event('/api/ai/extract','POST',{hospitalId:'bad',confirmPublic:false}));assert.equal(r.statusCode,400);assert.match(JSON.parse(r.body).error,/public/);});
test('review import refuses an unknown schema',async()=>{const r=await handler(event('/api/reviews','POST',{records:[]}));assert.equal(r.statusCode,400);});
