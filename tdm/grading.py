"""Independent pitch and rhythm evidence, with sequence alignment for omissions."""
from fractions import Fraction as F
from .music import sounding, validate
from dataclasses import replace
VERSION='1'

def align(a,b):
    """Levenshtein pitch alignment. Gaps cost 1; a pitch substitution costs 1.
    Return ambiguous when multiple minimum-cost paths exist.
    Timing is excluded so rhythm mistakes cannot corrupt pitch evidence.
    """
    m,n=len(a),len(b); dp=[[0]*(n+1) for _ in range(m+1)]; ways=[[1]*(n+1) for _ in range(m+1)]
    for i in range(m+1): dp[i][0]=i
    for j in range(n+1): dp[0][j]=j
    for i in range(1,m+1):
        for j in range(1,n+1):
            v=[dp[i-1][j-1]+(a[i-1].midi!=b[j-1].midi),dp[i-1][j]+1,dp[i][j-1]+1]
            best=min(v); dp[i][j]=best
            ways[i][j]=min(2,sum(w for cost,w in zip(v,[ways[i-1][j-1],ways[i-1][j],ways[i][j-1]]) if cost==best))
    pairs=[]; i=m;j=n
    while i or j:
        if i and j and dp[i][j]==dp[i-1][j-1]+(a[i-1].midi!=b[j-1].midi):
            pairs.append((i-1,j-1));i-=1;j-=1
        elif i and dp[i][j]==dp[i-1][j]+1: i-=1
        else: j-=1
    return list(reversed(pairs)),dp[m][n],ways[m][n]>1

def grade(target,answer,rhythm_only=False):
    t=sounding(target.events); a=sounding(answer.events)
    tn=[e for e in t if not e.rest]; an=[e for e in a if not e.rest]
    attacks_t={e.onset for e in tn}; attacks_a={e.onset for e in an}
    attacks=2*len(attacks_t & attacks_a)/max(1,len(attacks_t)+len(attacks_a))
    # Exact segmentation and rest/sound status, deliberately independent of pitch.
    ts={(e.onset,e.duration,e.rest) for e in t}; ass={(e.onset,e.duration,e.rest) for e in a}
    durations=2*len(ts&ass)/max(1,len(ts)+len(ass))
    pairs,edits,ambiguous=align(tn,an)
    pitch=max(0,1-edits/max(1,len(tn),len(an)))
    matched=[(tn[i],an[j]) for i,j in pairs if tn[i].midi==an[j].midi]
    spelling=sum(x.step==y.step and x.accidental==y.accidental for x,y in matched)/max(1,len(matched))
    # Cross-bar single glyphs are a notation issue, not a listening failure.
    conventions=all(e.duration is not None and e.onset//answer.measure==(e.onset+e.duration-F(1,10000))//answer.measure for e in answer.events)
    notation=float(conventions and (spelling==1 or rhythm_only))
    validation_answer=replace(answer,events=tuple(replace(e,step=28) if e.step is None and not e.rest else e for e in answer.events)) if rhythm_only else answer
    issues=validate(validation_answer)
    incomplete=any(e.duration is None or (e.step is None and not e.rest and not rhythm_only) for e in answer.events) or not answer.events
    rhythm=min(attacks,durations)
    integrated=min(rhythm,pitch) if not rhythm_only else rhythm
    if incomplete: integrated=0
    feedback=[]
    if incomplete: feedback.append('This sketch is incomplete. Resolve each question mark before using it as independent evidence.')
    missing=sorted(attacks_t-attacks_a); extra=sorted(attacks_a-attacks_t)
    if missing: feedback.append(f'An attack is missing at quarter-note position {missing[0]} from the beginning. Mark this attack before adding pitches.')
    if extra: feedback.append(f'An extra attack appears at quarter-note position {extra[0]}. Check whether a note should sustain instead.')
    if attacks==1 and durations<1: feedback.append('Attack positions match. Check releases, sustained lengths and rests.')
    if pitch<1 and not rhythm_only: feedback.append(f'Pitch sequence needs {edits} edit(s). Preserve the rhythm while checking contour and pitch landmarks.')
    if ambiguous: feedback.append('More than one pitch alignment fits. The sequence score is stable, but a note-by-note diagnosis would be uncertain.')
    if notation<1: feedback.append('Review spelling and barline grouping separately from the listening scores.')
    if integrated==1: feedback.append('The assessed sound matches. Try an unfamiliar phrase with the same settings.')
    return dict(attacks=attacks,durations=durations,pitch=None if rhythm_only else pitch,notation=notation,
                integrated=integrated,complete=not incomplete and not issues,ambiguous=ambiguous,
                feedback=feedback,issues=issues,version=VERSION)
