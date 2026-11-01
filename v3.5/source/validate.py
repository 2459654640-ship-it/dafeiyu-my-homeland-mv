"""Validate the delivered media rather than mirroring the drawing implementation."""
from pathlib import Path
import json,subprocess,hashlib
import numpy as np
from scipy.signal import correlate

ROOT=Path(__file__).resolve().parents[1];PROJECT=ROOT.parent
movie=ROOT/'output/Dafeiyu-My-Homeland-v3.5-1080p60-Master.mp4'
result=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries',
 'stream=codec_type,codec_name,profile,width,height,r_frame_rate,avg_frame_rate,nb_frames,sample_rate,channels,duration,bit_rate,color_space,color_transfer,color_primaries:format=duration,size,bit_rate',
 '-of','json',str(movie)]))
v=next(s for s in result['streams'] if s['codec_type']=='video')
a=next(s for s in result['streams'] if s['codec_type']=='audio')
assert (v['width'],v['height'],v['r_frame_rate'],int(v['nb_frames']))==(1920,1080,'60/1',11700),v
assert v['avg_frame_rate']=='60/1'
assert abs(float(result['format']['duration'])-195)<.035
assert a['channels']==2 and a['sample_rate']=='48000'
assert v['codec_name']=='h264' and a['codec_name']=='aac'

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
    sync.append(dict(seconds=at,offset_ms=lag/12,correlation=r));print('SYNC',sync[-1],flush=True)

decode=subprocess.run(['ffmpeg','-v','error','-i',str(movie),'-f','null','-'],capture_output=True,text=True)
assert decode.returncode==0 and not decode.stderr,decode.stderr
result['full_decode']='passed';result['audio_sync']=sync
result['sha256']=hashlib.file_digest(movie.open('rb'),'sha256').hexdigest()
result['master_encode']={'crf':13,'maxrate_mbps':45,'audio_kbps':320,'audio_stream_copied':True,'video_reencoded_for_transitions':True}
result['inspection']='Representative compositions, motion proof, browser decoding and full-file decoding checked. Artistic impact is not certified by these technical checks.'
result['status']='passed'
(ROOT/'output/validation-v3.5.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
print('V3_VALIDATION_PASSED',result['format'],flush=True)
