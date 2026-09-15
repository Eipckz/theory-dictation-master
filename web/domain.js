// Exact integer score time: 12 ticks per quarter; a sixteenth is 3 ticks.
export const VERSION='0.2.0';
export const Q=12;
export const LEVELS=['One-pitch durations','Two-pitch rhythm bridge','Three-pitch integration','Eighth-note division','Wider pitch landmarks','Dotted values and rests','Sixteenth-note cells'];
export const DURATIONS=[['Whole',48],['Half',24],['Quarter',12],['Eighth',6],['Sixteenth',3],['Unknown',null]];
export const clone=x=>JSON.parse(JSON.stringify(x));
export const midi=e=>e.rest||e.step===null?null:12*(Math.floor(e.step/7)+1)+[0,2,4,5,7,9,11][e.step%7]+e.acc;
export const name=e=>e.rest?'Rest':e.step===null?'Pitch ?':'CDEFGAB'[e.step%7]+({'-1':'♭',0:'',1:'♯'}[e.acc])+Math.floor(e.step/7);
export function reflow(events){let t=0;return events.map(e=>{const result={...e,onset:t};t+=e.duration??Q;return result;});}
export function sequence(durations,steps,extra={}){return {seed:0,level:0,bpm:80,bars:1,meter:'4/4',version:VERSION,...extra,events:reflow(durations.map((d,i)=>({duration:d,step:steps[i]===-1?null:steps[i],acc:0,rest:steps[i]===-1,tie:false})))};}
export function random(seed){let a=seed>>>0;return()=>{a+=0x6D2B79F5;let t=a;t=Math.imul(t^t>>>15,t|1);t^=t+Math.imul(t^t>>>7,t|61);return((t^t>>>14)>>>0)/4294967296;};}
export function generate(seed,level=0,bpm=80,bars=1){
 const rng=random(seed),pick=a=>a[Math.floor(rng()*a.length)];let bank=[[12],[24]];
 if(level>=3)bank.push([6,6]);if(level>=5)bank.push([36],[18,6]);if(level>=6)bank.push([3,3,3,3],[6,3,3],[3,3,6],[3,6,3],[9,3],[3,9]);
 const pitches=level===0?[28]:level===1?[28,29]:level<=3?[28,29,30]:[28,29,30,31,32];let step=28,events=[];
 for(let b=0;b<bars;b++){let left=48;while(left){const cell=pick(bank.filter(c=>c.reduce((s,x)=>s+x,0)<=left));for(const duration of cell){if(level)step=pick(pitches.filter(s=>Math.abs(s-step)<=(level>=4?2:1)));const rest=events.length>0&&rng()<.18;events.push({duration,step:rest?null:step,acc:0,rest,tie:false});left-=duration;}}}
 return {seed,level,bpm,bars,meter:'4/4',version:VERSION,events:reflow(events)};
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
 if(t!==score.bars*48)issues.push(`Your entry has ${t/Q} quarter-note units; this phrase needs ${score.bars*4}.`);
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
 const notation=answer.events.length>0&&answer.events.every(e=>e.duration!==null&&Math.floor(e.onset/48)===Math.floor((e.onset+e.duration-1)/48))?1:0;
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
export const comparable=a=>JSON.stringify([a.target.level,a.target.bpm,a.target.bars,a.policy.mode,a.policy.support,a.policy.hearings,a.policy.rhythmOnly]);
export function progression(attempts,current){const seen=new Set(),rows=attempts.filter(a=>{if(!independent(a)||comparable(a)!==comparable(current)||seen.has(a.fingerprint))return false;seen.add(a.fingerprint);return true;});const pass=a=>Math.min(a.result.attacks,a.result.durations,a.result.pitch??1)>=.9,last=rows.slice(-16);return {count:rows.length,action:last.length===16&&[0,8].every(i=>last.slice(i,i+8).filter(pass).length>=7)?'advance':rows.length>=5&&rows.slice(-5).reduce((s,a)=>s+a.result.integrated,0)/5<.7?'support':'consolidate'};}
export function validateScore(s){
 if(!s||s.meter!=='4/4'||!Number.isInteger(s.bars)||s.bars<1||s.bars>4||!Number.isInteger(s.level)||s.level<0||s.level>6||!Number.isFinite(s.bpm)||s.bpm<40||s.bpm>160||!Array.isArray(s.events)||s.events.length>128)throw Error('Invalid score in backup.');
 for(const e of s.events){if(!Number.isInteger(e.onset)||e.onset<0||e.onset>1536||(e.duration!==null&&(!Number.isInteger(e.duration)||e.duration<1||e.duration>72))||(e.step!==null&&(!Number.isInteger(e.step)||e.step<21||e.step>49))||![-1,0,1].includes(e.acc)||typeof e.rest!=='boolean'||typeof e.tie!=='boolean')throw Error('Invalid note in backup.');}
 return s;
}
