"""Pre-rendered local synthesis. No UI timer is used as a musical clock."""
from fractions import Fraction as F
import wave
import numpy as np
from .music import sounding
SR=44100

def schedule(score, support='Count-in only', count_in=True):
    lead=float(score.measure)*score.seconds_per_quarter if count_in else 0
    notes=[(lead+float(e.onset)*score.seconds_per_quarter,float(e.duration)*score.seconds_per_quarter,e.midi)
           for e in sounding(score.events) if not e.rest and e.midi is not None and e.duration]
    clicks=[]
    if count_in:
        for i in range(int(score.measure/score.beat_unit)):
            clicks.append((float(i*score.beat_unit)*score.seconds_per_quarter,i==0))
    unit=score.beat_unit/(2 if support=='Subdivision clicks' else 1)
    if support in ('Subdivision clicks','Beat clicks','Dropout'):
        t=F(0)
        while t<score.length:
            if support!='Dropout' or t<score.beat_unit*2: clicks.append((lead+float(t)*score.seconds_per_quarter,t%score.measure==0))
            t+=unit
    return notes,clicks,lead+float(score.length)*score.seconds_per_quarter+.15

def render(score,support='Count-in only',count_in=True,volume=.65):
    notes,clicks,length=schedule(score,support,count_in)
    out=np.zeros(int(length*SR)+1,dtype=np.float64)
    for onset,duration,midi in notes:
        n=max(2,int(duration*SR)); t=np.arange(n)/SR; f=440*2**((midi-69)/12)
        tone=sum(np.sin(2*np.pi*f*k*t)*(1/k**2) for k in (1,2,3,4))
        envelope=np.minimum(1,t/.008)*np.minimum(1,(duration-t)/.025)*(.65+.35*np.exp(-3*t))
        start=round(onset*SR); out[start:start+n]+=.35*tone*envelope
    for onset,accent in clicks:
        t=np.arange(int(.035*SR))/SR
        click=.25*np.sin(2*np.pi*(1500 if accent else 1100)*t)*np.exp(-t*120)
        start=round(onset*SR);out[start:start+len(click)]+=click
    return (np.clip(out,-.95,.95)*volume).astype(np.float32)

def write_wav(path,samples):
    with wave.open(str(path),'wb') as f:
        f.setnchannels(1);f.setsampwidth(2);f.setframerate(SR)
        f.writeframes((samples*32767).astype('<i2').tobytes())

class Player:
    def __init__(self): self.active=False
    def play(self,score,support='Count-in only',count_in=True,volume=.65):
        import sounddevice as sd
        self.stop(); samples=render(score,support,count_in,volume)
        sd.check_output_settings(samplerate=SR,channels=1,dtype='float32')
        sd.play(samples,SR,blocking=False);self.active=True
        return len(samples)/SR
    def stop(self):
        import sounddevice as sd
        sd.stop();self.active=False
