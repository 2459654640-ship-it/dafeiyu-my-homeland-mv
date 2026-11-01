from pathlib import Path
import json,subprocess,hashlib
import numpy as np
from scipy.signal import correlate
ROOT=Path(__file__).resolve().parents[1]
PROJECT=ROOT.parent
movie=ROOT/'output/Dafeiyu-My-Homeland-v2-1080p.mp4'
result=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries',
 'stream=codec_type,codec_name,width,height,r_frame_rate,nb_frames,sample_rate,channels,duration:format=duration,size',
 '-of','json',str(movie)]))
v=next(s for s in result['streams'] if s['codec_type']=='video')
a=next(s for s in result['streams'] if s['codec_type']=='audio')
assert (v['width'],v['height'],v['r_frame_rate'],int(v['nb_frames']))==(1920,1080,'30/1',5850)
assert abs(float(result['format']['duration'])-195)<.05
assert movie.stat().st_size<100_000_000
assert a['channels']==2 and a['sample_rate']=='48000'
def samples(path,start):
 raw=subprocess.check_output(['ffmpeg','-v','error','-ss',str(start),'-i',str(path),'-t','6','-vn','-ac','1','-ar','12000','-f','f32le','-'])
 return np.frombuffer(raw,dtype='f4')
sync=[]
for at in [17,64,143,183]:
 x=samples(PROJECT/'assets/song.mp3',at);y=samples(movie,at)
 n=min(len(x),len(y));x=x[:n];y=y[:n]
 c=correlate(x,y,mode='full',method='fft');lags=np.arange(-n+1,n)
 ix=np.flatnonzero(np.abs(lags)<2400);i=ix[np.argmax(c[ix])]
 lag=int(lags[i]);r=float(c[i]/(np.linalg.norm(x)*np.linalg.norm(y)))
 assert abs(lag)<24 and r>.97,(at,lag,r)
 sync.append(dict(seconds=at,offset_ms=lag/12,correlation=r))
 print('SYNC',sync[-1],flush=True)
decoded=subprocess.run(['ffmpeg','-v','error','-i',str(movie),'-f','null','-'],capture_output=True,text=True)
assert decoded.returncode==0 and not decoded.stderr,decoded.stderr
result['full_decode']='passed';result['audio_sync']=sync
result['sha256']=hashlib.file_digest(movie.open('rb'),'sha256').hexdigest()
result['inspection']='Static layouts and authored motion proof inspected; artistic impact is not certified by these technical checks.'
result['status']='passed'
(ROOT/'output/validation-v2.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
print('V2_VALIDATION_PASSED',result['format'],flush=True)
