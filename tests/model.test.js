import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {filterHospitals,toCsv,safeUrl} from '../src/model.js';
const {hospitals}=JSON.parse(fs.readFileSync(new URL('../public/data/baseline.json',import.meta.url)));
test('baseline import preserves 212 reviews and the 14 supplied A grades',()=>{assert.equal(hospitals.length,212);assert.equal(hospitals.filter(h=>h.grade==='A').length,14);assert.equal(new Set(hospitals.map(h=>h.id)).size,212);});
test('search and composed filters return only matching hospitals',()=>{const results=filterHospitals(hospitals,{query:'albany',grade:'D'});assert.ok(results.length>0);assert.ok(results.every(h=>h.grade==='D'&&[h.name,h.city,h.system].join(' ').toLowerCase().includes('albany')));assert.equal(filterHospitals(hospitals,{query:'nothingmatches98765'}).length,0);});
test('missing information is never coerced to a failed check',()=>{const checks=hospitals.flatMap(h=>h.checks);assert.ok(checks.some(c=>c.status==='na'));for(const c of checks.filter(c=>c.raw==='N/A'))assert.equal(c.status,'na');});
test('CSV safely quotes commas, quotes, and formula-like values',()=>{const csv=toCsv([{name:'=IMPORTDATA("bad")',city:'A,B',county:'C',system:'@bad',grade:'N/A',noncompliantCount:0,languages:[],assistanceUrl:'https://example.org'}]);assert.ok(csv.includes('"\'=IMPORTDATA(""bad"")"'));assert.ok(csv.includes('"A,B"'));assert.ok(csv.includes('"\'@bad"'));});
test('only browser-safe external source URLs can be linked',()=>{assert.equal(safeUrl('javascript:alert(1)'),null);assert.equal(safeUrl('data:text/html,test'),null);assert.equal(safeUrl('https://example.org/'),'https://example.org/');});

test('all 212 source links resolve to underlying web URLs, including rich-text hyperlinks',()=>{assert.ok(hospitals.every(h=>safeUrl(h.assistanceUrl)));assert.equal(new Set(hospitals.map(h=>h.assistanceUrl)).size,92);});
