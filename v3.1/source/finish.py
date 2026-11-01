"""Minimal v3.1 conform: replace two picture segments and soften scene cuts, preserving audio timing."""
from pathlib import Path
import subprocess,sys,json,math
from PIL import Image
from director import PLAN
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT.parent/'v3/output/Dafeiyu-My-Homeland-v3-1080p60-Master.mp4'
OUT=ROOT/'output/Dafeiyu-My-Homeland-v3.1-1080p60-Master.mp4'
W,H,FPS=1920,1080,60;SIZE=W*H*3

def decoder(p):return subprocess.Popen(['ffmpeg','-v','error','-threads','1','-filter_threads','1','-i',str(p),'-an','-filter_threads','1','-f','rawvideo','-pix_fmt','rgb24','-threads','1','-'],stdout=subprocess.PIPE)
def read(p):
 data=p.stdout.read(SIZE)
 if len(data)!=SIZE:raise RuntimeError('Incomplete decoded frame')
 return data

def main():
 original=decoder(BASE);patches=[(0,636,decoder(ROOT/'output/opening.mp4')),(6630,7545,decoder(ROOT/'output/code.mp4'))]
 cuts=sorted(set([math.ceil(t*60-1e-6) for t,_,_ in PLAN if t>0]+[round(t*60) for t in [114.31,118.12,119.2,121.74,122.65,123.55,124.65]]))
 cmd=['ffmpeg','-y','-v','warning','-filter_threads','1','-f','rawvideo','-pix_fmt','rgb24','-s','1920x1080','-r','60','-i','-','-i',str(BASE),'-map','0:v','-map','1:a','-c:a','copy','-c:v','libx264','-preset','veryfast','-crf','13','-maxrate','45M','-bufsize','90M','-threads','3','-g','120','-pix_fmt','yuv420p','-color_primaries','bt709','-color_trc','bt709','-colorspace','bt709','-t','195','-movflags','+faststart',str(OUT)]
 log=open(ROOT/'analysis/conform-ffmpeg.log','w');enc=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=log)
 previous=None;hold=None;cut=-100
 for n in range(11700):
  frame=read(original)
  for a,b,p in patches:
   if a<=n<b:frame=read(p);break
  if n in cuts:hold=previous;cut=n
  if hold is not None and n-cut<20:
   u=(n-cut+1)/20;u=u*u*(3-2*u)
   frame=Image.blend(Image.frombytes('RGB',(W,H),hold),Image.frombytes('RGB',(W,H),frame),u).tobytes()
  enc.stdin.write(frame);previous=frame
  if n%600==0:print('CONFORM',n,'/11700',flush=True)
 enc.stdin.close();assert enc.wait()==0
 original.stdout.close();assert original.wait()==0
 for _,_,p in patches:p.stdout.close();assert p.wait()==0
 print('FINAL_COMPLETE',OUT,OUT.stat().st_size,flush=True)
if __name__=='__main__':main()
