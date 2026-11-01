"""Standalone native render: needs only the assets and analysis included in the editable ZIP."""
from finish import *
def run():
 film=__import__('director').FilmV3();out=ROOT/'output/Dafeiyu-My-Homeland-v3.2-Native.mp4';out.parent.mkdir(parents=True,exist_ok=True)
 p=subprocess.Popen(['ffmpeg','-y','-v','warning','-filter_threads','1','-f','rawvideo','-pix_fmt','rgb24','-s','1920x1080','-r','60','-i','-','-i',str(ROOT.parent/'assets/song.mp3'),'-map','0:v','-map','1:a','-c:v','libx264','-preset','veryfast','-crf','13','-maxrate','45M','-bufsize','90M','-threads','3','-pix_fmt','yuv420p','-c:a','aac','-b:a','320k','-t','195','-movflags','+faststart',str(out)],stdin=subprocess.PIPE)
 cuts={math.ceil(t*60-1e-6) for t,_,_ in PLAN if t>0}|{round(t*60) for t in [114.31,118.12,119.2,121.74,122.65,123.55,124.65]}
 prev=None;hold=None;cut=-100
 for n in range(11700):
  frame=film.render(n/60)
  if n in cuts:hold=prev;cut=n
  if hold is not None and n-cut<20:
   u=(n-cut+1)/20;u=u*u*(3-2*u);frame=Image.blend(hold,frame,u)
  p.stdin.write(frame.tobytes());prev=frame
  if n%600==0:print(n,'/11700',flush=True)
 p.stdin.close();assert p.wait()==0
if __name__=='__main__':run()
