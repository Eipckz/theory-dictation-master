import {validateBackup} from './store.js';
// Credentials stay in memory. They are never written to backups or the public site.
const encode=s=>btoa(Array.from(new TextEncoder().encode(s),b=>String.fromCharCode(b)).join(''));
const decode=s=>new TextDecoder().decode(Uint8Array.from(atob(s.replace(/\s/g,'')),c=>c.charCodeAt(0)));
export function mergeProgress(local,remote){
 const a=validateBackup(local),b=validateBackup(remote);
 // A reset generation prevents an old offline device from restoring erased progress.
 const ar=a.resetAt||0,br=b.resetAt||0;if(ar!==br)return ar>br?a:b;
 const newer=(a.updatedAt||0)>=(b.updatedAt||0)?a:b;
 const rows=new Map(b.attempts.map(x=>[x.id,x]));for(const x of a.attempts)rows.set(x.id,x);
 const passes={};for(let i=0;i<9;i++)passes[i]=[...new Set([...(a.lessonPasses[i]||[]),...(b.lessonPasses[i]||[])])];
 return {...newer,attempts:[...rows.values()].sort((x,y)=>x.created-y.created),lessonPasses:passes,earnedLevel:Math.max(a.earnedLevel,b.earnedLevel),tutorialDone:a.tutorialDone||b.tutorialDone};
}
export async function syncProgress(local,{repo,token},request=fetch){
 if(!/^[\w.-]+\/[\w.-]+$/.test(repo)||!token.trim())throw Error('Enter owner/repository and a repository access token.');
 const base='https://api.github.com/repos/'+repo,headers={Accept:'application/vnd.github+json',Authorization:'Bearer '+token.trim(),'X-GitHub-Api-Version':'2022-11-28'};
 const meta=await request(base,{headers,cache:'no-store'});
 if(!meta.ok)throw Error('Cannot access the progress repository. Check its name and token permissions.');
 if(!(await meta.json()).private)throw Error('Progress sync requires a private repository.');
 for(let retry=0;retry<3;retry++){
  const response=await request(base+'/contents/progress.json',{headers,cache:'no-store'});let sha,merged=validateBackup(local);
  if(response.ok){const file=await response.json();if(file.size>4000000)throw Error('Cloud backup exceeds the 4 MB limit.');sha=file.sha;merged=mergeProgress(local,JSON.parse(decode(file.content)));}
  else if(response.status!==404)throw Error('Could not download progress. Your local work is unchanged.');
  const result=await request(base+'/contents/progress.json',{method:'PUT',headers:{...headers,'Content-Type':'application/json'},body:JSON.stringify({message:'Sync dictation progress',content:encode(JSON.stringify(merged)),...(sha?{sha}:{})})});
  if(result.ok)return merged;
  if(![409,422].includes(result.status))throw Error('Could not save cloud progress. Check Contents: read and write permission, token expiry, and connection.');
 }
 throw Error('Another device is updating progress. Try Sync now again.');
}
