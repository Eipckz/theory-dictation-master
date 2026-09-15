from dataclasses import replace
from fractions import Fraction as F
import os
import pytest
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt,QPoint
from PyQt6.QtTest import QTest
from tdm.ui import Window
from tdm.storage import Store
from tdm.music import sequence,Event,Score
from tdm.grading import grade

@pytest.fixture(scope='module')
def app():
    return QApplication.instance() or QApplication([])

@pytest.fixture
def window(app,tmp_path):
    w=Window(Store(tmp_path));w.show();app.processEvents()
    yield w
    w.close();app.processEvents()

def test_editor_sketch_edit_and_undo(window,app):
    w=window;w.navigate('Practice');w.duration.setCurrentText('Unknown duration');w.editor.append(28)
    assert w.editor.events[0].duration is None
    w.duration.setCurrentText('Eighth');w.dotted.setChecked(True);w.apply_selected()
    assert w.editor.events[0].duration==F(3,4)
    w.editor.undo();assert w.editor.events[0].duration is None
    w.editor.redo();assert w.editor.events[0].duration==F(3,4)
    w.editor.delete();assert not w.editor.events

def test_exam_has_no_target_or_aids(window):
    w=window;w.mode.setCurrentText('Assessment');w.support.setCurrentText('No clicks');w.new_exercise()
    assert not w.editor.events and not w.editor.grid and not w.score_tabs.isTabVisible(1)
    assert not w.answer_button.isEnabled() and not w.depitch_button.isEnabled()
    assert not w.reveal_staff.events

def test_paper_selfcheck_is_not_graded(window):
    w=window;w.mode.setCurrentText('Paper');w.new_exercise()
    assert not w.score_tabs.isVisible()
    w.paper_selfcheck();a=w.store.attempts()[-1]
    assert a['kind']=='paper self-check' and not a['result'] and w.submitted

def test_hearing_draft_gate_and_interrupt(window,monkeypatch):
    w=window;monkeypatch.setattr(w.player,'play',lambda *a,**kw:3)
    w.play_target();assert w.exposures==1 and w.playing
    w.stop_audio();assert 'interrupted playback' in w.assistance and w.awaiting_draft
    w.play_target();assert w.exposures==1
    w.save_draft();w.play_target();assert w.exposures==2
    w.audio_finished();assert w.completed_hearings==1 and w.awaiting_draft

def test_rhythm_only_accepts_explicit_unknown_pitch():
    target=sequence([1,1,2],[28,29,30]);answer=replace(target,events=tuple(replace(e,step=None) for e in target.events))
    r=grade(target,answer,True);assert r['complete'] and r['integrated']==1 and r['pitch'] is None
    assert not grade(target,answer,False)['complete']

def test_vocal_rest_and_backup_identity(window):
    assert window.settings['vocal_rest'] is True
    assert window.store.path.name=='progress.sqlite3'
    assert not hasattr(window,'recorder')
