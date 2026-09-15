import {sounding,midi,Q} from './domain.js';
export function schedule(score,support='countin'){
 const beat=60/score.bpm,lead=support==='none'?0:4*beat,notes=sounding(score.events).filter(e=>!e.rest&&midi(e)!==null&&e.duration>0).map(e=>({time:lead+e.onset/Q*beat,duration:e.duration/Q*beat,midi:midi(e)})),clicks=[];
 if(lead)for(let i=0;i<4;i++)clicks.push({time:i*beat,accent:i===0});
 if(['subdivision','beat','dropout'].includes(support))for(let t=0;t<score.bars*4;t+=support==='subdivision'?.5:1)if(support!=='dropout'||t<2)clicks.push({time:lead+t*beat,accent:t%4===0});
 return {notes,clicks,length:lead+score.bars*4*beat+.15};
}
export function render(score,support='countin',rate=44100){
 const plan=schedule(score,support),out=new Float32Array(Math.ceil(plan.length*rate));
 for(const e of plan.notes){const start=Math.round(e.time*rate),n=Math.floor(e.duration*rate),f=440*2**((e.midi-69)/12);for(let i=0;i<n;i++){const t=i/rate,envelope=Math.min(1,t/.008)*Math.min(1,(e.duration-t)/.025)*(.65+.35*Math.exp(-3*t));let wave=0;for(let h=1;h<=4;h++)wave+=Math.sin(2*Math.PI*f*h*t)/(h*h);out[start+i]+=.23*wave*envelope;}}
 for(const c of plan.clicks){const start=Math.round(c.time*rate);for(let i=0;i<Math.floor(.035*rate);i++){const t=i/rate;out[start+i]+=.16*Math.sin(2*Math.PI*(c.accent?1500:1100)*t)*Math.exp(-120*t);}}
 for(let i=0;i<out.length;i++)out[i]=Math.max(-.95,Math.min(.95,out[i]));return out;
}
export function wav(score,support){const pcm=render(score,support),buffer=new ArrayBuffer(44+pcm.length*2),d=new DataView(buffer),str=(p,s)=>[...s].forEach((c,i)=>d.setUint8(p+i,c.charCodeAt(0)));str(0,'RIFF');d.setUint32(4,36+pcm.length*2,true);str(8,'WAVE');str(12,'fmt ');d.setUint32(16,16,true);d.setUint16(20,1,true);d.setUint16(22,1,true);d.setUint32(24,44100,true);d.setUint32(28,88200,true);d.setUint16(32,2,true);d.setUint16(34,16,true);str(36,'data');d.setUint32(40,pcm.length*2,true);pcm.forEach((x,i)=>d.setInt16(44+i*2,Math.round(x*32767),true));return new Blob([buffer],{type:'audio/wav'});}
export class Player{
 constructor(){this.generation=0;this.context=null;this.source=null;this.onInterrupt=()=>{};}
 async play(score,support,onEnd){
  this.stop();const generation=this.generation;const Audio=globalThis.AudioContext||globalThis.webkitAudioContext;if(!Audio)throw Error('This browser does not support Web Audio.');
  if(!this.context){this.context=new Audio();this.context.onstatechange=()=>{if(this.source&&this.context.state!=='running')this.onInterrupt();};}
  await this.context.resume();if(generation!==this.generation)return;if(this.context.state!=='running')throw Error('Audio is paused. Tap Hear phrase again after enabling sound.');
  const data=render(score,support,this.context.sampleRate),buffer=this.context.createBuffer(1,data.length,this.context.sampleRate);buffer.copyToChannel(data,0);
  const source=this.context.createBufferSource();source.buffer=buffer;source.connect(this.context.destination);this.source=source;
  source.onended=()=>{if(this.source===source){this.source=null;source.disconnect();onEnd?.();}};source.start();
 }
 stop(){this.generation++;if(this.source){const old=this.source;this.source=null;old.onended=null;try{old.stop();}catch{}old.disconnect();}}
}
