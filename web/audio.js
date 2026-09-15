import {sounding,midi,Q,beatTicks,beatCount,keyInfo,tonicMidi} from './domain.js';
export const INSTRUMENTS=['piano','flute','clarinet'];
export function chooseInstrument(mode,previous,random=Math.random){const choices=INSTRUMENTS.filter(x=>x!==previous);return mode==='mixed'?choices[Math.floor(random()*choices.length)]:INSTRUMENTS.includes(mode)?mode:'piano';}
const ROOTS=[48,54,60,66,72,78,84,90,96];let pianoPromise;
export function loadPiano(){return pianoPromise??=(Promise.all(ROOTS.map(async root=>{
 const response=await fetch(new URL('./piano/'+root+'.pcm',import.meta.url));if(!response.ok)throw Error('Piano samples are unavailable. Connect once to cache the instrument.');
 const view=new DataView(await response.arrayBuffer()),data=new Float32Array(view.byteLength/2);let peak=0;for(let i=0;i<data.length;i++){data[i]=view.getInt16(i*2,true)/32768;peak=Math.max(peak,Math.abs(data[i]));}if(!peak)throw Error('Empty piano sample.');for(let i=0;i<data.length;i++)data[i]*=.7/peak;
 return [root,data];
})).then(rows=>Object.fromEntries(rows)).catch(error=>{pianoPromise=null;throw error;}));}
export function schedule(score,support='countin'){
 const beat=60/score.bpm,reference=score.reference||'none',referenceNotes=reference==='chord'?keyInfo(score).chord:reference==='pitch'?[tonicMidi(score)]:reference==='first'?[midi(score.events.find(e=>!e.rest&&e.step!==null)||{rest:true})??tonicMidi(score)]:[],referenceLength=referenceNotes.length?1.8:0;
 const count=beatCount(score),unit=beatTicks(score),lead=referenceLength+(support==='none'?0:count*beat),notes=sounding(score.events).filter(e=>!e.rest&&midi(e)!==null&&e.duration>0).map(e=>({time:lead+e.onset/unit*beat,duration:e.duration/unit*beat,midi:midi(e)})),clicks=[];
 if(support!=='none')for(let i=0;i<count;i++)clicks.push({time:referenceLength+i*beat,accent:i===0});
 const divisions=support==='subdivision'?(score.meter==='6/8'?3:2):1;if(['subdivision','beat','dropout'].includes(support))for(let k=0;k<score.bars*count*divisions;k++){const t=k/divisions;if(support!=='dropout'||t<2)clicks.push({time:lead+t*beat,accent:k%(count*divisions)===0});}
 return {notes,referenceNotes:referenceNotes.map(midi=>({midi,time:0,duration:1.2,gain:referenceNotes.length===3?.5:.8})),clicks,length:lead+score.bars*count*beat+.15};
}
export function render(score,support='countin',rate=44100,piano=null){
 const plan=schedule(score,support),out=new Float32Array(Math.ceil(plan.length*rate)),instrument=score.instrument||'piano';
 if(instrument==='piano'&&!piano)throw Error('Load piano samples before rendering.');
 for(const e of [...plan.referenceNotes,...plan.notes]){
  const start=Math.round(e.time*rate),n=Math.floor(e.duration*rate),f=440*2**((e.midi-69)/12),gain=e.gain??1;
  if(instrument==='piano'){
   const root=ROOTS.reduce((best,r)=>Math.abs(r-e.midi)<Math.abs(best-e.midi)?r:best),data=piano[root],ratio=22050/rate*2**((e.midi-root)/12);
   for(let i=0;i<n;i++){const pos=i*ratio,index=Math.floor(pos);if(index+1>=data.length)break;const wave=data[index]+(data[index+1]-data[index])*(pos-index),release=Math.min(1,(n-i)/Math.max(1,.018*rate));out[start+i]+=.6*gain*wave*release;}
  }else{
   const harmonics=instrument==='clarinet'?[1,.03,.55,.02,.25,.01,.1]:[1,.16,.06,.02],attack=instrument==='clarinet'?.015:.025;
   for(let i=0;i<n;i++){const t=i/rate,envelope=Math.min(1,t/attack)*Math.min(1,(e.duration-t)/.02);let wave=0;for(let h=1;h<=harmonics.length;h++)if(f*h<rate/2)wave+=harmonics[h-1]*Math.sin(2*Math.PI*f*h*t);out[start+i]+=.19*gain*wave*envelope;}
  }
 }
 for(const c of plan.clicks){const start=Math.round(c.time*rate);for(let i=0;i<Math.floor(.035*rate);i++){const t=i/rate;out[start+i]+=.16*Math.sin(2*Math.PI*(c.accent?1500:1100)*t)*Math.exp(-120*t);}}
 for(let i=0;i<out.length;i++)out[i]=Math.max(-.95,Math.min(.95,out[i]));return out;
}
export async function wav(score,support){const piano=(score.instrument||'piano')==='piano'?await loadPiano():null;const pcm=render(score,support,44100,piano),buffer=new ArrayBuffer(44+pcm.length*2),d=new DataView(buffer),str=(p,s)=>[...s].forEach((c,i)=>d.setUint8(p+i,c.charCodeAt(0)));str(0,'RIFF');d.setUint32(4,36+pcm.length*2,true);str(8,'WAVE');str(12,'fmt ');d.setUint32(16,16,true);d.setUint16(20,1,true);d.setUint16(22,1,true);d.setUint32(24,44100,true);d.setUint32(28,88200,true);d.setUint16(32,2,true);d.setUint16(34,16,true);str(36,'data');d.setUint32(40,pcm.length*2,true);pcm.forEach((x,i)=>d.setInt16(44+i*2,Math.round(x*32767),true));return new Blob([buffer],{type:'audio/wav'});}
export class Player{
 constructor(){this.volume=.7;this.gain=null;this.generation=0;this.context=null;this.source=null;this.onInterrupt=()=>{};}
 async play(score,support,onEnd){
  this.stop();const generation=this.generation;const Audio=globalThis.AudioContext||globalThis.webkitAudioContext;if(!Audio)throw Error('This browser does not support Web Audio.');
  if(!this.context){this.context=new Audio();this.context.onstatechange=()=>{if(this.source&&this.context.state!=='running')this.onInterrupt();};}
  await this.context.resume();if(generation!==this.generation)return;if(this.context.state!=='running')throw Error('Audio is paused. Tap Hear phrase again after enabling sound.');
  const piano=(score.instrument||'piano')==='piano'?await loadPiano():null;if(generation!==this.generation)return;const data=render(score,support,this.context.sampleRate,piano),buffer=this.context.createBuffer(1,data.length,this.context.sampleRate);buffer.copyToChannel(data,0);
  const source=this.context.createBufferSource();source.buffer=buffer;const gain=this.context.createGain();gain.gain.value=this.volume;this.gain=gain;source.connect(gain);gain.connect(this.context.destination);source.onended=()=>gain.disconnect();this.source=source;
  source.onended=()=>{if(this.source===source){this.source=null;source.disconnect();gain.disconnect();onEnd?.();}};source.start();
 }
 stop(){this.generation++;if(this.gain){this.gain.disconnect();this.gain=null;}if(this.source){const old=this.source;this.source=null;old.onended=null;try{old.stop();}catch{}old.disconnect();}}
}
