from pathlib import Path
import json, subprocess
import numpy as np
import librosa
import scipy.ndimage as ndi
from scipy.signal import find_peaks
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1]
audio=ROOT/'assets/song.mp3'
y,sr=librosa.load(audio,sr=22050,mono=True)
hop=256
S=np.abs(librosa.stft(y,n_fft=2048,hop_length=hop))
f=librosa.fft_frequencies(sr=sr,n_fft=2048)
t=librosa.frames_to_time(np.arange(S.shape[1]),sr=sr,hop_length=hop)
def norm(a):
    return np.clip(a/(np.percentile(a,95)+1e-9),0,1.4)
bands={}
for name,lo,hi in [('bass',35,180),('mid',180,2600),('air',2600,10000)]:
    bands[name]=norm(ndi.gaussian_filter1d(np.sqrt((S[(f>=lo)&(f<hi)]**2).mean(axis=0)),1.5))
rms=norm(librosa.feature.rms(y=y,frame_length=2048,hop_length=hop)[0])
onset=librosa.onset.onset_strength(y=y,sr=sr,hop_length=hop)
tempo,beat=librosa.beat.beat_track(onset_envelope=onset,sr=sr,hop_length=hop,start_bpm=120,trim=False)
beats=librosa.frames_to_time(beat,sr=sr,hop_length=hop)
peaks,_=find_peaks(onset,distance=int(.15*sr/hop),prominence=np.percentile(onset,60)*.8)
onsets=t[peaks]
smooth=ndi.gaussian_filter1d(rms,100)
mel=librosa.feature.melspectrogram(S=S**2,sr=sr,n_mels=48)
log=librosa.power_to_db(mel,ref=np.max)
feature=ndi.gaussian_filter1d(log,100,axis=1)
novelty=np.sqrt(np.mean((np.roll(feature,180,axis=1)-np.roll(feature,-180,axis=1))**2,axis=0))
novelty[:300]=novelty[-300:]=0
changes,_=find_peaks(novelty,distance=int(7*sr/hop),prominence=1)
result={'duration':len(y)/sr,'sample_rate':sr,'tempo_bpm':float(np.asarray(tempo).ravel()[0]),'beats':beats.tolist(),'onsets':onsets.tolist(),'section_candidates':[{'time':float(t[i]),'strength':float(novelty[i])} for i in changes]}
(ROOT/'analysis/music.json').write_text(json.dumps(result,indent=2))
np.savez_compressed(ROOT/'analysis/features.npz',time=t,rms=rms,onset=norm(onset),**bands)
fig,axes=plt.subplots(3,1,figsize=(18,8),sharex=True,facecolor='#061020')
for ax in axes:
    ax.set_facecolor('#061020');ax.tick_params(colors='#a1d7e5');ax.spines[['top','right']].set_visible(False)
axes[0].plot(np.arange(0,len(y),64)/sr,y[::64],lw=.35,color='#71ccdc');axes[0].plot(t,smooth,color='white',lw=1)
axes[1].imshow(log,origin='lower',aspect='auto',extent=[0,t[-1],0,48],cmap='magma',vmin=-65,vmax=0)
axes[2].plot(t,novelty,color='#a5e7f5');axes[2].set_xlabel('seconds',color='white')
for i in changes:
    for ax in axes:ax.axvline(t[i],color='#a5e7f5',lw=.6,alpha=.4)
    axes[2].text(t[i],novelty[i],f'{t[i]:.1f}',color='white',fontsize=8)
axes[0].set_title(f'OCEAN OF WORLDS / audio map / {result["tempo_bpm"]:.2f} BPM',color='white',loc='left')
fig.tight_layout();fig.savefig(ROOT/'analysis/music-map.png',dpi=130);plt.close(fig)
print(json.dumps(result|{'beats':len(beats),'onsets':len(onsets)},indent=2))
