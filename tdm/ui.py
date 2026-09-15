from __future__ import annotations
from dataclasses import replace
from fractions import Fraction as F
import json
from pathlib import Path
import secrets
import time
import uuid
from PyQt6.QtCore import Qt,QTimer
from PyQt6.QtGui import QFont,QPdfWriter,QPainter,QPageSize
from PyQt6.QtWidgets import (QApplication,QMainWindow,QWidget,QVBoxLayout,QHBoxLayout,QGridLayout,
    QLabel,QPushButton,QComboBox,QCheckBox,QSpinBox,QScrollArea,QStackedWidget,QMessageBox,
    QFileDialog,QFrame,QTextBrowser,QDialog,QDialogButtonBox,QTabWidget)
from .music import Score,Event,DURATIONS,generate,sequence,depitch,validate
from .editor import Staff
from .audio import Player,render,write_wav
from .grading import grade
from .storage import Store,independent,comparable,progression
from .curriculum import LESSONS,LEVEL_NAMES,PLANS

DARK='''QWidget{background:#101F22;color:#E7EFE8;font:11pt "Segoe UI";}
QLabel{background:transparent;} QFrame#rail{background:#0B181B;border-radius:10px;}
QPushButton{background:#20363A;border:1px solid #365156;border-radius:6px;padding:9px 13px;}
QPushButton:hover{background:#365156;} QPushButton:disabled{color:#9AABA7;background:#182D30;}
QPushButton[primary="true"]{background:#A6E3C5;color:#101F22;font-weight:600;}
QPushButton[primary="true"]:disabled{background:#29433D;color:#A3B8AE;}
QComboBox,QSpinBox{background:#20363A;border:1px solid #526C70;border-radius:4px;padding:6px;}
QComboBox QAbstractItemView{background:#20363A;color:#E7EFE8;selection-background-color:#365156;}
QTextBrowser{background:#182D30;border:1px solid #365156;border-radius:8px;padding:12px;}
QScrollArea{border:0;} QCheckBox{spacing:7px;padding:5px;} QToolTip{background:#F6F1E5;color:#101F22;}
QTabBar::tab{background:#20363A;padding:8px 18px;} QTabBar::tab:selected{background:#365156;}
'''
LIGHT='''QWidget{background:#F6F1E5;color:#152A2D;font:11pt "Segoe UI";} QLabel{background:transparent;}
QPushButton,QComboBox,QSpinBox{background:#E4EADB;color:#152A2D;border:1px solid #58706A;border-radius:5px;padding:8px;}
QPushButton[primary="true"]{background:#254E42;color:white;} QTextBrowser{background:white;color:#152A2D;padding:12px;}
QPushButton:disabled{color:#656D68;} QScrollArea{border:0;}'''

def label(text,size=11):
    x=QLabel(text);x.setWordWrap(True)
    if size!=11:x.setStyleSheet(f'font: {size}pt "Georgia"; background:transparent;')
    return x
def button(text,callback,primary=False):
    b=QPushButton(text);b.setProperty('primary',primary);b.clicked.connect(callback);return b
def combo(values):
    c=QComboBox();c.addItems(values);return c
def scroll(widget):
    s=QScrollArea();s.setWidgetResizable(True);s.setWidget(widget);return s

class Window(QMainWindow):
    def __init__(self,store=None):
        super().__init__();self.store=store or Store();self.player=Player();self.loading=True
        self.setWindowTitle('Theory Dictation Master');self.resize(1280,820);self.setMinimumSize(900,640)
        self.timer=QTimer(self);self.timer.setSingleShot(True);self.timer.timeout.connect(self.audio_finished)
        self.active_kind=None;self.completed_hearings=0;self.playing=False
        self.settings=self.store.get('settings',{'vocal_rest':True,'theme':'Ink green','bpm':80,'bars':1,'hearings':4,'support':'Beat clicks'})
        QApplication.instance().setStyleSheet(LIGHT if self.settings['theme']=='Light' else DARK)
        root=QWidget();layout=QHBoxLayout(root);layout.setContentsMargins(14,14,14,14);layout.setSpacing(22)
        rail=QFrame();rail.setObjectName('rail');rail.setFixedWidth(165);nav=QVBoxLayout(rail)
        nav.addWidget(label('Theory\nDictation\nMaster',20));nav.addSpacing(24)
        self.stack=QStackedWidget();self.pages={}
        for name in ['Today','Learn','Practice','Progress','Settings']:
            nav.addWidget(button(name,lambda checked=False,n=name:self.navigate(n)))
        nav.addStretch();nav.addWidget(label('LOCAL & OFFLINE\nYour ear. Your notation.'))
        layout.addWidget(rail);layout.addWidget(self.stack,1);self.setCentralWidget(root)
        self.build_practice();self.build_today();self.build_learn();self.build_progress();self.build_settings()
        saved=self.store.get('session')
        if saved:
            try:self.restore_session(saved)
            except (ValueError,KeyError,TypeError) as exc:
                QMessageBox.warning(self,'Session could not resume',f'Your attempt history is intact. A new exercise will open.\n{exc}');self.new_exercise()
        else:self.new_exercise()
        self.loading=False;self.navigate('Today' if self.store.get('tutorial_done') else 'Learn')
    def add_page(self,name,page):
        old=self.pages.get(name)
        if old:self.stack.removeWidget(old);old.deleteLater()
        self.pages[name]=page;self.stack.addWidget(page)
    def navigate(self,name):
        self.stop_audio();self.save_session()
        if name=='Learn' and hasattr(self,'target') and not self.submitted and self.exposures and 'lesson during attempt' not in self.assistance:
            self.assistance.append('lesson during attempt');self.save_session()
        if name=='Today':self.build_today()
        if name=='Progress':self.build_progress()
        self.stack.setCurrentWidget(self.pages[name])
    def build_today(self):
        page=QWidget();v=QVBoxLayout(page);v.setSpacing(18)
        v.addWidget(label('A LITTLE LISTENING. A CLEARER PHRASE.'))
        v.addWidget(label('Make room for the rhythm.',30))
        v.addWidget(label('Welcome, Christian. Hear the phrase, write what you know, then reconnect pitch and rhythm.'))
        current=self.store.get('earned_level',0)
        v.addWidget(label('Current path: '+LEVEL_NAMES[current],18))
        v.addWidget(label('Begin at zero. Lessons introduce one concept at a time. Independent evidence governs confirmed progression.'))
        row=QHBoxLayout();row.addWidget(button('Continue practice',lambda:self.navigate('Practice'),True));row.addWidget(button('Learn the next concept',lambda:self.navigate('Learn')));v.addLayout(row)
        self.session_length=combo(['20 minute block','15 minute block','25 minute block','Low energy: 8 minutes'])
        row=QHBoxLayout();row.addWidget(self.session_length);row.addWidget(button('Start a focused block',self.start_block));v.addLayout(row)
        for title,body in PLANS:
            v.addWidget(label(title,17));v.addWidget(label(body))
        attempts=self.store.attempts();count=sum(independent(a) for a in attempts)
        v.addWidget(label(f'Evidence so far: {len(attempts)} saved attempts; {count} complete independent attempts.'))
        v.addWidget(label('Vocal rest is '+('on. Listening and silent notation remain available.' if self.settings.get('vocal_rest',True) else 'off. Optional vocal modules are planned.')))
        v.addStretch();self.add_page('Today',scroll(page))
    def start_block(self):
        minutes=[20,15,25,8][self.session_length.currentIndex()]
        self.block_end=time.time()+minutes*60;self.navigate('Practice');self.coach.setText(f'{minutes}-minute block. You can stop early without losing progress. Keep all counts internal.')
    def build_learn(self):
        page=QWidget();v=QVBoxLayout(page);v.addWidget(label('Learn it. Hear it. Write it.',28))
        self.lesson_choice=combo([f'{i}. {x[0]}' for i,x in enumerate(LESSONS)])
        self.lesson_choice.setCurrentIndex(self.store.get('lesson_index',0));self.lesson_text=QTextBrowser()
        self.example_staff=Staff(readonly=True);self.example_staff.grid=True
        v.addWidget(self.lesson_choice);v.addWidget(self.lesson_text,1);v.addWidget(scroll(self.example_staff),1)
        row=QHBoxLayout();row.addWidget(button('Hear worked example',self.play_lesson));row.addWidget(button('Try guided entry',self.guided));row.addWidget(button('Independent check',self.lesson_check,True));v.addLayout(row)
        row=QHBoxLayout();row.addWidget(button('Finish interface tutorial',self.finish_tutorial));row.addWidget(button('Next lesson',self.next_lesson));v.addLayout(row)
        self.lesson_choice.currentIndexChanged.connect(self.show_lesson);self.show_lesson();self.add_page('Learn',page)
    def show_lesson(self):
        self.stop_audio();idx=self.lesson_choice.currentIndex();title,text,durs,steps,level=LESSONS[idx]
        self.lesson_text.setPlainText(title+'\n\n'+text+'\n\nMethod: establish pulse and key, notice contour and landmarks, mark attacks, then fill details. No audible counting is needed.')
        self.lesson_score=sequence(durs,steps,level=level);self.example_staff.context=self.lesson_score;self.example_staff.set_events(self.lesson_score.events)
        self.store.put('lesson_index',idx)
    def play_lesson(self):self.play_score(self.lesson_score,'Beat clicks','lesson')
    def guided(self):
        self.navigate('Practice');self.new_exercise(self.lesson_score,assistance=['worked example'],lesson=self.lesson_choice.currentIndex())
        self.coach.setText(LESSONS[self.lesson_choice.currentIndex()][1]);self.reveal_staff.set_events(self.target.events);self.score_tabs.setTabVisible(1,True)
    def lesson_check(self):
        idx=self.lesson_choice.currentIndex();self.navigate('Practice');self.level.setCurrentIndex(LESSONS[idx][4]);self.new_exercise(lesson=idx)
    def finish_tutorial(self):
        if self.store.get('tutorial_actions',False):
            self.store.put('tutorial_done',True);self.lesson_text.append('\nInterface tutorial complete. Start the pulse lesson next.')
        else:self.lesson_text.append('\nChoose Try guided entry, add a note, and use Undo. These interface actions do not affect mastery.')
    def next_lesson(self):
        idx=self.lesson_choice.currentIndex()
        if idx==0 and not self.store.get('tutorial_done'):
            self.lesson_text.append('\nFinish the ungraded interface tutorial first.');return
        if idx>0 and self.store.get(f'lesson_passes.{idx}',0)<2:
            self.lesson_text.append('\nComplete two unfamiliar independent checks with each assessed component at least 90% before moving on.');return
        self.lesson_choice.setCurrentIndex(min(len(LESSONS)-1,idx+1))
    def build_practice(self):
        page=QWidget();v=QVBoxLayout(page);v.setSpacing(10)
        v.addWidget(label('Catch the shape. Keep the pulse.',27))
        setup=QGridLayout();self.level=combo(LEVEL_NAMES);self.level.setCurrentIndex(self.store.get('earned_level',0))
        self.mode=combo(['Practice','Assessment','Paper']);self.support=combo(['Subdivision clicks','Beat clicks','Dropout','Count-in only','No clicks'])
        self.support.setCurrentText(self.settings.get('support','Beat clicks'))
        self.rhythm_only=QCheckBox('Assess rhythm only');self.rhythm_only.setChecked(False)
        self.bpm=QSpinBox();self.bpm.setRange(40,160);self.bpm.setValue(self.settings.get('bpm',80))
        self.bars=QSpinBox();self.bars.setRange(1,4);self.bars.setValue(self.settings.get('bars',1))
        self.hearings=QSpinBox();self.hearings.setRange(1,20);self.hearings.setValue(self.settings.get('hearings',4))
        for col,(name,w) in enumerate([('Target',self.level),('Mode',self.mode),('Pulse support',self.support)]):setup.addWidget(label(name),0,col);setup.addWidget(w,1,col)
        row=QHBoxLayout()
        for name,w in [('Quarter BPM',self.bpm),('Bars',self.bars),('Hearings',self.hearings)]:row.addWidget(label(name));row.addWidget(w)
        row.addWidget(self.rhythm_only);setup.addLayout(row,2,0,1,3);v.addLayout(setup)
        self.public_info=label('');v.addWidget(self.public_info)
        body=QHBoxLayout();left=QWidget();lv=QVBoxLayout(left);lv.setContentsMargins(0,0,0,0)
        tools=QGridLayout();self.duration=combo(list(DURATIONS)+['Unknown duration'])
        self.dotted=QCheckBox('Dot');self.rest=QCheckBox('Rest');self.unknown=QCheckBox('Unknown pitch');self.accidental=combo(['Natural','Sharp','Flat'])
        self.grid=QCheckBox('Beat grid');self.grid.setChecked(True)
        self.insert=QCheckBox('Insert before');self.insert.setToolTip('Place the next note before the selected event.')
        for i,w in enumerate([self.duration,self.accidental,self.dotted,self.rest,self.unknown,self.grid,self.insert]):tools.addWidget(w,i//4,i%4)
        self.toolbar=QWidget();self.toolbar.setLayout(tools);lv.addWidget(self.toolbar)
        self.editor=Staff();self.score_tabs=QTabWidget();self.score_tabs.addTab(scroll(self.editor),'Your answer');lv.addWidget(self.score_tabs,1)
        edits=QHBoxLayout()
        for text,fn in [('Apply to selected',self.apply_selected),('Tie',self.editor.tie),('Delete',self.editor.delete),('Undo',self.undo),('Redo',self.editor.redo)]:edits.addWidget(button(text,fn))
        self.edits_widget=QWidget();self.edits_widget.setLayout(edits);lv.addWidget(self.edits_widget)
        self.entry_status=label('');lv.addWidget(self.entry_status)
        self.reveal_staff=Staff(readonly=True);self.reveal_box=scroll(self.reveal_staff);self.score_tabs.addTab(self.reveal_box,'Target after submission');self.score_tabs.setTabVisible(1,False)
        body.addWidget(left,7)
        coach_panel=QWidget();cv=QVBoxLayout(coach_panel);cv.setContentsMargins(8,0,0,0)
        cv.addWidget(label('YOUR NEXT STEP',11));self.coach=label('Prepare barlines. Establish the pulse. Hear the whole phrase, then write the landmarks you caught.',16);cv.addWidget(self.coach)
        self.feedback=QTextBrowser();self.feedback.setMinimumHeight(150);cv.addWidget(self.feedback,1)
        self.confidence=combo(['Confidence: optional','Unsure','Somewhat sure','Very sure']);cv.addWidget(self.confidence)
        self.draft_button=button('Save hearing draft',self.save_draft,True);cv.addWidget(self.draft_button)
        self.depitch_button=button('Hear on one pitch',self.play_dep);cv.addWidget(self.depitch_button)
        self.answer_button=button('Play my answer',self.play_answer);cv.addWidget(self.answer_button)
        cv.addWidget(button('Hear tonic C reference',lambda:self.play_score(sequence([1],[28]),'No clicks','reference')))
        cv.addWidget(button('Targeted follow-up',self.targeted_followup))
        choice_row=QHBoxLayout()
        choice_row.addWidget(button('Easier',lambda:self.adjust_challenge(-1)))
        choice_row.addWidget(button('Stay here',lambda:self.new_exercise()))
        choice_row.addWidget(button('Challenge',lambda:self.adjust_challenge(1)))
        cv.addLayout(choice_row)
        self.paper_entry=button('Enter paper answer',self.enter_paper);cv.addWidget(self.paper_entry)
        self.selfcheck_button=button('Reveal for paper self-check',self.paper_selfcheck);cv.addWidget(self.selfcheck_button)
        self.export_button=button('Export audio + blank sheet',self.export_paper);cv.addWidget(self.export_button)
        self.key_button=button('Export answer key',self.export_key);cv.addWidget(self.key_button)
        body.addWidget(scroll(coach_panel),3);v.addLayout(body,1)
        footer=QHBoxLayout();self.play_button=button('Hear phrase',self.play_target,True);footer.addWidget(self.play_button)
        footer.addWidget(button('Stop',self.stop_audio));self.submit_button=button('Submit transcription',self.submit,True);footer.addWidget(self.submit_button)
        footer.addWidget(button('Next phrase',lambda:self.new_exercise()));v.addLayout(footer)
        self.level.currentIndexChanged.connect(self.settings_pending);self.mode.currentTextChanged.connect(self.settings_pending)
        for w in [self.support,self.bpm,self.bars,self.hearings]:
            (w.currentTextChanged if isinstance(w,QComboBox) else w.valueChanged).connect(self.settings_pending)
        self.rhythm_only.toggled.connect(self.settings_pending)
        for w in [self.duration,self.accidental]:w.currentTextChanged.connect(self.tool_changed)
        for w in [self.dotted,self.rest,self.unknown,self.grid,self.insert]:w.toggled.connect(self.tool_changed)
        self.editor.changed.connect(self.answer_changed);self.add_page('Practice',page)
    def settings_pending(self):
        if not self.loading:self.coach.setText('Settings apply to the next phrase. The current phrase keeps its original listening conditions.')
    def adjust_challenge(self,delta):
        self.level.setCurrentIndex(max(0,min(6,self.target.level+delta)));self.new_exercise()
        self.coach.setText('Exploratory practice. Only the pitch/rhythm level changed; confirmed progression still requires independent evidence.')
    def targeted_followup(self):
        if not self.submitted:
            self.coach.setText('Submit this response first so the follow-up can address an observed difference.');return
        old=self.target;r=self.result
        if r and min(r['attacks'],r['durations'])<.9:
            # Preserve rhythm and vary pitches. Familiar rhythm practice is assistance.
            steps=[28,29,30];rng=__import__('random').Random(secrets.randbits(32))
            events=tuple(replace(e,step=rng.choice(steps)) if not e.rest else e for e in old.events)
            self.new_exercise(replace(old,events=events),assistance=['matched rhythm follow-up'])
            self.coach.setText('Same rhythm, new pitches. This targeted practice is assisted. Afterward, use Next phrase for an unfamiliar transfer check.')
        else:
            self.new_exercise();self.coach.setText('Try an unfamiliar phrase. Keep its rhythm while recording contour and pitch landmarks.')
    def tool_changed(self):
        d=DURATIONS.get(self.duration.currentText());self.editor.duration=d*F(3,2) if d and self.dotted.isChecked() else d
        self.editor.accidental=[0,1,-1][self.accidental.currentIndex()];self.editor.rest=self.rest.isChecked();self.editor.unknown_pitch=self.unknown.isChecked();self.editor.insert_before=self.insert.isChecked()
        self.editor.grid=self.grid.isChecked() and getattr(self,'policy',{}).get('mode','Practice')=='Practice';self.editor.update()
    def apply_selected(self):
        self.tool_changed();self.editor.edit(duration=self.editor.duration,accidental=self.editor.accidental,rest=self.editor.rest,
            **({'step':None} if self.editor.unknown_pitch or self.editor.rest else {}))
    def undo(self):
        had=bool(self.editor.history);self.editor.undo()
        if had:self.store.put('tutorial_actions',True)
    def answer_changed(self):
        if not hasattr(self,'target'):return
        s=self.editor.score();units=sum((e.duration or F(0) for e in s.events),F(0))
        selected=self.editor.events[self.editor.selected] if 0<=self.editor.selected<len(self.editor.events) else None
        self.entry_status.setText(f'Your entry: {units} / {self.target.length} quarter-note units. '+(f'Selected: {selected.name}, duration {selected.duration or "?"}.' if selected else ''))
        self.save_session()
    def new_exercise(self,target=None,assistance=None,lesson=None):
        self.stop_audio()
        if hasattr(self,'target') and not self.submitted and (self.editor.events or self.completed_hearings):
            self.store.submit(self.attempt_record('abandoned'))
        self.policy=dict(mode=self.mode.currentText(),support=self.support.currentText(),hearings=self.hearings.value(),rhythm_only=self.rhythm_only.isChecked())
        if target is None:
            seen={a.get('fingerprint') for a in self.store.attempts()}
            for _ in range(300):
                target=generate(secrets.randbits(48),self.level.currentIndex(),self.bpm.value(),self.bars.value())
                if target.fingerprint not in seen:break
            if target.fingerprint in seen:assistance=list(assistance or [])+['familiar example; vocabulary pool exhausted']
        self.target=target;self.attempt_id=uuid.uuid4().hex;self.created=time.time();self.assistance=list(assistance or [])
        self.drafts=[];self.completed_hearings=0;self.exposures=0;self.awaiting_draft=False;self.submitted=False;self.audio_ok=True;self.lesson=lesson;self.result=None
        self.editor.context=replace(target,events=());self.editor.readonly=False;self.editor.set_events([])
        self.reveal_staff.context=target;self.reveal_staff.set_events([]);self.score_tabs.setTabVisible(1,False);self.score_tabs.setCurrentIndex(0);self.feedback.clear();self.confidence.setCurrentIndex(0)
        self.set_policy_ui();self.answer_changed();self.save_session()
    def set_policy_ui(self):
        exam=self.policy['mode']!='Practice';paper=self.policy['mode']=='Paper'
        self.editor.grid=not exam and self.grid.isChecked();self.grid.setEnabled(not exam);self.editor.update()
        self.depitch_button.setEnabled(not exam or self.submitted);self.answer_button.setEnabled(not exam or self.submitted)
        self.key_button.setEnabled(self.submitted);self.submit_button.setEnabled(not self.submitted)
        self.paper_entry.setVisible(paper and not self.submitted);self.selfcheck_button.setVisible(paper and not self.submitted)
        self.score_tabs.setVisible(not paper or self.submitted);self.toolbar.setVisible(not paper);self.edits_widget.setVisible(not paper)
        self.play_button.setText('Play target again' if self.submitted else 'Hear phrase')
        self.public_info.setText(f'{self.target.key}  |  4/4  |  {self.target.bars} bar(s)  |  Quarter = {self.target.bpm}  |  {self.policy["support"]}  |  {self.policy["mode"]}')
        self.update_hearings()
    def update_hearings(self):
        self.draft_button.setEnabled(self.awaiting_draft and not self.playing and not self.submitted)
        self.play_button.setEnabled(not self.playing and (self.submitted or (not self.awaiting_draft and self.exposures<self.policy['hearings'])))
        if not self.submitted:self.coach.setText(f'Hearings: {self.exposures}/{self.policy["hearings"]}. '+('Write what you retained, then save this hearing draft.' if self.awaiting_draft else 'Silently establish pulse, notice contour, and mark pitch landmarks or rhythm in any order.'))
    def play_score(self,score,support,kind):
        self.stop_audio()
        try:
            length=self.player.play(score,support,count_in=support!='No clicks');self.playing=True;self.active_kind=kind
            self.timer.start(round(length*1000));return True
        except Exception as exc:
            if hasattr(self,'audio_ok'):self.audio_ok=False;self.save_session()
            QMessageBox.warning(self,'Audio unavailable',f'Check your output device. This attempt cannot count as independent success.\n{exc}');return False
    def play_target(self):
        if not self.submitted and (self.awaiting_draft or self.exposures>=self.policy['hearings']):return
        if self.play_score(self.target,self.policy['support'],'target' if not self.submitted else 'debrief'):
            if not self.submitted:self.exposures+=1
            self.update_hearings();self.save_session()
    def audio_finished(self):
        self.playing=False
        if self.active_kind=='target':self.completed_hearings+=1;self.awaiting_draft=True
        self.active_kind=None;self.update_hearings();self.save_session()
    def stop_audio(self):
        if self.playing and self.active_kind=='target' and hasattr(self,'assistance'):
            if 'interrupted playback' not in self.assistance:self.assistance.append('interrupted playback')
            self.awaiting_draft=True
        self.timer.stop()
        try:self.player.stop()
        except Exception:pass
        self.playing=False;self.active_kind=None
        if hasattr(self,'policy'):self.update_hearings()
    def save_draft(self):
        if not self.awaiting_draft or self.playing or self.submitted:return
        self.drafts.append(dict(hearing=self.exposures,elapsed=time.time()-self.created,answer=self.editor.score().to_dict()))
        self.awaiting_draft=False;self.update_hearings();self.save_session()
    def play_dep(self):
        if self.policy['mode']!='Practice' and not self.submitted:return
        if not self.submitted:self.assistance.append('one-pitch reveal')
        self.play_score(depitch(self.target),'Beat clicks','aid');self.save_session()
    def play_answer(self):
        if self.policy['mode']!='Practice' and not self.submitted:return
        if not self.editor.events:return
        if not self.submitted:self.assistance.append('answer playback')
        self.play_score(self.editor.score(),'Count-in only','aid');self.save_session()
    def enter_paper(self):
        self.score_tabs.show();self.toolbar.show();self.edits_widget.show();self.editor.grid=False
        self.coach.setText('Copy your paper response before revealing the key. No handwriting has been automatically read.')
    def attempt_record(self,kind='independent',result=None):
        return dict(id=self.attempt_id,created=self.created,kind=kind,target=self.target.to_dict(),fingerprint=self.target.fingerprint,
            policy=self.policy,assistance=self.assistance,hearings=self.exposures,completed_hearings=self.completed_hearings,
            drafts=self.drafts,answer=self.editor.score().to_dict(),result=result or self.result or {},
            confidence=self.confidence.currentText(),audio_ok=self.audio_ok,elapsed=time.time()-self.created,lesson=self.lesson,adaptation_version='1',playing_target=self.playing and self.active_kind=='target')
    def submit(self):
        if self.submitted or self.playing:return
        if not self.completed_hearings:
            self.coach.setText('Complete a hearing before submitting. Audio trouble does not count as a wrong answer.');return
        if self.awaiting_draft:self.save_draft()
        self.result=grade(self.target,self.editor.score(),self.policy['rhythm_only'])
        kind='assisted' if self.assistance else 'independent'
        if not self.audio_ok:kind='invalid audio'
        record=self.attempt_record(kind,self.result);self.store.submit(record);self.submitted=True;self.editor.readonly=True
        if independent(record) and self.result['integrated']>=.9 and self.lesson is not None:
            key=f'lesson_fingerprints.{self.lesson}';seen=self.store.get(key,[])
            if self.target.fingerprint not in seen:
                seen.append(self.target.fingerprint);self.store.put(key,seen);self.store.put(f'lesson_passes.{self.lesson}',len(seen))
        report=progression(self.store.attempts(),record,threshold=self.store.get('pass_threshold',.9))
        if report['action']=='advance' and self.target.level==self.store.get('earned_level',0):
            self.store.put('earned_level',min(6,self.target.level+1))
        self.store.put(f'review.{self.target.level}',time.time()+20*60)
        self.reveal_staff.set_events(self.target.events);self.score_tabs.setTabVisible(1,True);self.set_policy_ui()
        r=self.result;lines=[f'Evidence: {kind}',f'Attack timing: {r["attacks"]:.0%}',f'Durations / rests: {r["durations"]:.0%}',
            'Pitch: not assessed' if r['pitch'] is None else f'Pitch sequence: {r["pitch"]:.0%}',f'Notation conventions: {r["notation"]:.0%}',f'Integrated: {r["integrated"]:.0%}','']+r['feedback']+r['issues']
        lines += ['',f'Comparable independent items: {report["count"]}. Recommendation: {report["action"]}.',report['rule']]
        self.feedback.setPlainText('\n'.join(lines));self.coach.setText('Compare target and answer. Hear the one-pitch version, then try an unfamiliar pitched phrase at these settings.')
        if hasattr(self,'block_end') and time.time()>self.block_end:self.coach.setText('Your planned block is complete. Save your progress and take a break, or choose a short review.')
        self.save_session()
    def paper_selfcheck(self):
        if self.policy['mode']!='Paper' or self.submitted:return
        self.stop_audio();self.assistance.append('answer revealed for paper self-check');self.result={}
        self.store.submit(self.attempt_record('paper self-check'));self.submitted=True;self.editor.readonly=True
        self.reveal_staff.set_events(self.target.events);self.score_tabs.setTabVisible(1,True);self.set_policy_ui()
        self.feedback.setPlainText('PAPER SELF-CHECK\nYour handwriting has not been graded.\n\nCompare attack positions, durations and rests, then pitch landmarks. Circle the first difference on paper. Replay the one-pitch version.\n\nThis self-check cannot establish independent mastery.');self.save_session()
    def save_session(self):
        if not hasattr(self,'target'):return
        self.store.put('session',dict(record=self.attempt_record(),submitted=self.submitted,awaiting_draft=self.awaiting_draft))
    def restore_session(self,saved):
        a=saved['record'];self.target=Score.from_dict(a['target']);self.policy=a['policy'];self.attempt_id=a['id'];self.created=a['created']
        self.assistance=a['assistance'];self.drafts=a['drafts'];self.completed_hearings=a.get('completed_hearings',0);self.exposures=a['hearings'];self.audio_ok=a['audio_ok']
        self.lesson=a.get('lesson');self.result=a.get('result') or None;self.submitted=saved['submitted'];self.awaiting_draft=saved['awaiting_draft']
        self.editor.context=replace(self.target,events=());self.editor.set_events(Score.from_dict(a['answer']).events);self.editor.readonly=self.submitted
        self.reveal_staff.context=self.target;self.reveal_staff.set_events(self.target.events if self.submitted else [])
        if a.get('playing_target'):
            self.assistance.append('interrupted by application exit');self.awaiting_draft=True
        self.score_tabs.setTabVisible(1,self.submitted);self.set_policy_ui();self.answer_changed()
        if self.result:self.feedback.setPlainText('\n'.join(self.result.get('feedback',[])))
    def export_pdf(self,path,key=False):
        pdf=QPdfWriter(str(path));pdf.setPageSize(QPageSize(QPageSize.PageSizeId.A4));pdf.setResolution(96)
        p=QPainter(pdf);p.setPen(Qt.GlobalColor.black);p.setFont(QFont('Georgia',17));p.drawText(35,40,'Theory Dictation Master')
        p.setFont(QFont('Segoe UI',11));p.drawText(35,70,f'{"ANSWER KEY" if key else "BLANK WORKSHEET"}   ID {self.attempt_id[:10]}')
        p.drawText(35,96,f'C major, 4/4, {self.target.bars} bar(s), quarter = {self.target.bpm}. {self.policy["hearings"]} hearings.')
        p.drawText(35,121,'Maintain pulse silently. Write after each hearing. Check attacks, then pitch landmarks.')
        if key:
            staff=Staff(self.target,readonly=True);staff.set_events(self.target.events);staff.resize(700,300);staff.grid=True
            p.save();p.translate(25,170);staff.render(p);p.restore()
        else:
            for row in range(5):
                y=190+row*150
                for line in range(5):p.drawLine(40,y+line*12,710,y+line*12)
        p.end()
    def export_paper(self):
        directory=QFileDialog.getExistingDirectory(self,'Choose worksheet export folder')
        if not directory:return
        base=Path(directory)/self.attempt_id[:10]
        write_wav(base.with_suffix('.wav'),render(self.target,self.policy['support'],self.policy['support']!='No clicks'))
        self.export_pdf(base.with_suffix('.pdf'))
        if not self.submitted:self.assistance.append('external audio export; exposures unobserved');self.save_session()
        self.coach.setText('Exported neutral-ID audio and blank worksheet. External listening is unobserved and cannot establish independent mastery here.')
    def export_key(self):
        if not self.submitted:return
        path,_=QFileDialog.getSaveFileName(self,'Save separate answer key',f'ANSWER-KEY-{self.attempt_id[:10]}.pdf','PDF (*.pdf)')
        if path:self.export_pdf(path,True)
    def build_progress(self):
        page=QWidget();v=QVBoxLayout(page);v.addWidget(label('Progress you can point to.',28));view=QTextBrowser();v.addWidget(view)
        attempts=self.store.attempts();rows=[a for a in attempts if independent(a)]
        lines=[f'{len(attempts)} saved attempts. {len(rows)} complete independent attempts.', 'Assisted, paper self-check, abandoned and invalid-audio records remain separate.','']
        for i,name in enumerate(LEVEL_NAMES):
            group=[a for a in rows if a['target']['level']==i]
            lines.append(name+f': {len(group)} independent items.')
            if group:
                tail=group[-8:];lines.append(f'  Last {len(tail)}: attacks {sum(a["result"]["attacks"] for a in tail)/len(tail):.0%}; durations {sum(a["result"]["durations"] for a in tail)/len(tail):.0%}. Conditions may differ; this is descriptive only.')
        lines+=['','Comparable first-draft evidence:']
        for a in rows[-8:]:
            if a.get('drafts'):
                first=grade(Score.from_dict(a['target']),Score.from_dict(a['drafts'][0]['answer']),a['policy']['rhythm_only'])
                lines.append(f'{a["id"][:8]}: first rhythm {min(first["attacks"],first["durations"]):.0%}, final rhythm {min(a["result"]["attacks"],a["result"]["durations"]):.0%}, {a["hearings"]} hearings.')
        lines+=['','Review reminders (unfamiliar items at the original level):']
        for i in range(7):
            due=self.store.get(f'review.{i}')
            if due:lines.append(LEVEL_NAMES[i]+': '+('due now' if due<=time.time() else time.strftime('%b %d %H:%M',time.localtime(due))))
        lines+=['','No retained-learning label is awarded by this core release. Later-day review and benchmark grouping need further calibration.']
        view.setPlainText('\n'.join(lines));v.addWidget(button('Export complete evidence JSON',self.export_history));self.add_page('Progress',page)
    def export_history(self):
        path,_=QFileDialog.getSaveFileName(self,'Save evidence','dictation-evidence.json','JSON (*.json)')
        if path:Path(path).write_text(json.dumps(self.store.attempts(),indent=2),encoding='utf-8')
    def build_settings(self):
        page=QWidget();v=QVBoxLayout(page);v.addWidget(label('A comfortable place to listen.',28))
        vocal=QCheckBox('Vocal rest: listening and silent notation only');vocal.setChecked(self.settings.get('vocal_rest',True));v.addWidget(vocal)
        theme=combo(['Ink green','Light']);theme.setCurrentText(self.settings['theme']);v.addWidget(theme)
        def save():
            self.settings.update(vocal_rest=vocal.isChecked(),theme=theme.currentText(),bpm=self.bpm.value(),bars=self.bars.value(),hearings=self.hearings.value(),support=self.support.currentText())
            self.store.put('settings',self.settings);QApplication.instance().setStyleSheet(LIGHT if theme.currentText()=='Light' else DARK)
        v.addWidget(button('Save preferences',save,True))
        v.addWidget(label('Core course: C major, treble clef, 4/4. Change BPM, bars, pulse support and hearings in Practice. Broader key, meter and clef curricula are planned.\n\nNo recording is opened by this application. Vocal recall, harmony and two-part dictation are planned extensions.\n\nThe interface uses no animated timing aids. Windows display scaling is supported.'))
        v.addWidget(button('Back up progress',self.backup));v.addWidget(button('Restore a backup',self.restore))
        v.addWidget(label('Data folder: '+str(self.store.directory)));v.addStretch();self.add_page('Settings',scroll(page))
    def backup(self):
        path,_=QFileDialog.getSaveFileName(self,'Save progress backup','TheoryDictationMaster-backup.sqlite3','SQLite (*.sqlite3)')
        if path:self.save_session();self.store.backup(path)
    def restore(self):
        path,_=QFileDialog.getOpenFileName(self,'Open progress backup','','SQLite (*.sqlite3)')
        if not path:return
        try:
            self.stop_audio();self.store.restore(path);saved=self.store.get('session')
            if saved:self.restore_session(saved)
            else:self.new_exercise()
            QMessageBox.information(self,'Restored','Backup restored. A safety backup of your previous data was saved. Restart to reload all profile preferences.')
        except Exception as exc:QMessageBox.warning(self,'Restore failed',str(exc))
    def closeEvent(self,event):
        self.stop_audio();self.save_session();self.store.close();event.accept()
