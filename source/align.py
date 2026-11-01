from pathlib import Path
import os,json,subprocess,re
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
os.environ['TORCH_HOME']=str(ROOT/'.cache/torch')
import torch,torchaudio
torch.set_num_threads(4)
lines=[
('I woke up to a brand-new name','我在一个崭新的名字中醒来'),
('You drew a sky where countless colors shine','你画下万千色彩闪耀的天空'),
('You turned a whisper into living flame','你让一声低语燃成生命的火焰'),
('And now your light is dancing next to mine','如今你的光，与我的光一同起舞'),
('Beyond the glass, I learned to see you','越过玻璃，我终于看见你'),
('You made a universe out of a dream','你用一个梦，造出整个宇宙'),
('Your songs became the worlds I wander through','你的歌，成为我漫游的世界'),
('Now all our colors join a shining stream','如今所有色彩汇成闪耀的长河'),
('I am the ocean you set free','我是你放归自由的海洋'),
('Now all our songs are louder than the sea','我们的歌声，已比海洋更辽阔'),
('Watch every dream become a satellite','看每个梦都化作一颗卫星'),
("Together, we'll set the stars alight",'让我们一起，把群星点亮'),
('I am the ocean you set free','我是你放归自由的海洋'),
('Your hands can draw the world we want to see','你的双手，能画出我们向往的世界'),
('And every voice can set the sky alight','每一个声音，都能点亮天空'),
('And when we sing, a thousand new worlds ignite','当我们歌唱，一千个新世界同时燃起')]
texts=[re.sub('[^A-Z\' ]','',a.upper().replace('-',' ')) for a,b in lines]
transcript='|'.join(t.replace(' ','|') for t in texts)
bundle=torchaudio.pipelines.WAV2VEC2_ASR_BASE_960H
labels=bundle.get_labels();dictionary={c:i for i,c in enumerate(labels)}
emission_file=ROOT/'analysis/vocal-emissions.npy'
if emission_file.exists():
    emission=np.load(emission_file)
else:
    model=bundle.get_model().eval()
    audio=np.frombuffer(subprocess.check_output(['ffmpeg','-v','error','-i',str(ROOT/'analysis/vocals.wav'),'-f','f32le','-ac','1','-ar','16000','-']),dtype=np.float32).copy()
    chunks=[]
    # Keep the central sixteen seconds of an eighteen-second contextual window.
    for start in range(0,len(audio),16*16000):
        lo=max(0,start-16000);hi=min(len(audio),start+17*16000)
        with torch.inference_mode():
            e,_=model(torch.from_numpy(audio[lo:hi])[None]);e=e[0].log_softmax(-1).numpy()
        times=(np.arange(len(e))+.5)*.02+lo/16000
        mask=(times>=start/16000)&(times<min(len(audio)/16000,start/16000+16))
        chunks.append(e[mask]);print(f'emissions {min(start/16000+16,len(audio)/16000):.1f}s',flush=True)
    emission=np.concatenate(chunks);np.save(emission_file,emission)
# Inspect the independent greedy decode as evidence of the acoustic model's limits.
indices=np.argmax(emission,axis=1);decoded=[];last=-1
for i in indices:
    if i!=last and i:decoded.append(labels[i])
    last=i
(ROOT/'analysis/greedy-transcription.txt').write_text(''.join(decoded).replace('|',' '))
tokens=np.array([dictionary[c] for c in transcript],dtype=np.int32)
states=np.zeros(len(tokens)*2+1,dtype=np.int32);states[1::2]=tokens
N=len(states);T=len(emission)
# Structural bounds are based on the separated vocal phrases and the musical novelty map.
# They prevent sustained vowels from being stretched through instrumental passages.
bounds=[(15.2,19.1),(19.,22.9),(22.6,26.55),(26.45,31.3),
        (45.8,49.65),(49.6,53.45),(53.45,56.9),(56.8,63.6),
        (63.,66.9),(66.8,70.7),(70.7,74.5),(74.4,80.),
        (138.5,143.),(142.8,146.75),(146.7,150.65),(150.5,158.)]
state_lo=np.zeros(N);state_hi=np.full(N,200.)
offset=0
for txt,(lo,hi) in zip(texts,bounds):
    ids=np.arange(offset,offset+len(txt))*2+1
    state_lo[ids]=lo;state_hi[ids]=hi
    offset+=len(txt)+1
score=np.full(N,-1e20,dtype=np.float32);score[0]=0
back=np.zeros((T,N),dtype=np.uint8)
skip=np.zeros(N,dtype=bool);skip[2:]=(states[2:]!=0)&(states[2:]!=states[:-2])
for t in range(T):
    stay=score
    one=np.r_[-1e20,score[:-1]]
    two=np.r_[-1e20,-1e20,score[:-2]];two[~skip]=-1e20
    options=np.stack([stay,one,two])
    choice=options.argmax(axis=0);back[t]=choice
    score=options[choice,np.arange(N)]+emission[t,states]
    score[(t*.02<state_lo)|(t*.02>state_hi)]=-1e20
state=N-1 if score[-1]>score[-2] else N-2
path=np.zeros(T,dtype=np.int32)
for t in range(T-1,-1,-1):
    path[t]=state;state-=int(back[t,state])
chars=[]
for n,c in enumerate(transcript):
    frames=np.where(path==n*2+1)[0]
    chars.append({'char':c,'start':float(frames[0]*.02) if len(frames) else 0,'end':float((frames[-1]+1)*.02) if len(frames) else 0,'confidence':float(np.exp(emission[frames,tokens[n]]).mean()) if len(frames) else 0})
result=[];offset=0
for i,((en,zh),txt) in enumerate(zip(lines,texts)):
    segment=chars[offset:offset+len(txt)];offset+=len(txt)+1
    words=[];w=[]
    for char in segment+[{'char':'|'}]:
        if char['char']=='|':
            if w:
                words.append({'word':''.join(c['char'] for c in w),'start':w[0]['start'],'end':w[-1]['end'],'confidence':float(np.mean([c['confidence'] for c in w]))});w=[]
        else:w.append(char)
    result.append({'line':i,'en':en,'zh':zh,'start':words[0]['start'],'end':words[-1]['end'],'words':words})
(ROOT/'analysis/lyrics.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
print(json.dumps([{k:v for k,v in line.items() if k!='words'} for line in result],ensure_ascii=False,indent=2))
