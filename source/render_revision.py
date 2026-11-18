"""Native 1080p60 revision: render edited shots, retain approved frames elsewhere."""
import os
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']:os.environ[k]='1'
import concurrent.futures,math,json,time,subprocess
import cv2,numpy as np
from pathlib import Path
from render import Composer
from film import MASK_MONTAGE
from visuals import R,W,H
FPS=60;N=16190;BASE=R/'output/Vice_City_My_Home_v1.0.0.mp4'
def changed_intervals(plan):
 out=[(0,3.1)]
 for s in plan:
  if s['index'] in MASK_MONTAGE or s['mode'] in ['portal','fastcar','free','duet','credits']:out.append((s['start'],min(269.84,s['end']+.34)))
 return out

def worker(job):
 i,a,b=job;f=Composer();changes=changed_intervals(f.film.plan);cap=cv2.VideoCapture(str(BASE),cv2.CAP_FFMPEG,[cv2.CAP_PROP_N_THREADS,1]);assert cap.isOpened();cap.set(cv2.CAP_PROP_POS_FRAMES,a)
 out=R/f'output/revision-{i:02d}.mp4';log=open(R/f'analysis/revision-encode-{i}.log','w');cmd=['ffmpeg','-y','-v','warning','-f','rawvideo','-pix_fmt','rgb24','-s','1920x1080','-r','60','-i','-','-an','-c:v','libx264','-preset','ultrafast','-crf','12','-threads','1','-vf','scale=out_color_matrix=bt709','-pix_fmt','yuv420p','-level:v','5.1','-maxrate','48M','-bufsize','60M','-color_primaries','bt709','-color_trc','bt709','-colorspace','bt709','-video_track_timescale','60000','-movflags','+faststart',str(out)]
 p=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=log);clock=time.monotonic();edited=0
 try:
  for n in range(a,b):
   ok,old=cap.read();assert ok,(i,n);t=n/60
   if any(lo<=t<hi for lo,hi in changes):rgb=np.asarray(f.frame(t));edited+=1
   else:rgb=cv2.cvtColor(old,cv2.COLOR_BGR2RGB)
   p.stdin.write(rgb.tobytes())
   if (n-a)%600==0:print(json.dumps(dict(chunk=i,frame=n-a,total=b-a,edited=edited,seconds=round(time.monotonic()-clock,1))),flush=True)
  p.stdin.close();assert p.wait()==0
 finally:cap.release();log.close()
 return out

def main():
 movie=R/'output/Vice_City_My_Home_1080p60_HQ.mp4'
 if not BASE.exists():movie.rename(BASE)
 step=math.ceil(N/4);jobs=[(i,a,min(a+step,N)) for i,a in enumerate(range(0,N,step))]
 with concurrent.futures.ProcessPoolExecutor(max_workers=4) as pool:parts=list(pool.map(worker,jobs))
 concat=R/'analysis/revision-concat.txt';concat.write_text(''.join(f"file '{p.as_posix()}'\n" for p in parts))
 subprocess.run(['ffmpeg','-y','-v','warning','-f','concat','-safe','0','-i',str(concat),'-i',str(BASE),'-map','0:v:0','-map','1:a:0','-c','copy','-t','269.84','-movflags','+faststart','-metadata','title=Vice City, My Home','-metadata','artist=梨茗子','-metadata','comment=Revision 1.1: official GTA VI logo and verified official promotional footage; expanded AI-assisted silhouette montage.',str(movie)],check=True)
 print('REVISION MASTER COMPLETE',movie,flush=True)
if __name__=='__main__':main()
