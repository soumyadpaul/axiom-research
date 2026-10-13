import {spawnSync} from 'node:child_process';
import {mkdirSync,writeFileSync,rmSync,readdirSync} from 'node:fs';
const out='.test-output';rmSync(out,{recursive:true,force:true});mkdirSync(out);writeFileSync(`${out}/package.json`,'{"type":"commonjs"}');
const files=readdirSync('tests').filter(x=>x.endsWith('.test.ts')).map(x=>`tests/${x}`);
const compile=spawnSync(process.execPath,['node_modules/typescript/bin/tsc','--module','commonjs','--moduleResolution','node','--target','es2022','--esModuleInterop','--skipLibCheck','--strict','--outDir',out,...files],{stdio:'inherit'});if(compile.status!==0)process.exit(compile.status??1);
const result=spawnSync(process.execPath,['--test',...files.map(x=>`${out}/${x.replace('.ts','.js')}`)],{stdio:'inherit'});process.exit(result.status??1);
