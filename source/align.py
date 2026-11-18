from pathlib import Path
import os,json,subprocess,re
import numpy as np
from lyrics_data import LINES
R=Path(__file__).resolve().parents[1];os.environ.setdefault('TORCH_HOME',str(R/'.cache/torch'))
import torch,torchaudio
torch.set_num_threads(3);bundle=torchaudio.pipelines.WAV2VEC2_ASR_BASE_960H;labels=bundle.get_labels();dictionary={c:i for i,c in enumerate(labels)}
y=np.frombuffer(subprocess.check_output(['ffmpeg','-v','error','-i',str(R/'analysis/vocals.wav'),'-f','f32le','-ac','1','-ar','16000','-']),dtype='f4').copy()
if (R/'analysis/emissions.npy').exists():em=np.load(R/'analysis/emissions.npy')
else:
 model=bundle.get_model().eval();chunks=[]
 for start in range(0,len(y),16*16000):
  lo=max(0,start-16000);hi=min(len(y),start+17*16000)
  with torch.inference_mode():e,_=model(torch.from_numpy(y[lo:hi])[None]);e=e[0].log_softmax(-1).numpy()
  times=(np.arange(len(e))+.5)*.02+lo/16000;keep=(times>=start/16000)&(times<min(len(y)/16000,start/16000+16));chunks.append(e[keep]);print('EMISSIONS',round(start/16000+16,1),flush=True)
 em=np.concatenate(chunks);np.save(R/'analysis/emissions.npy',em)
def decode(z):
 out=[];prev=-1
 for i in z.argmax(1):
  if i!=prev and i:out.append(labels[i])
  prev=i
 return ''.join(out).replace('|',' ')
(R/'analysis/greedy.txt').write_text('\n'.join(f'{k*.02:.1f} '+decode(em[k:k+500]) for k in range(0,len(em),500)))
texts=[re.sub("[^A-Z' ]",'',x['en'].upper().replace('-',' ')) for x in LINES];transcript='|'.join(t.replace(' ','|') for t in texts);tokens=np.array([dictionary[c] for c in transcript],dtype='i4')
states=np.zeros(len(tokens)*2+1,dtype='i4');states[1::2]=tokens;N=len(states);T=len(em);score=np.full(N,-1e20,dtype='f4');score[0]=0;back=np.zeros((T,N),dtype='u1');skip=np.zeros(N,bool);skip[2:]=(states[2:]!=0)&(states[2:]!=states[:-2])
# Prevent consonants and long vowels from being stretched into instrumental gaps.
lo=np.zeros(N);hi=np.full(N,270.);offset=0
for i,txt in enumerate(texts):
 ids=np.arange(offset,offset+len(txt))*2+1;offset+=len(txt)+1
 if i==7:hi[ids]=64.8
 if i==23:hi[ids]=148.2
 if i==36:lo[ids]=221.7;hi[ids]=226.15
for t in range(T):
 one=np.r_[-1e20,score[:-1]];two=np.r_[-1e20,-1e20,score[:-2]];two[~skip]=-1e20;opts=np.stack([score,one,two]);choice=opts.argmax(0);back[t]=choice;score=opts[choice,np.arange(N)]+em[t,states];score[(t*.02<lo)|(t*.02>hi)]=-1e20
state=N-1 if score[-1]>score[-2] else N-2;path=np.zeros(T,dtype='i4')
for t in range(T-1,-1,-1):path[t]=state;state-=int(back[t,state])
chars=[]
for n,c in enumerate(transcript):
 f=np.where(path==n*2+1)[0];chars.append(dict(char=c,start=float(f[0]*.02) if len(f) else 0,end=float((f[-1]+1)*.02) if len(f) else 0,confidence=float(np.exp(em[f,tokens[n]]).mean()) if len(f) else 0))
result=[];offset=0
for i,(line,txt) in enumerate(zip(LINES,texts)):
 seg=chars[offset:offset+len(txt)];offset+=len(txt)+1;words=[];w=[]
 for ch in seg+[{'char':'|'}]:
  if ch['char']=='|':
   if w:words.append(dict(word=''.join(x['char'] for x in w),start=w[0]['start'],end=w[-1]['end'],confidence=float(np.mean([x['confidence'] for x in w]))));w=[]
  else:w.append(ch)
 result.append(line|dict(index=i,start=words[0]['start'],end=words[-1]['end'],words=words))
(R/'analysis/lyrics.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
for l in result:print(l['index'],l['section'],l['start'],l['end'],l['en'],flush=True)
