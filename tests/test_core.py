from dataclasses import replace
from fractions import Fraction as F
import json
import time
import pytest
import numpy as np
from tdm.music import *
from tdm.grading import grade,align
from tdm.audio import schedule,render,SR
from tdm.storage import Store,progression,independent

def test_fixed_rhythm_sum():
    assert sum(map(F,['3/2','1/2','3/4','1/4','1/2','1/4','1/4']))==4
    assert F(1,4)*3+F(1,2)==F(5,4)
    assert [sum(x) for x in CELLS[3:10]]==[1]*7

def test_rest_lesson_can_resume():
    score=sequence(['3/2','1/2',2],[28,-1,30])
    assert Score.from_dict(score.to_dict())==score
    assert not validate(score)

@pytest.mark.parametrize('level',range(7))
@pytest.mark.parametrize('meter',['4/4','3/4','6/8'])
def test_generated_measure_boundaries(level,meter):
    for seed in range(100):
        s=generate(seed,level,bars=2,meter=meter)
        assert not validate(s)
        for bar in range(2):assert sum(e.duration for e in s.events if bar*s.measure<=e.onset<(bar+1)*s.measure)==s.measure
        assert Score.from_dict(s.to_dict())==s

def test_independent_rhythm_and_pitch():
    target=sequence([1,1,2],[28,29,30])
    rhythm_wrong=sequence([2,1,1],[28,29,30])
    r=grade(target,rhythm_wrong);assert r['pitch']==1 and r['durations']<1 and r['attacks']<1
    pitch_wrong=sequence([1,1,2],[30,31,32]);r=grade(target,pitch_wrong)
    assert r['attacks']==r['durations']==1 and r['pitch']<1

def test_deleted_note_does_not_cascade_pitch():
    target=sequence([1]*4,[28,29,30,31]);answer=sequence([1,1,2],[28,30,31])
    assert grade(target,answer)['pitch']==.75

def test_equivalent_tie_and_reattack():
    target=sequence([2,2],[28,30]);answer=sequence([1,1,2],[28,28,30])
    tied=replace(answer,events=(replace(answer.events[0],tie=True),)+answer.events[1:])
    assert grade(target,tied)['integrated']==1
    assert grade(target,answer)['attacks']<1
    assert len(schedule(tied)[0])==2
    assert schedule(tied)[0][0][1]==1.5

def test_dots_rests_and_compound_tempo():
    s=sequence(['3/2','1/2',2],[28,-1,30],bpm=120)
    notes,_,_=schedule(s,count_in=False)
    assert notes==[(0.,.75,60),(1.,1.,64)]
    s=sequence(['3/2','3/2'],[28,29],numerator=6,denominator=8,bpm=60,beat_unit=F(3,2))
    assert schedule(s,count_in=False)[0]==[(0.,1.,60),(1.,1.,62)]

def test_no_click_schedule_and_pcm():
    s=sequence([1,1,2],[28,29,30])
    assert schedule(s,'No clicks',False)[1]==[]
    pcm=render(s,'No clicks',False)
    assert pcm.dtype==np.float32 and np.isfinite(pcm).all()
    assert np.max(np.abs(pcm))<1
    assert abs(len(pcm)/SR-3.15)<.001

def test_unknown_is_not_correct_default():
    target=sequence([2,2],[28,29]);a=replace(target,events=(replace(target.events[0],duration=None),target.events[1]))
    assert grade(target,a)['integrated']==0
    assert not grade(target,a)['complete']

def test_ambiguous_pitch_alignment():
    a=sequence([1]*4,[28]*4);b=sequence([2,1,1],[28]*3)
    assert grade(a,b)['ambiguous']

def record(i,assisted=False):
    s=generate(i,3)
    return dict(id=str(i),created=time.time()+i,target=s.to_dict(),fingerprint=str(i),policy=dict(support='Beat clicks',mode='Practice',hearings=4,rhythm_only=False),
        kind='independent',assistance=['hint'] if assisted else [],audio_ok=True,result=dict(complete=True,attacks=1.,durations=1.,pitch=1.,integrated=1.))

def test_idempotence_backup_resume_restore(tmp_path):
    db=Store(tmp_path/'data');a=record(1)
    assert db.submit(a);assert not db.submit(a)
    db.put('session',{'answer':'saved'});backup=tmp_path/'backup.sqlite3';db.backup(backup);db.close()
    db=Store(tmp_path/'data');assert len(db.attempts())==1 and db.get('session')=={'answer':'saved'}
    db.put('session',{'answer':'changed'});db.restore(backup);assert db.get('session')=={'answer':'saved'};db.close()

def test_assistance_exposure_and_audio_cannot_promote():
    rows=[record(i,True) for i in range(16)];assert progression(rows,record(0))['action']!='advance'
    rows=[record(i) for i in range(16)];assert progression(rows,rows[0])['action']=='advance'
    for a in rows:a['fingerprint']='same'
    assert progression(rows,rows[0])['count']==1
    a=record(17);a['audio_ok']=False;assert not independent(a)

def test_corrupt_restore_preserves_data(tmp_path):
    db=Store(tmp_path/'data');db.put('kept',42);bad=tmp_path/'bad.sqlite3';bad.write_bytes(b'not a database')
    with pytest.raises(Exception):db.restore(bad)
    assert db.get('kept')==42;db.close()
