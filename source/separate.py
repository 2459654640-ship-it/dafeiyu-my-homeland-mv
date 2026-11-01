from pathlib import Path
import os,subprocess
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
os.environ['TORCH_HOME']=str(ROOT/'.cache/torch')
import torch,torchaudio,soundfile as sf
torch.set_num_threads(4)
bundle=torchaudio.pipelines.HDEMUCS_HIGH_MUSDB_PLUS
model=bundle.get_model().eval()
sr=bundle.sample_rate
raw=subprocess.check_output(['ffmpeg','-v','error','-i',str(ROOT/'assets/song.mp3'),'-f','f32le','-ac','2','-ar',str(sr),'-'])
audio=torch.from_numpy(np.frombuffer(raw,dtype=np.float32).reshape(-1,2).copy().T)
out=torch.zeros_like(audio);weight=torch.zeros(audio.shape[-1]);length=sr*10;step=sr*8
for start in range(0,audio.shape[-1],step):
    clip=audio[:,start:start+length];size=clip.shape[-1]
    if size<length:clip=torch.nn.functional.pad(clip,(0,length-size))
    mean=clip.mean();std=clip.std().clamp_min(1e-6)
    with torch.inference_mode():
        sources=model(((clip-mean)/std)[None])[0]*std
    vocal=sources[model.sources.index('vocals'),:,:size]
    fade=torch.ones(size)
    overlap=min(sr*2,size)
    if start:fade[:overlap]=torch.linspace(0,1,overlap)
    if start+size<audio.shape[-1]:fade[-overlap:]=torch.linspace(1,0,overlap)
    out[:,start:start+size]+=vocal*fade
    weight[start:start+size]+=fade
    print(f'vocals {min((start+size)/sr,audio.shape[-1]/sr):.1f}s',flush=True)
out/=weight.clamp_min(1e-6)
sf.write(ROOT/'analysis/vocals.wav',out.T.numpy(),sr,subtype='PCM_16')
print('VOCAL_SEPARATION_COMPLETE',flush=True)
