from pathlib import Path
import sys,os,json,argparse,time,subprocess
from PIL import Image
from director import FilmV3
from ui import ROOT,W,H

PROJECT=ROOT.parent

def render(ranges,out,fps=60,video_only=False):
    film=FilmV3();out=Path(out);out.parent.mkdir(parents=True,exist_ok=True)
    duration=sum(b-a for a,b in ranges);cmd=['ffmpeg','-y','-v','warning','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(fps),'-i','-']
    if not video_only:
        cmd+=['-i',str(PROJECT/'assets/song.mp3')]
        af=[]
        for i,(a,b) in enumerate(ranges):af.append(f'[1:a]atrim=start={a}:end={b},asetpts=PTS-STARTPTS[a{i}]')
        if len(ranges)>1:af.append(''.join(f'[a{i}]' for i in range(len(ranges)))+f'concat=n={len(ranges)}:v=0:a=1[audio]');audio='[audio]'
        else:audio='[a0]'
        cmd+=['-filter_complex',';'.join(af),'-map','0:v:0','-map',audio,'-c:a','aac','-b:a','320k','-ar','48000']
    else:cmd+=['-map','0:v:0','-an']
    # This is the only encode of the delivered picture. No low-bitrate GitHub-size transcode follows.
    cmd+=['-c:v','libx264','-preset','fast','-crf','14','-maxrate','45M','-bufsize','90M','-threads','1','-g',str(fps*2),
          '-pix_fmt','yuv420p','-t',str(duration),'-color_primaries','bt709','-color_trc','bt709','-colorspace','bt709',
          '-movflags','+faststart',str(out)]
    err=open(str(out)+'.ffmpeg.log','w');proc=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=err)
    n=0;total=sum(round((b-a)*fps) for a,b in ranges);start=time.monotonic()
    try:
        for a,b in ranges:
            for i in range(round((b-a)*fps)):
                image=film.render(a+i/fps)
                proc.stdin.write(image.tobytes());n+=1
                if n%120==0:print(f'FRAME {n}/{total} {n/(time.monotonic()-start):.2f}fps song={a+i/fps:.3f}',flush=True)
    finally:proc.stdin.close()
    code=proc.wait();err.close()
    if code:raise RuntimeError(f'ffmpeg failed: {code}')
    print('COMPLETE',str(out),'frames',n,'seconds',round(time.monotonic()-start,1),flush=True)

def parallel_master():
    (ROOT/'output').mkdir(parents=True,exist_ok=True);(ROOT/'analysis').mkdir(parents=True,exist_ok=True)
    specs=[(0,63.7),(63.7,129.55),(129.55,195.)]
    jobs=[]
    for i,(a,b) in enumerate(specs):
        path=ROOT/f'output/chunk-{i}.mp4';log=open(ROOT/f'analysis/chunk-{i}.log','w')
        cmd=[sys.executable,__file__,'--ranges',f'{a}:{b}','--output',str(path),'--video-only']
        jobs.append((subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT),path,log))
    while any(p.poll() is None for p,_,_ in jobs):time.sleep(3)
    for p,_,log in jobs:
        log.close()
        if p.returncode:raise RuntimeError(f'chunk failed {p.returncode}')
    concat=ROOT/'output/chunks.txt'
    concat.write_text(''.join("file '"+str(path)+"'\n" for _,path,_ in jobs))
    out=ROOT/'output/Dafeiyu-My-Homeland-v3-1080p60-Master.mp4'
    cmd=['ffmpeg','-y','-v','warning','-f','concat','-safe','0','-i',str(concat),'-i',str(PROJECT/'assets/song.mp3'),
         '-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a','320k','-ar','48000','-t','195','-movflags','+faststart',
         '-metadata','title=大肥鱼我的家乡 / v3 Beyond the Terminal',str(out)]
    subprocess.run(cmd,check=True)
    print('MASTER_COMPLETE',str(out),out.stat().st_size,flush=True)

def main():
    p=argparse.ArgumentParser();p.add_argument('--stills',action='store_true');p.add_argument('--times',default='0.3,2,6.4,7.7,9,10.2,12,17,20,28,35,43,47.6,51,55,59,64.5,66.4,69,73,77,82,85,89,93,97,101,105,109,112,116,120,124,127,131,137,141,144.5,148,153.7,156,160,164,169,176,183,190')
    p.add_argument('--ranges',default='0:195');p.add_argument('--output',default=str(ROOT/'output/preview-master.mp4'));p.add_argument('--fps',type=int,default=60);p.add_argument('--video-only',action='store_true');p.add_argument('--parallel-master',action='store_true')
    a=p.parse_args()
    if a.parallel_master:parallel_master()
    elif a.stills:
        (ROOT/'frames').mkdir(parents=True,exist_ok=True)
        film=FilmV3()
        for t in map(float,a.times.split(',')):
            film.render(t).save(ROOT/f'frames/frame-{t:07.3f}.jpg',quality=96)
            print('STILL',t,flush=True)
        (ROOT/'analysis/shot-plan.json').write_text(json.dumps(film.plan,ensure_ascii=False,indent=2))
    else:render([tuple(map(float,s.split(':'))) for s in a.ranges.split(',')],a.output,a.fps,a.video_only)

if __name__=='__main__':main()
