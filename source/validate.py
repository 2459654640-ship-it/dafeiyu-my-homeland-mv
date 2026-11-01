from pathlib import Path
import subprocess,json,hashlib
import numpy as np
from scipy.signal import correlate

ROOT=Path(__file__).resolve().parents[1]
film=ROOT/'output/大肥鱼我的家乡_1080p.mp4'
info=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-show_entries',
    'stream=index,codec_name,codec_type,width,height,r_frame_rate,nb_read_frames,duration,color_space,color_transfer,color_primaries,sample_rate,channels,start_time:format=duration,size',
    '-of','json',str(film)]))
video=next(s for s in info['streams'] if s['codec_type']=='video')
audio=next(s for s in info['streams'] if s['codec_type']=='audio')
assert (video['width'],video['height'],video['r_frame_rate'])==(1920,1080,'30/1')
assert int(video['nb_read_frames'])==5850
assert video['color_space']=='bt709'
assert abs(float(info['format']['duration'])-195)<.05
assert audio['sample_rate']=='48000' and audio['channels']==2
assert abs(float(audio['start_time']))<.025
result={'media':info,'audio_sync_checks':[]}

def samples(path,start,duration=6):
    raw=subprocess.check_output(['ffmpeg','-v','error','-ss',str(start),'-i',str(path),'-t',str(duration),'-vn','-ac','1','-ar','12000','-f','f32le','-'])
    return np.frombuffer(raw,dtype=np.float32)
for start in [17,64,143,183]:
    a=samples(ROOT/'assets/song.mp3',start);b=samples(film,start)
    n=min(len(a),len(b));a=a[:n];b=b[:n]
    c=correlate(a,b,mode='full',method='fft');lags=np.arange(-n+1,n)
    chosen=np.flatnonzero(np.abs(lags)<=2400);idx=chosen[np.argmax(c[chosen])]
    lag=int(lags[idx]);rho=float(c[idx]/(np.linalg.norm(a)*np.linalg.norm(b)))
    result['audio_sync_checks'].append({'at_seconds':start,'offset_ms':lag/12,'correlation':rho})
    assert abs(lag)<24 and rho>.97,(start,lag,rho)
    print('AUDIO_SYNC',result['audio_sync_checks'][-1],flush=True)

# Full media decode is required, not just a successful container probe.
decoded=subprocess.run(['ffmpeg','-v','error','-i',str(film),'-f','null','-'],capture_output=True,text=True)
assert decoded.returncode==0 and not decoded.stderr,decoded.stderr
result['full_decode']='passed'

# Inspect brightness coverage at five-second intervals. Intentional opening black is excluded.
raw=subprocess.check_output(['ffmpeg','-v','error','-i',str(film),'-vf',r'select=not(mod(n\,150)),scale=320:180','-fps_mode','vfr','-an','-f','rawvideo','-pix_fmt','rgb24','-'])
frames=np.frombuffer(raw,dtype=np.uint8).reshape(-1,180,320,3)
coverage=[]
for i,frame in enumerate(frames):
    fraction=float(np.mean(np.max(frame[12:-12],axis=2)>35))
    coverage.append({'seconds':i*5,'visible_pixel_fraction':fraction})
    if i:assert fraction>.005,(i*5,fraction)
result['frame_samples']=coverage

lyrics=json.loads((ROOT/'analysis/lyrics.json').read_text())
assert len(lyrics)==16
for i,line in enumerate(lyrics):
    assert 0<=line['start']<line['end']<195
    if i:assert line['start']>=lyrics[i-1]['end']
result['subtitle_cues']=16
result['subtitle_method']='vocal-stem CTC alignment with structural constraints; not human ear-verified word by word'
result['sha256']=hashlib.sha256(film.read_bytes()).hexdigest()
result['status']='passed'
(ROOT/'output/validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
print('VALIDATION_PASSED',json.dumps({'frames':video['nb_read_frames'],'seconds':info['format']['duration'],'sampled_frames':len(frames),'bytes':info['format']['size']}),flush=True)
