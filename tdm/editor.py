"""Staff-first editor. Layout depends only on the student's answer and public context."""
from dataclasses import replace
from fractions import Fraction as F
from PyQt6.QtCore import Qt,QPointF,QRectF,pyqtSignal
from PyQt6.QtGui import QPainter,QColor,QPen,QFont,QPainterPath
from PyQt6.QtWidgets import QWidget
from .music import Event,Score,reflow,DURATIONS

def music_font(size):
    f=QFont();f.setFamilies(['Segoe UI Symbol','Noto Music','FreeSerif']);f.setPixelSize(size);return f

class Staff(QWidget):
    changed=pyqtSignal()
    def __init__(self,context=None,readonly=False):
        super().__init__();self.context=context or Score(())
        self.events=[];self.selected=-1;self.readonly=readonly;self.grid=True
        self.duration=F(1);self.accidental=0;self.rest=False;self.unknown_pitch=False;self.tuplet=False
        self.history=[];self.future=[];self.hits=[];self.dragging=False;self.insert_before=False
        self.setMinimumSize(660,300);self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setAccessibleName('Transcription staff');self.setAccessibleDescription('Click to append. Select notes to edit. Arrows move pitch; Delete removes; Control Z undoes.')
    def score(self): return replace(self.context,events=tuple(self.events))
    def checkpoint(self):
        self.history.append((list(self.events),self.selected));self.history=self.history[-100:];self.future=[]
    def notify(self):
        self.events=reflow(self.events);self.fit_width();self.update();self.changed.emit()
    def set_events(self,events):
        self.events=list(events);self.selected=-1;self.history=[];self.future=[];self.fit_width();self.update()
    def fit_width(self):
        shortest=min((e.duration for e in self.events if e.duration),default=F(1))
        length=max(self.context.length,sum((e.duration or F(1) for e in self.events),F(0)))
        self.setMinimumWidth(max(600,int(length/min(shortest,F(1))*43)+140))
    def undo(self):
        if self.readonly or not self.history:return
        self.future.append((list(self.events),self.selected));self.events,self.selected=self.history.pop();self.notify()
    def redo(self):
        if self.readonly or not self.future:return
        self.history.append((list(self.events),self.selected));self.events,self.selected=self.future.pop();self.notify()
    def append(self,step):
        if self.readonly:return
        self.checkpoint();e=Event(F(0),self.duration,None if self.unknown_pitch or self.rest else step,self.accidental,self.rest,tuplet=self.tuplet)
        index=self.selected if self.insert_before and self.selected>=0 else len(self.events)
        self.events.insert(index,e);self.selected=index;self.notify()
    def edit(self,**kwargs):
        if self.readonly or not 0<=self.selected<len(self.events):return
        self.checkpoint();self.events[self.selected]=replace(self.events[self.selected],**kwargs);self.notify()
    def delete(self):
        if self.readonly or not 0<=self.selected<len(self.events):return
        self.checkpoint();self.events.pop(self.selected);self.selected=min(self.selected,len(self.events)-1);self.notify()
    def tie(self):
        if 0<=self.selected<len(self.events):self.edit(tie=not self.events[self.selected].tie)
    def y_for(self,step):return 176-(step-30)*7
    def step_for(self,y):return max(21,min(49,30+round((176-y)/7)))
    def mousePressEvent(self,event):
        if self.readonly:return
        self.setFocus();pt=event.position()
        hit=next((i for i,r in self.hits if r.contains(pt)),-1)
        if hit>=0:
            self.selected=hit
            if event.button()==Qt.MouseButton.RightButton:self.delete()
            else:self.dragging=True;self.drag_start=pt;self.drag_saved=False;self.update()
        elif event.button()==Qt.MouseButton.LeftButton and 75<=pt.y()<=255 and pt.x()>100:
            self.append(self.step_for(pt.y()))
    def mouseMoveEvent(self,event):
        if not self.dragging or self.readonly:return
        if abs(event.position().y()-self.drag_start.y())<5:return
        if not self.drag_saved:self.checkpoint();self.drag_saved=True
        self.events[self.selected]=replace(self.events[self.selected],step=self.step_for(event.position().y()),rest=False)
        self.notify()
    def mouseReleaseEvent(self,event):self.dragging=False
    def keyPressEvent(self,e):
        if self.readonly:return
        key=e.key();ctrl=e.modifiers() & Qt.KeyboardModifier.ControlModifier
        if ctrl and key==Qt.Key.Key_Z:self.undo();return
        if ctrl and key==Qt.Key.Key_Y:self.redo();return
        if key in (Qt.Key.Key_Delete,Qt.Key.Key_Backspace):self.delete();return
        if key in (Qt.Key.Key_Left,Qt.Key.Key_Right):
            self.selected=max(0,min(len(self.events)-1,self.selected+(1 if key==Qt.Key.Key_Right else -1)));self.update();return
        if key in (Qt.Key.Key_Up,Qt.Key.Key_Down) and self.selected>=0:
            old=self.events[self.selected];self.edit(step=max(21,min(49,(old.step or 28)+(1 if key==Qt.Key.Key_Up else -1))),rest=False);return
        if key==Qt.Key.Key_T:self.tie();return
        if key==Qt.Key.Key_R:self.append(None);self.edit(rest=True,step=None);return
        if key in range(Qt.Key.Key_A,Qt.Key.Key_G+1):
            self.append(28+'CDEFGAB'.index(chr(key)));return
        if key==Qt.Key.Key_Space:self.append(28);return
        super().keyPressEvent(e)
    def paintEvent(self,event):
        p=QPainter(self);p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.fillRect(self.rect(),QColor('#F6F1E5'));ink=QColor('#152A2D');p.setPen(QPen(ink,1))
        p.setFont(QFont('Segoe UI',10));p.drawText(24,28,'YOUR TRANSCRIPTION' if not self.readonly else 'NOTATION')
        p.drawText(24,49,f'{self.context.key}   |   {self.context.numerator}/{self.context.denominator}   |   {self.context.bars} bar(s)')
        w=self.width();left=112;right=w-30;span=right-left
        for line in range(5):p.drawLine(24,176-line*14,right,176-line*14)
        p.setFont(music_font(68));p.drawText(31,177,'\U0001d11e')
        p.setFont(QFont('Georgia',18));p.drawText(78,144,str(self.context.numerator));p.drawText(78,170,str(self.context.denominator))
        total=max(self.context.length,sum((e.duration or F(1) for e in self.events),F(0)))
        def xpos(t):return left+float(t/total)*max(1,span-25)
        for bar in range(self.context.bars+1):
            x=xpos(bar*self.context.measure);p.drawLine(QPointF(x,120),QPointF(x,176))
        if self.grid:
            p.setFont(QFont('Segoe UI',9));p.setPen(QColor('#657572'))
            for beat in range(int(self.context.length)):
                x=xpos(F(beat));p.drawText(QPointF(x+5,210),str(beat%int(self.context.measure)+1))
                p.setPen(QPen(QColor('#C7CEC1'),1,Qt.PenStyle.DotLine));p.drawLine(QPointF(x,91),QPointF(x,194));p.setPen(QColor('#657572'))
        self.hits=[];positions=[];groups=[];group=[]
        for i,e in enumerate(self.events):
            if not e.rest and e.duration and e.duration<1 and e.step is not None:
                if group and self.events[group[0]].onset//1!=e.onset//1:
                    if len(group)>1:groups.append(group)
                    group=[]
                group.append(i)
            else:
                if len(group)>1:groups.append(group)
                group=[]
        if len(group)>1:groups.append(group)
        beamed={i for g in groups for i in g};accidentals={};last_bar=-1
        for i,e in enumerate(self.events):
            x=xpos(e.onset)+15;y=self.y_for(e.step if e.step is not None else 34)
            positions.append((x,y));self.hits.append((i,QRectF(x-14,y-19,28,38)))
            if i==self.selected and not self.readonly:
                p.setPen(Qt.PenStyle.NoPen);p.setBrush(QColor('#C8DFC8'));p.drawRoundedRect(QRectF(x-15,y-20,30,42),6,6)
            p.setPen(QPen(ink,1.5));p.setBrush(ink)
            base=e.duration*F(2,3) if e.duration in (F(6),F(3),F(3,2),F(3,4),F(3,8)) else e.duration
            if e.rest:
                glyph={F(4):'\U0001d13b',F(2):'\U0001d13c',F(1):'\U0001d13d',F(1,2):'\U0001d13e',F(1,4):'\U0001d13f'}.get(base,'\U0001d13d')
                p.setFont(music_font(38));p.drawText(QPointF(x-9,159),glyph)
            else:
                if e.step is not None:
                    step=e.step
                    for ledger in range(28,step-1,-2) if step<30 else range(40,step+1,2) if step>38 else []:
                        ly=self.y_for(ledger);p.drawLine(QPointF(x-12,ly),QPointF(x+12,ly))
                if e.step is None:
                    p.setFont(QFont('Segoe UI',15));p.drawText(QPointF(x-6,y+5),'?')
                else:
                    p.setBrush(QColor('#F6F1E5') if e.duration in (F(2),F(3),F(4),F(6)) else ink)
                    p.drawEllipse(QRectF(x-7,y-4.5,14,9))
                if base!=F(4):
                    p.drawLine(QPointF(x+6,y),QPointF(x+6,y-34))
                    if base and base<F(1) and i not in beamed:
                        for flag in range(2 if base<=F(1,4) else 1):
                            path=QPainterPath(QPointF(x+6,y-34+flag*7));path.cubicTo(x+22,y-26+flag*7,x+20,y-17+flag*7,x+10,y-15+flag*7);p.drawPath(path)
                bar=e.onset//self.context.measure
                if bar!=last_bar:accidentals={};last_bar=bar
                if e.step is not None and accidentals.get(e.step,0)!=e.accidental:
                    p.setFont(music_font(23));p.drawText(QPointF(x-26,y+7),{-1:'♭',0:'♮',1:'♯'}[e.accidental])
                accidentals[e.step]=e.accidental
            p.setBrush(ink)
            if e.duration in (F(6),F(3),F(3,2),F(3,4),F(3,8)):p.drawEllipse(QPointF(x+12,y-3),2,2)
            if e.duration is None:
                p.setFont(QFont('Segoe UI',10));p.drawText(QPointF(x-10,239),'dur ?')
            if e.tuplet:
                p.setFont(QFont('Segoe UI',10));p.drawText(QPointF(x,y-45),'3')
            p.setFont(QFont('Segoe UI',9));p.drawText(QPointF(x-8,263),e.name)
        for g in groups:
            beam_y=min(positions[i][1] for i in g)-34
            p.setPen(QPen(ink,4));p.drawLine(QPointF(positions[g[0]][0]+6,beam_y),QPointF(positions[g[-1]][0]+6,beam_y))
            for i in g:
                x,y=positions[i];p.setPen(QPen(ink,1.5));p.drawLine(QPointF(x+6,y),QPointF(x+6,beam_y))
                e=self.events[i]
                if e.duration in (F(1,4),F(3,8)):
                    nxt=i+1 if i+1 in g and self.events[i+1].duration in (F(1,4),F(3,8)) else None
                    endpoint=positions[nxt][0]+6 if nxt is not None else x+16 if i!=g[-1] else x-4
                    p.setPen(QPen(ink,3));p.drawLine(QPointF(x+6,beam_y+7),QPointF(endpoint,beam_y+7))
        for i,e in enumerate(self.events[:-1]):
            if e.tie:
                x,y=positions[i];nx,ny=positions[i+1];p.setPen(QPen(ink,1.5));p.setBrush(Qt.BrushStyle.NoBrush)
                path=QPainterPath(QPointF(x,y+9));path.cubicTo(x+10,y+27,nx-10,ny+27,nx,ny+9);p.drawPath(path)
        if not self.events:
            p.setFont(QFont('Segoe UI',11));p.setPen(ink);p.drawText(122,244,'Choose a duration, then click a staff position. No notes are prefilled.')
        p.end()
