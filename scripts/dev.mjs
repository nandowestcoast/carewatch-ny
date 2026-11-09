import {spawn} from 'node:child_process';
const api=spawn(process.execPath,['backend/src/local-server.js'],{stdio:'inherit'});
const web=spawn(process.execPath,['node_modules/vite/bin/vite.js','--host','127.0.0.1'],{stdio:'inherit'});
function stop(){api.kill();web.kill();}process.on('SIGINT',stop);process.on('SIGTERM',stop);api.on('exit',()=>web.kill());web.on('exit',()=>api.kill());
