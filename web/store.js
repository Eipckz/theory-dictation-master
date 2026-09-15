import {VERSION,clone,validateScore,grade,fingerprint} from './domain.js';
export const KEY='theory-dictation-master.web.v1';
export const fresh=()=>({schema:1,version:VERSION,profile:{vocalRest:true,theme:'dark'},earnedLevel:0,lesson:0,lessonPasses:{},tutorialDone:false,attempts:[],session:null});
export function validateBackup(data){
 if(!data||data.schema!==1||!Array.isArray(data.attempts)||data.attempts.length>2000||!Number.isInteger(data.earnedLevel)||data.earnedLevel<0||data.earnedLevel>6||!data.profile||typeof data.profile.vocalRest!=='boolean'||!['dark','light'].includes(data.profile.theme)||!Number.isInteger(data.lesson)||data.lesson<0||data.lesson>8||!data.lessonPasses||typeof data.lessonPasses!=='object')throw Error('This is not a valid Theory Dictation Master web backup.');
 if(data.updatedAt!==undefined&&(!Number.isFinite(data.updatedAt)||data.updatedAt<0))throw Error('Invalid update time.');if(data.resetAt!==undefined&&(!Number.isFinite(data.resetAt)||data.resetAt<0))throw Error('Invalid reset time.');for(const [key,values] of Object.entries(data.lessonPasses))if(!/^[0-8]$/.test(key)||!Array.isArray(values)||values.length>2000||values.some(v=>typeof v!=='string'))throw Error('Invalid lesson evidence.');
 const check=s=>{if(!s||typeof s.id!=='string'||s.id.length>100||!Array.isArray(s.answer)||!Array.isArray(s.drafts)||s.drafts.length>20||!Array.isArray(s.assistance)||s.assistance.some(x=>typeof x!=='string'||x.length>150)||!s.policy||!['practice','exam','paper'].includes(s.policy.mode)||!['beat','subdivision','dropout','countin','none'].includes(s.policy.support)||!Number.isInteger(s.policy.hearings)||s.policy.hearings<1||s.policy.hearings>20||!Number.isInteger(s.exposures)||s.exposures<0||s.exposures>1000||!Number.isInteger(s.completed)||s.completed<0||typeof s.audioOK!=='boolean'||typeof s.submitted!=='boolean'||!Number.isFinite(s.created))throw Error('Invalid session record.');validateScore(s.target);validateScore({...s.target,events:s.answer});for(const d of s.drafts)validateScore({...s.target,events:d.answer});};
 for(const a of data.attempts){check(a);if(a.result)a.result=grade(a.target,{...a.target,events:a.answer},a.policy.rhythmOnly);a.fingerprint=fingerprint(a.target);}if(data.session){check(data.session);if(data.session.result)data.session.result=grade(data.session.target,{...data.session.target,events:data.session.answer},data.session.policy.rhythmOnly);}
 return clone(data);
}
export function read(storage){const raw=storage.getItem(KEY);return raw?validateBackup(JSON.parse(raw)):fresh();}
export function save(storage,data){storage.setItem(KEY,JSON.stringify(data));}
export function mergeBackup(current,incoming){
 const other=validateBackup(incoming),map=new Map(current.attempts.map(a=>[a.id,a]));for(const a of other.attempts)if(!map.has(a.id))map.set(a.id,{...a,kind:'imported'});
 // Imported evidence stays visible but never silently manufactures mastery in this browser.
 return {...current,session:other.session,attempts:[...map.values()].sort((a,b)=>a.created-b.created),lesson:other.lesson,profile:other.profile};
}
