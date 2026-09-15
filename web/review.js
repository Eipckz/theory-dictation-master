import {independent,comparable,fingerprint,grade} from './domain.js';
export const REVIEW_DELAYS=[20*60e3,24*60*60e3,3*24*60*60e3];
export function evidenceGroups(attempts){
 const groups=new Map();
 for(const a of [...attempts].sort((x,y)=>x.created-y.created)){
  if(!independent(a))continue;const key=comparable(a),g=groups.get(key)||{key,rows:[],seen:new Set()};
  const fp=fingerprint(a.target);if(g.seen.has(fp))continue;g.seen.add(fp);g.rows.push(a);groups.set(key,g);
 }
 return [...groups.values()];
}
export function reviewPlan(attempts,now=Date.now()){
 return evidenceGroups(attempts).map(g=>{
  let stage=0,lastSuccess=null,due=now,status='Emerging';
  for(const a of g.rows){
   if(a.result.integrated<.9){stage=0;lastSuccess=null;status='Needs review';due=a.created+REVIEW_DELAYS[0];continue;}
   if(lastSuccess===null){lastSuccess=a.created;due=a.created+REVIEW_DELAYS[stage];}
   else if(a.created>=due){stage=Math.min(2,stage+1);lastSuccess=a.created;due=a.created+REVIEW_DELAYS[stage];}status=stage===2?'Retained in these conditions':stage===1?'Reliable today':'Emerging';
  }
  const rows=g.rows.slice(-5),rhythm=rows.reduce((s,a)=>s+Math.min(a.result.attacks,a.result.durations),0)/rows.length,pitch=rows.reduce((s,a)=>s+(a.result.pitch??1),0)/rows.length;
  return {key:g.key,source:g.rows.at(-1),count:g.rows.length,stage,status,due,isDue:due<=now,reason:rhythm<pitch?'Rhythm needs more support than pitch in your recent comparable attempts.':pitch<rhythm?'Retain your rhythm while checking pitch landmarks.':'Consolidate both components with an unfamiliar phrase.'};
 }).sort((a,b)=>a.due-b.due);
}
const mean=(rows,fn)=>rows.reduce((sum,a)=>sum+fn(a),0)/rows.length;
export function comparisons(attempts){return evidenceGroups(attempts).map(g=>{
 const n=g.rows.length,first=g.rows.slice(0,4),last=g.rows.slice(-4),summary=rows=>({rhythm:mean(rows,a=>Math.min(a.result.attacks,a.result.durations)),pitch:mean(rows,a=>a.result.pitch??1),integrated:mean(rows,a=>a.result.integrated)});
 return {key:g.key,source:g.rows.at(-1),count:n,baseline:n>=8?summary(first):null,recent:n>=8?summary(last):null};
});}
export function draftEvidence(attempt){return (attempt.drafts||[]).map(d=>({hearing:d.hearing,elapsed:d.elapsed,result:grade(attempt.target,{...attempt.target,events:d.answer},attempt.policy.rhythmOnly)}));}
