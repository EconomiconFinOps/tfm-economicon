import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import vm from 'node:vm';
import {appRoot} from '../scripts/build.mjs';
import path from 'node:path';

const source=await readFile(path.join(appRoot,'src/app.js'),'utf8');
const start=source.indexOf('function setupSignalLoop(){'),end=source.indexOf('const syncSignalMotion=setupSignalLoop();');
assert.ok(start>=0&&end>start,'exercise the production controller, without a second implementation');
const controller=source.slice(start,end);
function fixture({width=1920,mobile=false,reduced=false,animate=true,observe=true}={}){
 const state={width,mobile,copies:[],animations:[],reduced,paused:false,observer:null,mediaChange:null};
 const classes=new Set(['signal-static']);
 const group={getBoundingClientRect:()=>({width:state.mobile?861:996}),cloneNode:()=>{
  const attrs=new Map();const copy={dataset:{},attrs,idRemoved:false,setAttribute:(k,v)=>attrs.set(k,v),querySelectorAll:()=>[{removeAttribute:k=>{if(k==='id')copy.idRemoved=true;}}],remove:()=>{state.copies.splice(state.copies.indexOf(copy),1);}};return copy;
 }};
 const section={getBoundingClientRect:()=>({width:state.width})};
 const track={querySelector:()=>group,closest:()=>section,querySelectorAll:()=>state.copies.slice(),append:copy=>state.copies.push(copy),classList:{toggle:(k,on)=>on?classes.add(k):classes.delete(k)},animate:animate?(frames,timing)=>{
  const a={frames,timing,currentTime:0,playState:'running',pause(){this.playState='paused';},play(){this.playState='running';},cancel(){this.playState='idle';}};state.animations.push(a);return a;
 }:undefined};
 const media={get matches(){return state.reduced;},addEventListener:(event,callback)=>{assert.equal(event,'change');state.mediaChange=callback;}};
 const context=vm.createContext({document:{querySelector:()=>track,body:{classList:{contains:()=>state.paused}}},matchMedia:()=>media,getComputedStyle:()=>({columnGap:'18px'}),ResizeObserver:observe?class{constructor(fn){state.observer=fn;}observe(){}}:undefined});
 vm.runInContext(controller+'\nglobalThis.sync=setupSignalLoop();',context);
 return {state,classes,sync:()=>context.sync(),resize:()=>state.observer(),animation:()=>state.animations.at(-1)};
}
function physicalCoverage(f,phase){
 const period=Math.abs(Number(/-([\d.]+)px/.exec(f.animation().frames[1].transform)[1]));
 const card=f.state.mobile?275:320,rects=[];
 for(let group=0;group<=f.state.copies.length;group++)for(let index=0;index<3;index++)rects.push({left:group*period+index*(card+18)-phase*period,right:group*period+index*(card+18)+card-phase*period});
 const visible=rects.filter(r=>r.right>0&&r.left<f.state.width);
 assert.ok(visible[0].left<=18,'no blank leading edge beyond the designed gap');
 assert.ok(visible.at(-1).right>=f.state.width-18,'no empty trailing viewport');
 for(let i=1;i<visible.length;i++)assert.ok(visible[i].left-visible[i-1].right<=18.001,'only the designed card gap');
 assert.ok(rects.at(-1).right>=f.state.width+period-18,'one full sequence remains outside the viewport');
}
test('all requested widths remain covered through the whole period with decorative, inert copies',()=>{
 for(const width of [320,390,1920,2560,3440]){
  const f=fixture({width,mobile:width<=600});
  for(const phase of [0,.25,.5,.75,.999999])physicalCoverage(f,phase);
  assert.ok(f.state.copies.every(c=>c.attrs.get('aria-hidden')==='true'&&c.attrs.has('inert')&&c.idRemoved));
 }
});
test('growing and shrinking viewport reuses phase and speed without accumulating copies',()=>{
 const f=fixture();const a=f.animation();a.currentTime=12345;
 const small=f.state.copies.length;f.state.width=3440;f.resize();assert.equal(f.animation(),a);assert.equal(a.currentTime,12345);assert.ok(f.state.copies.length>small);physicalCoverage(f,.999999);
 f.state.width=1920;f.resize();assert.equal(f.state.copies.length,small);assert.equal(f.animation(),a);assert.equal(a.currentTime,12345);
});
test('responsive card-width changes preserve sequence phase and constant pixels per second',()=>{
 const f=fixture();const before=f.animation();before.currentTime=before.timing.duration*.9;
 f.state.width=390;f.state.mobile=true;f.resize();const after=f.animation();assert.equal(before.playState,'idle');assert.ok(Math.abs(after.currentTime/after.timing.duration-.9)<1e-9);
 const distance=a=>Math.abs(Number(/-([\d.]+)px/.exec(a.frames[1].transform)[1]));
 assert.ok(Math.abs(distance(before)/before.timing.duration-distance(after)/after.timing.duration)<1e-9);physicalCoverage(f,.9);
});
test('pause and resume keep the same animation and current position, including resize',()=>{
 const f=fixture();const a=f.animation();a.currentTime=12345;f.state.paused=true;f.sync();assert.equal(a.playState,'paused');
 f.state.width=3440;f.resize();assert.equal(f.animation(),a);assert.equal(a.currentTime,12345);assert.equal(a.playState,'paused');
 f.state.paused=false;f.sync();assert.equal(a.playState,'running');assert.equal(a.currentTime,12345);
});
test('reduced motion stays static and changing preference removes copies without overriding user pause',()=>{
 const f=fixture({reduced:true});assert.equal(f.state.animations.length,0);assert.equal(f.state.copies.length,0);assert.ok(f.classes.has('signal-static'));
 f.state.reduced=false;f.state.mediaChange();assert.ok(f.state.copies.length>0);
 const a=f.animation();f.state.reduced=true;f.state.mediaChange();assert.equal(a.playState,'idle');assert.equal(f.state.copies.length,0);
 f.state.paused=true;f.state.reduced=false;f.state.mediaChange();assert.equal(f.animation().playState,'paused');
});
test('missing animation or resize support falls back to the static semantic sequence',()=>{
 for(const options of [{animate:false},{observe:false}]){const f=fixture(options);assert.ok(f.classes.has('signal-static'));assert.equal(f.state.copies.length,0);assert.equal(f.state.animations.length,0);}
});
test('the document starts with one accessible sequence of three cards and a static no-script fallback',async()=>{
 const html=await readFile(path.join(appRoot,'src/index.html'),'utf8');
 assert.equal([...html.matchAll(/class="signal-group"/g)].length,1);
 assert.equal([...html.matchAll(/class="signal-card"/g)].length,3);
 assert.match(html,/class="signal-track signal-static"/);
});
