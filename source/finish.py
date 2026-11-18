"""Conform late title/caption revisions onto an existing full-resolution render."""
import os
os.environ['OPENBLAS_NUM_THREADS']='1'
import subprocess,sys,json,time
from pathlib import Path
import cv2,numpy as np
from PIL import Image
from film import Film
from visuals import R,W,H
FPS=60;N=round(269.84*FPS)
def cap(p):
 c=cv2.VideoCapture(str(p),cv2.CAP_FFMPEG,[cv2.CAP_PROP_N_THREADS,1]);assert c.isOpened(),p;return c

def main():
 dest=R/'output/Vice_City_My_Home_1080p60_HQ.mp4';base=R/'output/base-render.mp4'
 if not base.exists():dest.rename(base)
 c=cap(base);opening=cap(R/'output/opening-cn.mp4');ending=cap(R/'output/ending-cn.mp4');f=Film();count=round(c.get(cv2.CAP_PROP_FRAME_COUNT));assert count==N,(count,N)
 log=open(R/'analysis/final-encode.log','w');cmd=['ffmpeg','-y','-v','warning','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r','60','-i','-','-i',str(R/'assets/song.mp3'),'-map','0:v:0','-map','1:a:0','-c:v','libx264','-preset','fast','-crf','12','-threads','2','-vf','scale=out_color_matrix=bt709','-maxrate','48M','-bufsize','96M','-pix_fmt','yuv420p','-color_primaries','bt709','-color_trc','bt709','-colorspace','bt709','-c:a','aac','-b:a','320k','-ar','48000','-t','269.84','-movflags','+faststart','-metadata','title=Vice City, My Home','-metadata','artist=梨茗子','-metadata','author=梨茗子','-metadata','comment=Chinese primary titles and captions; all GTA VI footage visually processed; unofficial fan music video.',str(dest)]
 p=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=log);clock=time.monotonic()
 try:
  for n in range(N):
   ok,frame=c.read();assert ok,n;t=n/FPS
   if n<round(15.3*FPS):ok,frame=opening.read();assert ok,('opening',n)
   elif n>=264*FPS:ok,frame=ending.read();assert ok,('ending',n)
   if any(l['start']<=t<l['end']+.28 for l in f.lyrics):
    im=Image.fromarray(cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)).convert('RGBA');f.subtitle(im,t);rgb=np.asarray(im.convert('RGB'))
   else:rgb=cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)
   p.stdin.write(rgb.tobytes())
   if n%1200==0:print('CONFORM',n,'/',N,round(time.monotonic()-clock,1),'sec',flush=True)
  p.stdin.close();assert p.wait()==0
 finally:
  c.release();opening.release();ending.release();log.close()
 print('CHINESE FINAL MASTER COMPLETE',dest,flush=True)
if __name__=='__main__':main()
