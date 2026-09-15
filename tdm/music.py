"""Authoritative score model. All times are rational quarter-note units."""
from __future__ import annotations
from dataclasses import dataclass, replace
from fractions import Fraction as F
import hashlib
import json
import random

LETTERS = "CDEFGAB"
PCS = (0, 2, 4, 5, 7, 9, 11)
DURATIONS = {"Whole": F(4), "Half": F(2), "Quarter": F(1), "Eighth": F(1, 2), "Sixteenth": F(1, 4)}
CELLS = [tuple(map(F, x)) for x in [(1,), (2,), (4,), ('1/2','1/2'), ('1/4','1/4','1/4','1/4'), ('1/2','1/4','1/4'), ('1/4','1/4','1/2'), ('1/4','1/2','1/4'), ('3/4','1/4'), ('1/4','3/4'), ('3/2','1/2')]]

@dataclass(frozen=True)
class Event:
    onset: F
    duration: F | None
    step: int | None = None  # C0=0, D0=1; None is explicitly unknown
    accidental: int = 0
    rest: bool = False
    tie: bool = False  # tie to next event
    voice: int = 0
    tuplet: bool = False

    @property
    def midi(self):
        if self.rest or self.step is None:
            return None
        return 12 * (self.step // 7 + 1) + PCS[self.step % 7] + self.accidental

    @property
    def name(self):
        return "rest" if self.rest else "?" if self.step is None else f"{LETTERS[self.step % 7]}{ {-1:'b',0:'',1:'#'}[self.accidental]}{self.step // 7}"

    def to_dict(self):
        return dict(onset=str(self.onset), duration=str(self.duration) if self.duration is not None else None,
                    step=self.step, accidental=self.accidental, rest=self.rest, tie=self.tie, voice=self.voice, tuplet=self.tuplet)

    @classmethod
    def from_dict(cls, d):
        e = cls(F(d['onset']), F(d['duration']) if d['duration'] is not None else None,
                d['step'], d.get('accidental',0), bool(d.get('rest')), bool(d.get('tie')), d.get('voice',0), bool(d.get('tuplet')))
        if e.onset < 0 or e.onset > 128 or (e.duration is not None and not F(1,64) <= e.duration <= 16):
            raise ValueError('Invalid score time')
        if e.step is not None and (type(e.step) is not int or not 7 <= e.step <= 63):
            raise ValueError('Invalid pitch')
        if e.accidental not in (-1,0,1) or e.voice != 0:
            raise ValueError('Unsupported accidental or voice')
        return e

@dataclass(frozen=True)
class Score:
    events: tuple[Event, ...]
    seed: int = 0
    level: int = 0
    numerator: int = 4
    denominator: int = 4
    bars: int = 1
    bpm: int = 80
    beat_unit: F = F(1)
    key: str = 'C major'
    version: str = '1'

    @property
    def measure(self): return F(self.numerator * 4, self.denominator)
    @property
    def length(self): return self.measure * self.bars
    @property
    def seconds_per_quarter(self): return 60 / self.bpm / float(self.beat_unit)
    @property
    def fingerprint(self):
        raw = json.dumps([e.to_dict() for e in self.events], sort_keys=True)
        return hashlib.sha256(raw.encode()).hexdigest()
    def to_dict(self):
        return dict(events=[e.to_dict() for e in self.events], seed=self.seed, level=self.level,
                    numerator=self.numerator, denominator=self.denominator, bars=self.bars,
                    bpm=self.bpm, beat_unit=str(self.beat_unit), key=self.key, version=self.version)
    @classmethod
    def from_dict(cls, d):
        if len(d['events']) > 256: raise ValueError('Score too long')
        s = cls(tuple(Event.from_dict(x) for x in d['events']), int(d['seed']), int(d['level']),
                int(d['numerator']), int(d['denominator']), int(d['bars']), int(d['bpm']), F(d['beat_unit']), d['key'], d.get('version','1'))
        if not 1 <= s.bars <= 4 or (s.numerator,s.denominator) not in ((4,4),(3,4),(6,8)) or not 40 <= s.bpm <= 160 or s.beat_unit not in (F(1),F(3,2)):
            raise ValueError('Unsupported score context')
        return s

def sequence(durations, steps=None, **kwargs):
    t = F(0); events = []
    for i, d in enumerate(durations):
        duration = F(d)
        step = steps[i] if steps is not None else 28
        events.append(Event(t, duration, None if step == -1 else step, rest=step == -1))
        t += duration
    return Score(tuple(events), **kwargs)

def reflow(events):
    """Unknown duration consumes a provisional beat for layout only, never for grading."""
    t = F(0); result=[]
    for e in events:
        result.append(replace(e, onset=t)); t += e.duration if e.duration is not None else F(1)
    return result

def validate(score, complete=True):
    issues=[]; end=F(0)
    for i,e in enumerate(score.events):
        if e.duration is None or (e.step is None and not e.rest):
            issues.append('An event is explicitly incomplete.')
        if e.onset != end: issues.append('Gap or overlap in the entered sequence.')
        end=e.onset+(e.duration or F(0))
        if e.tie:
            nxt=score.events[i+1] if i+1<len(score.events) else None
            if e.rest or e.midi is None or nxt is None or nxt.rest or nxt.midi != e.midi or nxt.onset != end:
                issues.append('A tie needs a following note of the same sounding pitch.')
    if complete and end != score.length: issues.append(f'Entered {end} quarter-note units; phrase requires {score.length}.')
    return list(dict.fromkeys(issues))

def sounding(events):
    """Merge valid ties. Repeated untied notes remain separate attacks."""
    result=[]; i=0
    while i<len(events):
        e=events[i]; d=e.duration or F(0)
        while e.tie and i+1<len(events) and e.midi is not None and e.midi==events[i+1].midi and events[i+1].onset==e.onset+(e.duration or F(0)):
            i+=1; e=events[i]; d+=e.duration or F(0)
        start=events[i].onset+ (events[i].duration or F(0))-d
        result.append(replace(e,onset=start,duration=d,tie=False)); i+=1
    return result

def generate(seed, level=0, bpm=80, bars=1, meter='4/4', **unused):
    rng=random.Random(seed); n,d=map(int,meter.split('/')); length=F(n*4,d)
    # Each level changes one dimension: pitch set or rhythmic vocabulary.
    bank=[(F(1),),(F(2),)]
    if level>=3: bank += [CELLS[3]]
    if level>=5: bank += [(F(3),),CELLS[10]]
    if level>=6: bank += CELLS[4:10]
    events=[]; t=F(0); step=28
    pitch_sets={0:[28],1:[28,29],2:[28,29,30],3:[28,29,30]}
    choices=pitch_sets.get(level,[28,29,30,31,32])
    for bar in range(bars):
        left=length
        while left:
            cell=rng.choice([c for c in bank if sum(c)<=left])
            for dur in cell:
                if level: step=rng.choice([s for s in choices if abs(s-step)<= (2 if level>=4 else 1)])
                rest=t>0 and rng.random()<.18
                events.append(Event(t,dur,step if not rest else None,rest=rest)); t+=dur
            left-=sum(cell)
    score=Score(tuple(events),seed,level,n,d,bars,bpm,F(3,2) if meter=='6/8' else F(1))
    assert not validate(score)
    return score

def depitch(score):
    return replace(score,events=tuple(replace(e,step=28,accidental=0) if not e.rest else e for e in score.events))
