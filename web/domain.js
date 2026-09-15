// Exact integer score time: 12 ticks per quarter; a sixteenth is 3 ticks.
export const VERSION='1.1.0';
export const Q=12;
export const SCALES={major:[0,2,4,5,7,9,11],minor:[0,2,3,5,7,8,10],'harmonic minor':[0,2,3,5,7,8,11],'melodic minor':[0,2,3,5,7,9,11],dorian:[0,2,3,5,7,9,10],phrygian:[0,1,3,5,7,8,10],lydian:[0,2,4,6,7,9,11],mixolydian:[0,2,4,5,7,9,10],locrian:[0,1,3,5,6,8,10]};
const NATURAL=[0,2,4,5,7,9,11];
export const KEYS={};
for(const [scale,intervals] of Object.entries(SCALES))for(let letter=0;letter<7;letter++)for(const alter of [0,-1,1]){
 const label='CDEFGAB'[letter]+({'-1':'b',0:'',1:'#'}[alter])+' '+scale,tonic=28+letter,root=60+NATURAL[letter]+alter,acc={};
 intervals.forEach((interval,i)=>{const diatonic=letter+i;acc[diatonic%7]=root+interval-(60+NATURAL[diatonic%7]+12*Math.floor(diatonic/7));});
 KEYS[label]={tonic,acc,chord:[root,root+intervals[2],root+intervals[4]],scale};
}
export const METERS=Array.from({length:32},(_,i)=>[1,2,4,8,16].map(d=>(i+1)+'/'+d)).flat();
export function meterInfo(s){
 const meter=s.meter||'4/4';if(!METERS.includes(meter))throw Error('Choose a meter from 1 to 32 over 1, 2, 4, 8 or 16.');
 const [n,d]=meter.split('/').map(Number),base=48/d;let groups;
 if(s.grouping){if(typeof s.grouping!=='string'||!/^\d{1,2}(?:\+\d{1,2}){0,31}$/.test(s.grouping))throw Error('Use beat groups such as 2+2+3.');groups=s.grouping.split('+').map(Number);if(groups.some(x=>x<1)||groups.reduce((a,b)=>a+b,0)!==n)throw Error('Beat groups must add up to the meter numerator.');}
 else if(n>=6&&n%3===0)groups=Array(n/3).fill(3);
 else if(d>=8&&n>=5){groups=[];let left=n;while(left>3){groups.push(2);left-=2;}groups.push(left);}
 else groups=Array(n).fill(1);
 const uniform=groups.every(x=>x===groups[0]),unit=base*(uniform?groups[0]:1),pulses=[];let t=0;for(const g of groups){pulses.push(t);t+=g*base;}
 const names={3:'Sixteenth',6:'Eighth',9:'Dotted eighth',12:'Quarter',18:'Dotted quarter',24:'Half',36:'Dotted half',48:'Whole',72:'Dotted whole'};
 return {n,d,base,groups,unit,pulses,span:n*base,label:names[unit]||`${unit/Q} quarter-note units`,grouping:groups.join('+')};
}
export const barTicks=s=>meterInfo(s).span;
export const beatTicks=s=>meterInfo(s).unit;
export const beatCount=s=>meterInfo(s).groups.length;
export const beatIndex=(s,t)=>{const m=meterInfo(s),bar=Math.floor(t/m.span),within=t%m.span;return bar*m.groups.length+m.pulses.findLastIndex(x=>x<=within);};
export const tempoLabel=s=>meterInfo(s).label;
export const keyInfo=s=>KEYS[s.key||'C major'];
export const keyAcc=(s,step)=>keyInfo(s).acc[((step%7)+7)%7]||0;
export const tonicMidi=s=>keyInfo(s).chord[0];

export const LEVELS=['One-pitch durations','Two-pitch rhythm bridge','Three-pitch integration','Eighth-note division','Wider pitch landmarks','Dotted values and rests','Sixteenth-note cells'];
export const DURATIONS=[['Whole',48],['Half',24],['Quarter',12],['Eighth',6],['Sixteenth',3],['Unknown',null]];
export const clone=x=>JSON.parse(JSON.stringify(x));
export const midi=e=>e.rest||e.step===null?null:12*(Math.floor(e.step/7)+1)+[0,2,4,5,7,9,11][e.step%7]+e.acc;
export const name=e=>e.rest?'Rest':e.step===null?'Pitch ?':'CDEFGAB'[e.step%7]+({'-2':'♭♭','-1':'♭',0:'',1:'♯',2:'𝄪'}[e.acc])+Math.floor(e.step/7);
export function reflow(events){let t=0;return events.map(e=>{const result={...e,onset:t};t+=e.duration??Q;return result;});}
export function sequence(durations,steps,extra={}){return {seed:0,level:0,bpm:80,bars:1,meter:'4/4',version:VERSION,...extra,events:reflow(durations.map((d,i)=>({duration:d,step:steps[i]===-1?null:steps[i],acc:0,rest:steps[i]===-1,tie:false})))};}
export function random(seed){let a=seed>>>0;return()=>{a+=0x6D2B79F5;let t=a;t=Math.imul(t^t>>>15,t|1);t^=t+Math.imul(t^t>>>7,t|61);return((t^t>>>14)>>>0)/4294967296;};}
export function generate(seed,level=0,bpm=80,bars=1,options={}){
 const meter=options.meter||'4/4',key=options.key||'C major';if(!METERS.includes(meter)||!KEYS[key])throw Error('Choose a supported key and meter.');const settings={meter,key,...(options.grouping?{grouping:options.grouping}:{})},span=barTicks(settings);
 const rng=random(seed),pick=a=>a[Math.floor(rng()*a.length)];let bank=[[12],[24]];
 if(level>=3)bank.push([6,6]);if(level>=5)bank.push([36],[18,6]);if(level>=6)bank.push([3,3,3,3],[6,3,3],[3,3,6],[3,6,3],[9,3],[3,9]);
 if(meterInfo(settings).groups.every(g=>g===3)&&meterInfo(settings).base===6){bank=[[18],[36]];if(level>=3)bank.push([6,6,6],[12,6],[6,12]);if(level>=6)bank.push([3,3,6,6],[6,3,3,6]);}
 const pitches=level===0?[28]:level===1?[28,29]:level<=3?[28,29,30]:Array.from({length:level===6?8:level===5?6:5},(_,i)=>28+i);let step=28,events=[];
 for(let b=0;b<bars;b++){let left=span;while(left){const candidates=bank.filter(c=>c.reduce((s,x)=>s+x,0)<=left);const cell=pick(candidates.length?candidates:[[3]]);for(const duration of cell){if(level)step=pick(pitches.filter(s=>Math.abs(s-step)<=(level>=4?2:1)));const rest=events.length>0&&rng()<.18;events.push({duration,step:rest?null:step,acc:0,rest,tie:false});left-=duration;}}}
 const shift=KEYS[key].tonic-28;events=events.map(e=>e.rest?e:{...e,step:e.step+shift,acc:keyAcc(settings,e.step+shift)});
 return {seed,level,bpm,bars,meter,key,pitchRange:pitches.length,...(options.grouping?{grouping:options.grouping}:{}),version:VERSION,events:reflow(events)};
}
export const fingerprint=s=>JSON.stringify(s.events);
export function validate(score,rhythmOnly=false){
 const issues=[];let t=0;
 for(const [i,e] of score.events.entries()){
  if(e.onset!==t)issues.push('Gap or overlap in your sequence.');
  if(e.duration===null||(!e.rest&&e.step===null&&!rhythmOnly))issues.push('Resolve the incomplete note or duration.');
  t=e.onset+(e.duration??0);
  if(e.tie){const n=score.events[i+1];if(e.rest||midi(e)===null||!n||n.rest||midi(n)!==midi(e)||n.onset!==t)issues.push('A tie needs a following note of the same pitch.');}
 }
 if(t!==score.bars*barTicks(score))issues.push(`Your entry has ${t/Q} quarter-note units; this phrase needs ${score.bars*barTicks(score)/Q}.`);
 if(!score.events.length)issues.push('The answer is empty.');return [...new Set(issues)];
}
export function sounding(events){const out=[];for(let i=0;i<events.length;i++){let e=events[i],duration=e.duration??0,onset=e.onset;while(e.tie&&events[i+1]&&midi(e)!==null&&midi(e)===midi(events[i+1])&&events[i+1].onset===e.onset+(e.duration??0)){e=events[++i];duration+=e.duration??0;}out.push({...e,onset,duration,tie:false});}return out;}
export function align(a,b){
 const m=a.length,n=b.length,d=Array.from({length:m+1},()=>Array(n+1).fill(0)),w=Array.from({length:m+1},()=>Array(n+1).fill(1));
 for(let i=0;i<=m;i++)d[i][0]=i;for(let j=0;j<=n;j++)d[0][j]=j;
 for(let i=1;i<=m;i++)for(let j=1;j<=n;j++){const costs=[d[i-1][j-1]+(midi(a[i-1])!==midi(b[j-1])?1:0),d[i-1][j]+1,d[i][j-1]+1],best=Math.min(...costs);d[i][j]=best;w[i][j]=Math.min(2,[w[i-1][j-1],w[i-1][j],w[i][j-1]].reduce((s,x,k)=>s+(costs[k]===best?x:0),0));}
 return {edits:d[m][n],ambiguous:w[m][n]>1};
}
function overlap(a,b){const x=new Set(a),y=new Set(b);return 2*[...x].filter(v=>y.has(v)).length/Math.max(1,x.size+y.size);}
export function grade(target,answer,rhythmOnly=false){
 const t=sounding(target.events),a=sounding(answer.events),tn=t.filter(e=>!e.rest),an=a.filter(e=>!e.rest);
 const attacks=overlap(tn.map(e=>e.onset),an.map(e=>e.onset));
 const durations=overlap(t.map(e=>`${e.onset}/${e.duration}/${e.rest}`),a.map(e=>`${e.onset}/${e.duration}/${e.rest}`));
 const alignment=align(tn,an),pitch=rhythmOnly?null:Math.max(0,1-alignment.edits/Math.max(1,tn.length,an.length));
 const issues=validate(answer,rhythmOnly),complete=issues.length===0,integrated=complete?Math.min(attacks,durations,pitch??1):0;
 const notation=answer.events.length>0&&answer.events.every(e=>e.duration!==null&&Math.floor(e.onset/barTicks(answer))===Math.floor((e.onset+e.duration-1)/barTicks(answer)))?1:0;
 const missing=tn.find(e=>!an.some(x=>x.onset===e.onset)),extra=an.find(e=>!tn.some(x=>x.onset===e.onset));const feedback=[];
 if(missing)feedback.push(`Missing attack at quarter-note position ${missing.onset/Q} from the start. Keep the pulse and mark that attack.`);
 if(extra)feedback.push(`Extra attack at quarter-note position ${extra.onset/Q}. Check whether a note should sustain instead.`);
 if(attacks===1&&durations<1)feedback.push('Attacks line up. Check note releases, rests, and sustained lengths.');
 if(pitch!==null&&pitch<1)feedback.push(`Pitch sequence needs ${alignment.edits} edit(s). Retain your rhythm while checking contour and landmarks.`);
 if(alignment.ambiguous&&!rhythmOnly)feedback.push('Several pitch alignments fit. A precise note-by-note pitch diagnosis would be uncertain.');
 if(integrated===1)feedback.push('The assessed sound matches. Try a new phrase at the same settings.');
 return {attacks,durations,pitch,notation,integrated,complete,feedback,issues,ambiguous:alignment.ambiguous,version:VERSION};
}
export const independent=a=>a.kind==='independent'&&!a.assistance.length&&a.audioOK&&a.result?.complete;
export const comparable=a=>JSON.stringify([a.target.level,a.target.bpm,a.target.bars,a.policy.mode,a.policy.support,a.policy.hearings,a.policy.rhythmOnly,a.target.instrument||'piano',a.target.reference||'none',a.target.key||'C major',a.target.meter||'4/4',meterInfo(a.target).grouping,a.target.pitchRange??(a.target.level===0?1:a.target.level===1?2:a.target.level<=3?3:5)]);
export function progression(attempts,current){const seen=new Set(),rows=attempts.filter(a=>{if(!independent(a)||comparable(a)!==comparable(current)||seen.has(a.fingerprint))return false;seen.add(a.fingerprint);return true;});const pass=a=>Math.min(a.result.attacks,a.result.durations,a.result.pitch??1)>=.9,last=rows.slice(-16);return {count:rows.length,action:last.length===16&&[0,8].every(i=>last.slice(i,i+8).filter(pass).length>=7)?'advance':rows.length>=5&&rows.slice(-5).reduce((s,a)=>s+a.result.integrated,0)/5<.7?'support':'consolidate'};}
export function validateScore(s){
 if(!s||!METERS.includes(s.meter)||!KEYS[s.key||'C major']||!Number.isInteger(s.bars)||s.bars<1||s.bars>4||!Number.isInteger(s.level)||s.level<0||s.level>6||!Number.isFinite(s.bpm)||s.bpm<40||s.bpm>160||!Array.isArray(s.events)||s.events.length>2048)throw Error('Invalid score in backup.');
 meterInfo(s);if(s.pitchRange!==undefined&&(!Number.isInteger(s.pitchRange)||s.pitchRange<1||s.pitchRange>8))throw Error('Invalid pitch range.');if(s.instrument!==undefined&&!['piano','flute','clarinet'].includes(s.instrument))throw Error('Invalid instrument.');if(s.soundMode!==undefined&&!['piano','flute','clarinet','mixed'].includes(s.soundMode))throw Error('Invalid instrument mode.');if(s.reference!==undefined&&!['none','pitch','chord','first'].includes(s.reference))throw Error('Invalid tonal reference.');
 for(const e of s.events){if(!Number.isInteger(e.onset)||e.onset<0||e.onset>6144||(e.duration!==null&&(!Number.isInteger(e.duration)||e.duration<1||e.duration>72))||(e.step!==null&&(!Number.isInteger(e.step)||e.step<21||e.step>49))||![-2,-1,0,1,2].includes(e.acc)||typeof e.rest!=='boolean'||typeof e.tie!=='boolean')throw Error('Invalid note in backup.');}
 return s;
}
