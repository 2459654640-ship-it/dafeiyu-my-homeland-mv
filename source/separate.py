from pathlib import Path
import os,subprocess
import numpy as np
R=Path(__file__).resolve().parents[1];os.environ.setdefault('TORCH_HOME',str(R/'.cache/torch'))
import torch,torchaudio,soundfile as sf
torch.set_num_threads(3);bundle=torchaudio.pipelines.HDEMUCS_HIGH_MUSDB_PLUS;model=bundle.get_model().eval();sr=bundle.sample_rate
raw=subprocess.check_output(['ffmpeg','-v','error','-i',str(R/'assets/song.mp3'),'-f','f32le','-ac','2','-ar',str(sr),'-'])
audio=torch.from_numpy(np.frombuffer(raw,dtype='f4').reshape(-1,2).copy().T);out=torch.zeros((4,audio.shape[-1]));weight=torch.zeros(audio.shape[-1]);length=sr*10;step=sr*8
for start in range(0,audio.shape[-1],step):
 clip=audio[:,start:start+length];n=clip.shape[-1]
 if n<length:clip=torch.nn.functional.pad(clip,(0,length-n))
 mean=clip.mean();std=clip.std().clamp_min(1e-6)
 with torch.inference_mode():sources=model(((clip-mean)/std)[None])[0]*std
 selected=sources[[model.sources.index(k) for k in ['vocals','drums','bass','other']],:,:n].mean(1)
 fade=torch.ones(n);overlap=min(sr*2,n)
 if start:fade[:overlap]=torch.linspace(0,1,overlap)
 if start+n<audio.shape[-1]:fade[-overlap:]=torch.linspace(1,0,overlap)
 out[:,start:start+n]+=selected*fade;weight[start:start+n]+=fade
 print('STEMS',round((start+n)/sr,1),flush=True)
out/=weight.clamp_min(1e-6)
for i,k in enumerate(['vocals','drums','bass','other']):sf.write(R/f'analysis/{k}.wav',out[i].numpy(),sr,subtype='PCM_16')
print('SEPARATION_COMPLETE',flush=True)
