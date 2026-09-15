"""Packaged deterministic smoke test. Uses an isolated temporary database by default."""
from dataclasses import replace
from pathlib import Path
import json
import tempfile
from PyQt6.QtCore import Qt,QPoint
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication
from .music import sequence
from .storage import Store
from .ui import Window
from .audio import render,write_wav

def run(data_dir=None,capture=None):
    root=Path(data_dir) if data_dir else Path(tempfile.mkdtemp(prefix='tdm-selftest-'))
    root.mkdir(parents=True,exist_ok=True)
    w=Window(Store(root));w.show();app=QApplication.instance();app.processEvents()
    w.navigate('Practice');w.new_exercise(sequence([1,2,1],[28,29,28]));app.processEvents()
    QTest.mouseClick(w.editor,Qt.MouseButton.LeftButton,pos=QPoint(140,w.editor.y_for(28)))
    assert len(w.editor.events)==1 and w.editor.events[0].midi==60
    w.duration.setCurrentText('Half');QTest.mouseClick(w.editor,Qt.MouseButton.LeftButton,pos=QPoint(230,w.editor.y_for(29)))
    assert len(w.editor.events)==2 and w.editor.events[1].duration==2
    w.undo();assert len(w.editor.events)==1;w.editor.redo();assert len(w.editor.events)==2
    w.duration.setCurrentText('Quarter');QTest.mouseClick(w.editor,Qt.MouseButton.LeftButton,pos=QPoint(540,w.editor.y_for(28)))
    assert len(w.editor.events)==3
    # Simulate completed audio for automated grading. This does not verify physical sound.
    w.completed_hearings=1;w.exposures=1;w.awaiting_draft=True;w.save_draft();w.submit()
    assert w.result['integrated']==1 and len(w.store.attempts())==1
    w.submit();assert len(w.store.attempts())==1
    if capture:
        out=Path(capture);out.mkdir(parents=True,exist_ok=True)
        app.processEvents();w.grab().save(str(out/'practice-feedback.png'))
        w.navigate('Today');app.processEvents();w.grab().save(str(out/'today.png'))
        w.navigate('Learn');app.processEvents();w.grab().save(str(out/'learn.png'))
        w.mode.setCurrentText('Assessment');w.support.setCurrentText('No clicks');w.navigate('Practice');w.new_exercise();app.processEvents()
        assert not w.editor.grid and not w.depitch_button.isEnabled() and not w.answer_button.isEnabled()
        w.resize(940,680);app.processEvents();w.grab().save(str(out/'assessment-small.png'))
        w.export_pdf(out/'sample-blank.pdf');w.submitted=True;w.export_pdf(out/'sample-answer-key.pdf',True)
        write_wav(out/'sample-phrase.wav',render(sequence([1,2,1],[28,29,28])))
    w.close();app.processEvents()
    reopened=Store(root);assert len(reopened.attempts())>=1;assert reopened.get('session');reopened.close()
    (root/'self-test.json').write_text(json.dumps({'passed':True,'hardware_audio_verified':False,'checks':['Qt mouse entry','duration editing','undo redo','component grading','idempotence','restart persistence','exam aid policy','PDF WAV export']}),encoding='utf-8')
