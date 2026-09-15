"""Capture real Qt widgets with isolated, scripted demonstration data."""
import sys
from pathlib import Path
import tempfile
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt,QPoint
from PyQt6.QtTest import QTest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tdm.ui import Window
from tdm.storage import Store
from tdm.music import sequence

app=QApplication([]);out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=True)
w=Window(Store(tempfile.mkdtemp(prefix='tdm-documentation-')));w.resize(1360,900);w.show()
def capture(name):
    app.processEvents();w.grab().save(str(out/name))
w.navigate('Today');capture('01-today.png')
w.navigate('Learn');w.lesson_choice.setCurrentIndex(2);capture('02-learn.png')
w.navigate('Practice');w.level.setCurrentIndex(1);w.new_exercise(sequence([1,2,1],[28,29,28],level=1))
capture('03-blank.png')
w.duration.setCurrentText('Half');w.editor.append(28);capture('04-entry.png')
w.duration.setCurrentText('Quarter');w.editor.append(29);w.editor.append(28)
# Simulated hearing completion is documented; this demonstrates grading, not listening ability.
w.exposures=1;w.completed_hearings=1;w.awaiting_draft=True;w.save_draft();w.submit();capture('05-feedback.png')
w.score_tabs.setCurrentIndex(1);capture('06-target.png')
w.mode.setCurrentText('Paper');w.support.setCurrentText('Count-in only');w.new_exercise();capture('07-paper.png')
w.mode.setCurrentText('Assessment');w.support.setCurrentText('No clicks');w.new_exercise();capture('08-assessment.png')
w.resize(940,680);capture('09-small.png');w.close()
