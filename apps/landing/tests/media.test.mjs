import test from 'node:test';
import assert from 'node:assert/strict';
import {promises as fs} from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import http from 'node:http';
import {buildLanding,digest} from '../scripts/build.mjs';
import {loadMediaSnapshot,localMediaPath,MAX_MEDIA_BYTES} from '../scripts/public-media.mjs';
import {createLandingServer} from '../scripts/serve.mjs';

const bytes=Buffer.concat([Buffer.from([0,0,0,24]),Buffer.from('ftypmp42'),Buffer.from('fixture for hashing and HTTP ranges, not playback')]);
async function fixture(t){
 const root=await fs.mkdtemp(path.join(os.tmpdir(),'economicon-landing-media-'));
 const mediaDirectory=path.join(root,'media');await fs.mkdir(mediaDirectory);
 const entry={name:'one.mp4',mimeType:'video/mp4',bytes:bytes.length,sha256:digest(bytes)};
 await fs.writeFile(path.join(mediaDirectory,entry.name),bytes);
 await fs.writeFile(path.join(mediaDirectory,'manifest.json'),JSON.stringify({version:1,files:[entry]}));
 t.after(async()=>{assert.equal(path.dirname(root),os.tmpdir());assert.ok(path.basename(root).startsWith('economicon-landing-media-'));await fs.rm(root,{recursive:true,force:true});});
 return {root,mediaDirectory,entry};
}
async function start(t,f){
 const directory=path.join(f.root,'dist');await buildLanding({outDir:directory,origin:''});
 const server=await createLandingServer({directory,mediaDirectory:f.mediaDirectory,runtimeConfig:{videoUrl:'/media/one.mp4',appUrl:'https://app.example.org/'}});
 await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
 t.after(()=>new Promise(resolve=>server.close(resolve)));
 return server.address().port;
}
function request(port,route,method='GET',headers={}){return new Promise((resolve,reject)=>{const req=http.request({host:'127.0.0.1',port,path:route,method,headers},res=>{const chunks=[];res.on('data',c=>chunks.push(c));res.on('end',()=>resolve({status:res.statusCode,headers:res.headers,body:Buffer.concat(chunks)}));});req.on('error',reject);req.end();});}
test('only the approved relative media form is accepted',()=>{
 for(const value of ['/media/one.mp4','/media/Presentation_2-final.mp4'])assert.equal(localMediaPath(value),value);
 for(const value of [null,'//host/media/one.mp4','/media/.mp4','/media/a.b.mp4','/media/../one.mp4','/media/a/b.mp4','/media/a%2fb.mp4','/media/a%2emp4','/media/one.mp4?q=1','/media/one.mp4#x','/media/one.MP4','/media/'+ 'a'.repeat(81)+'.mp4'])assert.equal(localMediaPath(value),null,String(value));
});
test('selected bytes are verified once, stay stable after host mutation and never expose another listed file',async t=>{
 const f=await fixture(t);const other={...f.entry,name:'two.mp4'};await fs.writeFile(path.join(f.mediaDirectory,'two.mp4'),bytes);
 await fs.writeFile(path.join(f.mediaDirectory,'manifest.json'),JSON.stringify({version:1,files:[f.entry,other]}));
 const port=await start(t,f);
 await fs.writeFile(path.join(f.mediaDirectory,'one.mp4'),'CHANGED');await fs.writeFile(path.join(f.mediaDirectory,'manifest.json'),'CHANGED');
 assert.deepEqual((await request(port,'/media/one.mp4')).body,bytes);
 assert.equal((await request(port,'/media/two.mp4')).status,404);
 assert.equal(await loadMediaSnapshot(f.mediaDirectory,'/media/one.mp4'),null);
});
test('GET, HEAD, open/suffix/clamped byte ranges and416 preserve exact bytes and lengths',async t=>{
 const f=await fixture(t),port=await start(t,f),length=bytes.length;
 const get=await request(port,'/media/one.mp4');assert.equal(get.status,200);assert.deepEqual(get.body,bytes);assert.equal(get.headers['content-type'],'video/mp4');assert.equal(get.headers['cache-control'],'no-store');assert.equal(get.headers['accept-ranges'],'bytes');assert.equal(get.headers['x-content-type-options'],'nosniff');
 for(const [range,start,end] of [['bytes=0-7',0,7],['bytes=8-',8,length-1],['bytes=-5',length-5,length-1],['bytes=0-999999999999999999999999',0,length-1],['bytes=-999999999999999999999999',0,length-1]]){
  const response=await request(port,'/media/one.mp4','GET',{range});assert.equal(response.status,206,range);assert.equal(response.headers['content-range'],`bytes ${start}-${end}/${length}`);assert.deepEqual(response.body,bytes.subarray(start,end+1));assert.equal(Number(response.headers['content-length']),end-start+1);
 }
 const head=await request(port,'/media/one.mp4','HEAD',{range:'bytes=0-7'});assert.equal(head.status,200);assert.equal(head.body.length,0);assert.equal(Number(head.headers['content-length']),length);assert.equal(head.headers['content-range'],undefined);
 for(const range of [`bytes=${length}-`,'bytes=7-2','bytes=-0','bytes=-','bytes=abc','bytes=999999999999999999999999-']){
  const response=await request(port,'/media/one.mp4','GET',{range});assert.equal(response.status,416,range);assert.equal(response.headers['content-range'],`bytes */${length}`);assert.equal(response.body.length,0);
 }
 for(const headers of [{range:'unknown=0-7'},{range:'bytes=0-2,5-7'},{range:'bytes=0-7','if-range':'"not-a-known-validator"'}])assert.equal((await request(port,'/media/one.mp4','GET',headers)).status,200);
 assert.equal((await request(port,'/media/one.mp4','POST')).status,405);
});
test('encoded paths, queries, traversal, manifests and private files are never media routes',async t=>{
 const f=await fixture(t),port=await start(t,f);
 for(const route of ['/media/','/media/manifest.json','/media/two.mp4','/media/one.mp4?q=1','/media/%6fne.mp4','/media/a/../one.mp4','/media/%2e%2e/app.js','/media/%2e%2e/.env','/media%2fone.mp4','/media/one.mp4/extra','/public-media/one.mp4','/scripts/public-media.mjs'])assert.equal((await request(port,route)).status,404,route);
});
test('bad hashes, sizes, MIME, schemas, duplicate names and oversized media disable only media',async t=>{
 const f=await fixture(t);
 const variants=[{...f.entry,sha256:'0'.repeat(64)},{...f.entry,bytes:bytes.length-1},{...f.entry,bytes:MAX_MEDIA_BYTES+1},{...f.entry,mimeType:'text/html'},{...f.entry,name:'../one.mp4'},{...f.entry,extra:'PRIVATE'}];
 for(const entry of variants){await fs.writeFile(path.join(f.mediaDirectory,'manifest.json'),JSON.stringify({version:1,files:[entry]}));assert.equal(await loadMediaSnapshot(f.mediaDirectory,'/media/one.mp4'),null);}
 for(const manifest of [{version:1,files:[f.entry,f.entry]},{version:1,files:[f.entry],secret:'PRIVATE'},{version:2,files:[f.entry]}]){await fs.writeFile(path.join(f.mediaDirectory,'manifest.json'),JSON.stringify(manifest));assert.equal(await loadMediaSnapshot(f.mediaDirectory,'/media/one.mp4'),null);}
 await fs.writeFile(path.join(f.mediaDirectory,'manifest.json'),'not JSON');
 const port=await start(t,f);assert.equal((await request(port,'/media/one.mp4')).status,404);assert.equal((await request(port,'/healthz')).status,200);const config=await request(port,'/runtime-config.js');assert.equal(config.status,200);assert.match(config.body.toString(),/app.example.org/);assert.equal(config.headers['cache-control'],'no-store');
});
test('unapproved magic, missing file and oversized sparse input fail closed before allocation',async t=>{
 const f=await fixture(t);await fs.writeFile(path.join(f.mediaDirectory,'one.mp4'),Buffer.alloc(bytes.length));assert.equal(await loadMediaSnapshot(f.mediaDirectory,'/media/one.mp4'),null);
 await fs.unlink(path.join(f.mediaDirectory,'one.mp4'));assert.equal(await loadMediaSnapshot(f.mediaDirectory,'/media/one.mp4'),null);
 const handle=await fs.open(path.join(f.mediaDirectory,'one.mp4'),'w');await handle.truncate(MAX_MEDIA_BYTES+1);await handle.close();assert.equal(await loadMediaSnapshot(f.mediaDirectory,'/media/one.mp4'),null);
});
test('symlink file, manifest and directory are rejected (Linux review runtime)',{skip:process.platform==='win32'?'File symlink creation requires host privilege; run unchanged in Linux container':false},async t=>{
 const f=await fixture(t);const outside=path.join(f.root,'outside.mp4');await fs.rename(path.join(f.mediaDirectory,'one.mp4'),outside);await fs.symlink(outside,path.join(f.mediaDirectory,'one.mp4'));assert.equal(await loadMediaSnapshot(f.mediaDirectory,'/media/one.mp4'),null);
 await fs.unlink(path.join(f.mediaDirectory,'one.mp4'));await fs.rename(outside,path.join(f.mediaDirectory,'one.mp4'));await fs.rename(path.join(f.mediaDirectory,'manifest.json'),path.join(f.root,'outside.json'));await fs.symlink(path.join(f.root,'outside.json'),path.join(f.mediaDirectory,'manifest.json'));assert.equal(await loadMediaSnapshot(f.mediaDirectory,'/media/one.mp4'),null);
 const link=path.join(f.root,'directory-link');await fs.symlink(f.mediaDirectory,link);assert.equal(await loadMediaSnapshot(link,'/media/one.mp4'),null);
});
