"""Deterministic 1080p/60fps renderer. Audio is muxed once, without a time stretch."""
import os
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']:os.environ[k]='1'
import argparse,json,math,subprocess,time,bisect,concurrent.futures
import numpy as np,cv2
from PIL import Image
from film import Film
from visuals import R,W,H,smooth
DURATION=269.84;FPS=60;N=round(DURATION*FPS)
class Composer:
 def __init__(self):self.film=Film();self.starts=[s['start'] for s in self.film.plan]
 def frame(self,t):
  f=self.film;i=max(0,bisect.bisect_right(self.starts,t)-1);s=f.plan[i];age=t-s['start'];current=f.render(t,s,False).convert('RGBA')
  if i and age<.34:
   old=f.render(t,f.plan[i-1],False).convert('RGBA');q=smooth(age/.34)
   # Feathered optical wipe: every shot enters with a moving boundary, not a hard cut.
   pos=q*(W+640)-320;blend=np.clip((pos-np.arange(W,dtype='f4')+320)/640,0,1)[None,:,None]
   a=np.asarray(old,dtype='f4')*(1-blend)+np.asarray(current,dtype='f4')*blend;current=Image.fromarray(a.astype('u1'))
  f.subtitle(current,t)
  return current.convert('RGB')

def encode(job):
 i,a,b,fps,prefix=job;f=Composer();out=R/f'output/{prefix}-{i:02d}.mp4';log=open(R/f'analysis/render-{prefix}-{i:02d}.log','w')
 cmd=['ffmpeg','-y','-v','warning','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(fps),'-i','-','-an','-c:v','libx264','-preset','fast','-crf','14','-vf','scale=out_color_matrix=bt709','-maxrate','48M','-bufsize','96M','-threads','1','-pix_fmt','yuv420p','-color_primaries','bt709','-color_trc','bt709','-colorspace','bt709','-video_track_timescale','60000','-movflags','+faststart',str(out)]
 p=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=log);clock=time.monotonic()
 try:
  for n in range(a,b):
   p.stdin.write(f.frame(n/fps).tobytes())
   if (n-a)%300==0:print(json.dumps(dict(chunk=i,frame=n-a,total=b-a,seconds=round(time.monotonic()-clock,1))),flush=True)
  p.stdin.close();assert p.wait()==0,out
 except BaseException:
  p.terminate();raise
 finally:log.close()
 return out

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--start',type=float,default=0);ap.add_argument('--end',type=float,default=DURATION);ap.add_argument('--workers',type=int,default=4);ap.add_argument('--fps',type=int,default=FPS);ap.add_argument('--name',default='master');args=ap.parse_args();fps=args.fps
 a=round(args.start*fps);b=round(args.end*fps);step=math.ceil((b-a)/args.workers);jobs=[(i,aa,min(b,aa+step),fps,args.name) for i,aa in enumerate(range(a,b,step))]
 with concurrent.futures.ProcessPoolExecutor(max_workers=args.workers) as pool:parts=list(pool.map(encode,jobs))
 concat=R/f'analysis/{args.name}-concat.txt';concat.write_text(''.join(f"file '{p.as_posix()}'\n" for p in parts))
 dest=R/'output'/('Vice_City_My_Home_1080p60_HQ.mp4' if args.name=='master' else f'{args.name}.mp4')
 subprocess.run(['ffmpeg','-y','-v','warning','-f','concat','-safe','0','-i',str(concat),'-ss',str(args.start),'-i',str(R/'assets/song.mp3'),'-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a','320k','-ar','48000','-t',str(args.end-args.start),'-movflags','+faststart','-metadata','title=Vice City, My Home','-metadata','artist=梨茗子','-metadata','author=梨茗子','-metadata','comment=Fan-made music video; official GTA VI footage: Rockstar Games; visual animation and AI-assisted assets.',str(dest)],check=True)
 print('COMPLETE',dest,flush=True)
if __name__=='__main__':main()
