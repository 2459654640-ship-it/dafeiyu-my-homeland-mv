import json,math
from pathlib import Path
import numpy as np
from ui import ROOT,clamp,smooth

class Rhythm:
    def __init__(self):
        self.data=json.loads((ROOT/'analysis/hits.json').read_text())
        self.tracks={k:np.array([x['t'] for x in v]) for k,v in self.data.items()}
        self.strength={k:np.array([x['strength'] for x in v]) for k,v in self.data.items()}
        self.percussion=dict(np.load(ROOT/'analysis/percussion.npz'))

    def event(self,kind,t,decay=16):
        times=self.tracks[kind];i=int(np.searchsorted(times,t)-1)
        if i<0:return 0.,0.,0
        age=t-times[i];strength=clamp(self.strength[kind][i]/1.9)
        return float(math.exp(-age*decay)*strength),float(age),i

    def phase(self,kind,t):
        times=self.tracks[kind];i=max(0,int(np.searchsorted(times,t)-1))
        nxt=times[min(i+1,len(times)-1)]
        span=max(.08,min(.50,nxt-times[i]))
        return i+smooth(clamp((t-times[i])/span))

    def value(self,kind,t):
        return float(np.interp(t,self.percussion['time'],self.percussion[kind]))

    def state(self,t):
        return {k:self.event(k,t)[0] for k in ['kick','snare','hat','guitar','bass','accents']}

class LyricClock:
    def __init__(self,lines):self.lines=lines
    def word(self,line,word):
        for w in self.lines[line]['words']:
            if w['word']==word:return w['start'],w['end']
        return self.lines[line]['start'],self.lines[line]['end']
    def age(self,t,line,word):return t-self.word(line,word)[0]
    def active(self,t):return next((x for x in self.lines if x['start']<=t<x['end']+.40),None)
