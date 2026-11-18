"""Conform revised native title segments and a Chinese-first subtitle layer."""
import os
os.environ['OPENBLAS_NUM_THREADS']='1'
import subprocess,time
import numpy as np
from PIL import Image
from film import Film
from visuals import R,W,H
FPS=60;N=round(269.84*FPS)
def main():
 dest=R/'output/Vice_City_My_Home_1080p60_HQ.mp4';base=R/'output/base-render.mp4'
 if not base.exists():dest.rename(base)
 f=Film();log=open(R/'analysis/final-encode.log','w')
 graph='[0:v]setpts=PTS-STARTPTS[v0];[1:v]setpts=PTS-STARTPTS[v1];[2:v]setpts=PTS-STARTPTS[v2];[v0][v1][v2]concat=n=3:v=1:a=0[cut];[3:v]format=yuva420p[subs];[cut][subs]overlay=0:920:format=yuv420:shortest=1,tpad=stop_mode=clone:stop_duration=0.034,fps=60[v]'
 cmd=['ffmpeg','-y','-v','warning','-threads','1','-i',str(R/'output/opening-cn.mp4'),'-ss','15.3','-t','248.7','-threads','1','-i',str(base),'-threads','1','-i',str(R/'output/ending-cn.mp4'),'-f','rawvideo','-pix_fmt','rgba','-s','1920x160','-r','60','-i','-','-i',str(R/'assets/song.mp3'),'-filter_complex_threads','1','-filter_complex',graph,'-map','[v]','-map','4:a:0','-r','60','-frames:v','16190','-video_track_timescale','60000','-c:v','libx264','-preset','ultrafast','-crf','12','-level:v','5.1','-threads','2','-maxrate','48M','-bufsize','96M','-pix_fmt','yuv420p','-color_primaries','bt709','-color_trc','bt709','-colorspace','bt709','-c:a','aac','-b:a','320k','-ar','48000','-t','269.84','-movflags','+faststart','-metadata','title=Vice City, My Home','-metadata','artist=梨茗子','-metadata','author=梨茗子','-metadata','comment=Chinese primary titles and captions; all GTA VI footage visually processed; unofficial fan music video.',str(dest)]
 p=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=log);clock=time.monotonic();empty=Image.new('RGBA',(W,160),(0,0,0,0));blank=empty.tobytes()
 try:
  for n in range(N):
   t=n/FPS
   if any(l['start']<=t<l['end']+.28 for l in f.lyrics):
    band=empty.copy();f.subtitle(band,t,offset_y=920);p.stdin.write(band.tobytes())
   else:p.stdin.write(blank)
   if n%1200==0:print('CONFORM',n,'/',N,round(time.monotonic()-clock,1),'sec',flush=True)
  p.stdin.close();assert p.wait()==0
 finally:log.close()
 print('CHINESE FINAL MASTER COMPLETE',dest,flush=True)
if __name__=='__main__':main()
