import {spawnSync} from 'node:child_process';
import {mkdirSync} from 'node:fs';
mkdirSync('public/downloads',{recursive:true});
const git=spawnSync('git',['archive','--format=zip','--prefix=carewatch-ny/','--output=public/downloads/carewatch-source.zip','HEAD'],{stdio:'inherit'});if(git.status!==0){console.error('Commit the project first, after checking git status.');process.exit(git.status||1);}
const bundle=spawnSync('git',['bundle','create','public/downloads/carewatch-history.bundle','--all'],{stdio:'inherit'});if(bundle.status)process.exit(bundle.status);console.log('Source ZIP and Git history bundle created without ignored files.');
