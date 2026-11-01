from pathlib import Path
import os,json,subprocess
import numpy as np
ROOT=Path(__file__).resolve().parents[1];PROJECT=ROOT.parent
os.environ['TORCH_HOME']=str(PROJECT/'.cache/torch')
import torch,torchaudio,soundfile as sf
import scipy.ndimage as ndi
from scipy.signal import stft,find_peaks
torch.set_num_threads(3)
stem_path=ROOT/'analysis/drums.wav'
if not stem_path.exists():
 bundle=torchaudio.pipelines.HDEMUCS_HIGH_MUSDB_PLUS;model=bundle.get_model().eval();sr=bundle.sample_rate
 raw=subprocess.check_output(['ffmpeg','-v','error','-i',str(PROJECT/'assets/song.mp3'),'-f','f32le','-ac','2','-ar',str(sr),'-'])
 audio=torch.from_numpy(np.frombuffer(raw,dtype='f4').reshape(-1,2).copy().T)
 out=torch.zeros((3,audio.shape[-1]));weight=torch.zeros(audio.shape[-1]);length=sr*10;step=sr*8
 for start in range(0,audio.shape[-1],step):
  clip=audio[:,start:start+length];size=clip.shape[-1]
  if size<length:clip=torch.nn.functional.pad(clip,(0,length-size))
  mean=clip.mean();std=clip.std().clamp_min(1e-6)
  with torch.inference_mode():sources=model(((clip-mean)/std)[None])[0]*std
  selected=sources[[model.sources.index(n) for n in ['drums','bass','other']],:,:size].mean(1)
  fade=torch.ones(size);overlap=min(sr*2,size)
  if start:fade[:overlap]=torch.linspace(0,1,overlap)
  if start+size<audio.shape[-1]:fade[-overlap:]=torch.linspace(1,0,overlap)
  out[:,start:start+size]+=selected*fade;weight[start:start+size]+=fade
  print(f'STEMS {min((start+size)/sr,195):.1f}',flush=True)
 out/=weight.clamp_min(1e-6)
 for i,n in enumerate(['drums','bass','other']):sf.write(ROOT/f'analysis/{n}.wav',out[i].numpy(),sr,subtype='PCM_16')
sr=22050
def load(name):
 raw=subprocess.check_output(['ffmpeg','-v','error','-i',str(ROOT/f'analysis/{name}.wav'),'-ac','1','-ar',str(sr),'-f','f32le','-'])
 return np.frombuffer(raw,dtype='f4')
def spectral(y):
 f,t,s=stft(y,fs=sr,nperseg=1024,noverlap=896,boundary='zeros');return f,t,np.abs(s)
f,t,D=spectral(load('drums'));_,_,G=spectral(load('other'));_,_,B=spectral(load('bass'))
def band(S,lo,hi):return np.sqrt((S[(f>=lo)&(f<hi)]**2).mean(0))
def flux(a):return ndi.gaussian_filter1d(np.maximum(0,np.diff(np.log1p(a*100),prepend=0)),.8)
tracks={'kick':flux(band(D,35,170)),'snare':flux(band(D,180,4200)),'hat':flux(band(D,4500,10000)),'guitar':flux(band(G,500,6000)),'bass':flux(band(B,30,400))}
events={};normalized={}
for name,a in tracks.items():
 a=a/(np.percentile(a,96)+1e-8);normalized[name]=np.clip(a,0,3.)
 distance=int((.21 if name=='kick' else .16 if name=='snare' else .10)*sr/128)
 peaks,props=find_peaks(a,distance=distance,prominence=.26,height=.33)
 events[name]=[{'t':round(float(t[i]),4),'strength':round(float(a[i]),3)} for i in peaks]
combo=normalized['kick']*.5+normalized['snare']*.45+normalized['guitar']*.15
peaks,props=find_peaks(combo,distance=int(.35*sr/128),prominence=.35,height=.65)
events['accents']=[{'t':round(float(t[i]),4),'strength':round(float(combo[i]),3)} for i in peaks]
np.savez_compressed(ROOT/'analysis/percussion.npz',time=t,**normalized)
(ROOT/'analysis/hits.json').write_text(json.dumps(events,indent=2))
print('ANALYZED',json.dumps({k:len(v) for k,v in events.items()}),flush=True)
print('INTRO_ACCENTS',events['accents'][:18],flush=True)
