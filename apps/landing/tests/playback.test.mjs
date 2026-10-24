import test from 'node:test';
import assert from 'node:assert/strict';
import {promises as fs} from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import {appRoot} from '../scripts/build.mjs';

function element(){
 const attrs=new Map(),listeners=new Map(),classes=new Set();
 return {textContent:'Reproducir vídeo',hidden:true,disabled:true,dataset:{},listeners,
  setAttribute:(k,v)=>attrs.set(k,v),getAttribute:k=>attrs.get(k),removeAttribute:k=>attrs.delete(k),
  addEventListener:(k,fn)=>listeners.set(k,fn),emit(k){return listeners.get(k)?.();},focus(){},querySelectorAll:()=>[],
  classList:{add:k=>classes.add(k),remove:k=>classes.delete(k),toggle:k=>classes.has(k)?(classes.delete(k),false):(classes.add(k),true),contains:k=>classes.has(k)}};
}
async function client(videoUrl,blocked=false){
 const selectors=['.theme-toggle','.menu-button','#mobile-nav','#motion-toggle','.app-destination','#app-error','#presentation-video','.presentation','#video-toggle','#video-state','#video-original'];
 const nodes=Object.fromEntries(selectors.map(key=>[key,element()]));
 const video=nodes['#presentation-video'];video.paused=true;video.calls=0;video.muted=false;
 video.play=()=>{video.calls++;if(blocked&&video.calls===1)return Promise.reject(new Error('NotAllowedError'));video.paused=false;video.emit('play');return Promise.resolve();};
 video.pause=()=>{video.paused=true;video.emit('pause');};
 const context=vm.createContext({document:{documentElement:{dataset:{}},body:element(),querySelector:key=>nodes[key],querySelectorAll:()=>[],addEventListener:()=>{}},localStorage:{getItem:()=>null,setItem:()=>{}},matchMedia:()=>({matches:false}),__LANDING_PUBLIC_CONFIG__:{videoUrl,appUrl:'https://app.example.org/'}});
 vm.runInContext(await fs.readFile(path.join(appRoot,'src/app.js'),'utf8'),context);
 await new Promise(resolve=>setImmediate(resolve));
 return {nodes,video};
}
test('autoplay rejection leaves a usable manual control; user pause is not undone by theme or loading events',async()=>{
 const {nodes,video}=await client('/media/one.mp4',true),toggle=nodes['#video-toggle'],state=nodes['#video-state'];
 assert.equal(video.calls,1);assert.equal(video.muted,true);assert.equal(video.paused,true);assert.equal(toggle.hidden,false);assert.equal(toggle.disabled,false);assert.equal(state.hidden,false);assert.match(state.textContent,/Pulsa Reproducir/);
 toggle.emit('click');await new Promise(resolve=>setImmediate(resolve));assert.equal(video.calls,2);assert.equal(video.paused,false);assert.equal(state.hidden,true);assert.equal(toggle.textContent,'Pausar vídeo');
 video.emit('loadeddata');assert.equal(nodes['.presentation'].classList.contains('media-loaded'),true);
 toggle.emit('click');assert.equal(video.paused,true);assert.equal(toggle.textContent,'Reproducir vídeo');
 nodes['.theme-toggle'].emit('click');video.emit('loadeddata');assert.equal(video.calls,2);assert.equal(video.paused,true);
});
test('media failure preserves the separate video link and application action with a useful error',async()=>{
 const {nodes,video}=await client('/media/one.mp4');video.error={code:4};video.emit('error');
 assert.equal(nodes['#video-toggle'].hidden,true);assert.equal(nodes['#video-state'].hidden,false);assert.match(nodes['#video-state'].textContent,/No se ha podido cargar/);
 assert.equal(nodes['#video-original'].href,'/media/one.mp4');assert.equal(nodes['#video-original'].hidden,false);assert.equal(nodes['.app-destination'].href,'https://app.example.org/');
});
test('missing media or external viewer URLs do not cause automatic third-party media loads',async()=>{
 for(const url of [null,'https://drive.google.com/file/d/approved/view']){
  const {nodes,video}=await client(url);assert.equal(video.calls,0);assert.equal(video.src,undefined);assert.equal(nodes['#video-toggle'].hidden,true);assert.equal(nodes['#video-state'].hidden,false);assert.equal(nodes['.app-destination'].href,'https://app.example.org/');
  if(url)assert.equal(nodes['#video-original'].href,url);
 }
});
