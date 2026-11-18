"""Validate editorial inputs and, when present, the exported video and audio clock."""
from pathlib import Path
import json,subprocess,hashlib
import numpy as np
R=Path(__file__).resolve().parents[1]
def audio(path):return np.frombuffer(subprocess.check_output(['ffmpeg','-v','error','-i',str(path),'-ac','1','-ar','8000','-f','f32le','-']),dtype='f4')
def check():
 lines=json.loads((R/'analysis/lyrics.json').read_text());schedule=json.loads((R/'analysis/shot-sources.json').read_text());items=sorted([i for v in schedule.values() for i in v],key=lambda x:x['start'])
 assert len(lines)==45
 for a,b in zip(items,items[1:]):assert a['end']<=b['start']+.001,(a['name'],b['name'])
 last=0
 for l in lines:
  assert l['start']>=last-.01 and l['end']>l['start'],l['index'];last=l['end']
  for w in l['words']:assert l['start']<=w['start']<w['end']<=l['end']+.001,(l['index'],w)
 result=dict(bilingual_lines=len(lines),unique_official_excerpts=len(items),source_intervals_overlap=False,word_times_monotonic=True)
 for n in ['opening-poster','unified-mask','characters-atlas','jason','lucia','poses-atlas','jason-walk','jason-lean','lucia-walk','lucia-turn']:assert (R/f'assets/{n}.png').exists(),n
 movie=R/'output/Vice_City_My_Home_1080p60_HQ.mp4'
 if movie.exists():
  probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_format','-show_streams','-of','json',str(movie)]));v=next(s for s in probe['streams'] if s['codec_type']=='video');a=next(s for s in probe['streams'] if s['codec_type']=='audio')
  assert int(v['nb_frames'])==16190;assert probe['format']['tags'].get('artist')=='梨茗子';assert (v['width'],v['height'],v['r_frame_rate'])==(1920,1080,'60/1');assert abs(float(v['duration'])-269.84)<.03;assert abs(float(a['duration'])-269.84)<.03
  subprocess.run(['ffmpeg','-v','error','-xerror','-err_detect','explode','-i',str(movie),'-f','null','-'],check=True)
  ref=audio(R/'assets/song.mp3');got=audio(movie);clocks=[]
  for sec in [40,120,180,240]:
   st=sec*8000;n=32000;x=ref[st:st+n].astype('f8');y=got[st:st+n].astype('f8');size=65536;corr=np.fft.irfft(np.fft.rfft(y,size)*np.conj(np.fft.rfft(x,size)),size);lags=np.arange(-400,401);lag=int(lags[np.argmax(corr[lags%size])]);lo=max(0,lag);hi=min(n,n+lag);p=y[lo:hi];q=x[lo-lag:hi-lag];r=float(np.corrcoef(p,q)[0,1]);assert abs(lag)<=8 and r>.97,(sec,lag,r);clocks.append(dict(t=sec,offset_ms=lag/8,correlation=round(r,6)))
  result.update(artist=probe['format']['tags']['artist'],frames=int(v['nb_frames']),width=v['width'],height=v['height'],fps=v['r_frame_rate'],video_duration=float(v['duration']),audio_duration=float(a['duration']),video_bitrate=int(v.get('bit_rate',0)),audio_bitrate=int(a.get('bit_rate',0)),full_decode_passed=True,audio_checks=clocks,size_bytes=movie.stat().st_size,sha256=hashlib.file_digest(open(movie,'rb'),'sha256').hexdigest())
 (R/'output/validation.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
if __name__=='__main__':check()
