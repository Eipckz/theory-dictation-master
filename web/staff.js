import {name,Q,barTicks,beatTicks,beatCount} from './domain.js';
const esc=s=>String(s).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('"','&quot;');
export const yFor=step=>184-(step-30)*7;
export const stepFor=y=>Math.max(21,Math.min(49,30+Math.round((184-y)/7)));
export function staffSVG(score,{selected=-1,grid=false,readonly=false,title='Your transcription'}={}){
 const events=score.events,total=Math.max(score.bars*barTicks(score),events.reduce((s,e)=>s+(e.duration??Q),0)),shortest=Math.min(Q,...events.filter(e=>e.duration).map(e=>e.duration)),width=Math.max(640,total/shortest*44+150),xpos=t=>120+t/total*(width-158),pos=events.map(e=>[xpos(e.onset)+12,yFor(e.step??34)]);
 let svg=`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${width} 300" width="${width}" height="300" role="img" aria-label="${esc(title)}: ${events.length} entered events" ${readonly?'':'tabindex="0"'} class="score-svg"><rect width="100%" height="100%" fill="#F6F1E5"/><text x="24" y="27" class="score-label">${esc(title.toUpperCase())}</text><text x="24" y="49" class="score-context">${esc(score.key||'C major')} · Treble · ${esc(score.meter)} · ${score.bars} bar${score.bars===1?'':'s'}</text>`;
 for(let i=0;i<5;i++)svg+=`<path d="M24 ${184-i*14}H${width-24}" class="staff-line"/>`;
 svg+=`<text x="30" y="170" class="music clef">&#xE050;</text><text x="82" y="151" class="meter">${score.meter.split('/')[0]}</text><text x="82" y="178" class="meter">${score.meter.split('/')[1]}</text>`;
 for(let b=0;b<=score.bars;b++)svg+=`<path d="M${xpos(b*barTicks(score))} 128V184" class="staff-line"/>`;
 if(grid)for(let b=0;b<score.bars*beatCount(score);b++)svg+=`<path d="M${xpos(b*beatTicks(score))} 98V211" class="grid-line"/><text x="${xpos(b*beatTicks(score))+10}" y="225" class="beat-label">${b%beatCount(score)+1}</text>`;
 const groups=[];let group=[];events.forEach((e,i)=>{if(!e.rest&&e.step!==null&&e.duration&&e.duration<Q){if(group.length&&Math.floor(events[group[0]].onset/beatTicks(score))!==Math.floor(e.onset/beatTicks(score))){if(group.length>1)groups.push(group);group=[];}group.push(i);}else{if(group.length>1)groups.push(group);group=[];}});if(group.length>1)groups.push(group);const beamed=new Set(groups.flat());let accidentals={},bar=-1;
 events.forEach((e,i)=>{const [x,y]=pos[i],dotted=[72,36,18,9].includes(e.duration),base=dotted?e.duration*2/3:e.duration;
 svg+=`<g data-note="${i}"><title>${esc(name(e))}, ${e.duration===null?'unknown duration':e.duration/Q+' quarter-note units'}</title><rect x="${x-19}" y="${Math.min(y-23,105)}" width="38" height="${Math.max(55,y+23-105)}" fill="${i===selected&&!readonly?'#d7e8d4':'transparent'}" rx="8"/>`;
 if(e.rest){const code=({48:'E4E3',24:'E4E4',12:'E4E5',6:'E4E6',3:'E4E7'})[base]??'E4E5';svg+=`<text x="${x-6}" y="162" class="music rest">&#x${code};</text>`;}
 else{
  if(e.step!==null){for(let l=28;l>=e.step;l-=2)svg+=`<path d="M${x-12} ${yFor(l)}h24" class="staff-line"/>`;for(let l=40;l<=e.step;l+=2)svg+=`<path d="M${x-12} ${yFor(l)}h24" class="staff-line"/>`;svg+=`<ellipse cx="${x}" cy="${y}" rx="7" ry="4.7" transform="rotate(-14 ${x} ${y})" fill="${base>=24?'#F6F1E5':'#172e30'}" stroke="#172e30" stroke-width="1.7"/>`;}
  else svg+=`<text x="${x-6}" y="${y+6}" class="unknown">?</text>`;
  if(base!==48){svg+=`<path d="M${x+6} ${y}V${y-35}" class="stem"/>`;if(base&&base<Q&&!beamed.has(i))for(let f=0;f<(base<=3?2:1);f++)svg+=`<path d="M${x+6} ${y-35+f*7}q23 12 4 23q12 -12 -4 -19Z" fill="#172e30"/>`;}
  const nextBar=Math.floor(e.onset/barTicks(score));if(nextBar!==bar){bar=nextBar;accidentals={};}if(e.step!==null&&(accidentals[e.step]??0)!==e.acc)svg+=`<text x="${x-25}" y="${y+7}" class="accidental">${({'-1':'♭',0:'♮',1:'♯'})[e.acc]}</text>`;accidentals[e.step]=e.acc;
 }
 if(dotted)svg+=`<circle cx="${x+13}" cy="${y-4}" r="2" fill="#172e30"/>`;
 svg+=`<text x="${x}" y="260" text-anchor="middle" class="note-label">${esc(name(e))}</text>`;
 if(e.duration===null)svg+=`<text x="${x}" y="281" text-anchor="middle" class="note-label">duration ?</text>`;
 svg+='</g>';
 });
 for(const g of groups){const beamY=Math.min(...g.map(i=>pos[i][1]))-35;svg+=`<path d="M${pos[g[0]][0]+6} ${beamY}H${pos[g.at(-1)][0]+6}" stroke="#172e30" stroke-width="4"/>`;for(const i of g){const [x,y]=pos[i];svg+=`<path d="M${x+6} ${y}V${beamY}" class="stem"/>`;if(events[i].duration===3){const end=g.includes(i+1)&&events[i+1].duration===3?pos[i+1][0]+6:x+(i===g.at(-1)?-5:17);svg+=`<path d="M${x+6} ${beamY+7}H${end}" stroke="#172e30" stroke-width="3"/>`;}}}
 events.forEach((e,i)=>{if(e.tie&&pos[i+1]){const [x,y]=pos[i],[nx,ny]=pos[i+1];svg+=`<path d="M${x} ${y+9}C${x+10} ${y+27},${nx-10} ${ny+27},${nx} ${ny+9}" fill="none" stroke="#172e30" stroke-width="1.5"/>`;}});
 if(!events.length)svg+='<text x="125" y="265" class="score-context">Choose a duration, then tap the staff or a pitch button.</text>';
 return svg+'</svg>';
}
