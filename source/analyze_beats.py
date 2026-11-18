"""Optional: rebuild onset events after separating a replacement song."""
from pathlib import Path
import json,subprocess
import numpy as np
from scipy.signal import stft,find_peaks
from scipy.ndimage import gaussian_filter1d
R=Path(__file__).resolve().parents[1]
def audio(name):return np.frombuffer(subprocess.check_output(['ffmpeg','-v','error','-i',str(R/f'analysis/{name}.wav'),'-ac','1','-ar','22050','-f','f32le','-']),dtype='f4')
f,t,D=stft(audio('drums'),22050,nperseg=1024,noverlap=768);_,_,B=stft(audio('bass'),22050,nperseg=1024,noverlap=768);_,_,O=stft(audio('other'),22050,nperseg=1024,noverlap=768)
def flux(S,lo,hi):
 v=np.sqrt((abs(S[(f>=lo)&(f<hi)])**2).mean(0));v=gaussian_filter1d(np.maximum(0,np.diff(np.log1p(v*120),prepend=0)),.7);return np.clip(v/(np.percentile(v,96)+1e-8),0,3)
tracks={'kick':flux(D,35,180),'snare':flux(D,180,4200),'hat':flux(D,4500,10000),'bass':flux(B,35,400),'music':flux(O,300,6000)};hits={}
for n,v in tracks.items():
 peaks,_=find_peaks(v,distance=round((.23 if n=='kick' else .12)*22050/256),prominence=.3,height=.42);hits[n]=[dict(t=round(float(t[i]),4),s=round(float(v[i]),3)) for i in peaks]
np.savez_compressed(R/'analysis/features.npz',time=t,**tracks);(R/'analysis/hits.json').write_text(json.dumps(hits));print({k:len(v) for k,v in hits.items()})
