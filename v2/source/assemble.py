"""Reuse the completed full render; replace only the two contrast fixes and their outgoing transitions."""
from pathlib import Path
import subprocess,json
ROOT=Path(__file__).resolve().parents[1]
files=['大肥鱼我的家乡_v2.mp4','patch-chorus.mp4','patch-chorus-tail.mp4','patch-climax.mp4','patch-climax-tail.mp4']
expected=[5850,166,24,122,25]
for name,n in zip(files,expected):
    path=ROOT/'output'/name
    info=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=nb_frames','-of','json',str(path)]))
    assert int(info['streams'][0]['nb_frames'])==n,(name,info)
cmd=['ffmpeg','-y','-v','warning']
for name in files:cmd+=['-i',str(ROOT/'output'/name)]
fc=';'.join([
'[0:v]split=3[x0][x3][x6]',
'[x0]trim=start_frame=0:end_frame=2235,setpts=PTS-STARTPTS[v0]',
'[1:v]setpts=PTS-STARTPTS[v1]',
'[2:v]setpts=PTS-STARTPTS[v2]',
'[x3]trim=start_frame=2425:end_frame=4522,setpts=PTS-STARTPTS[v3]',
'[3:v]setpts=PTS-STARTPTS[v4]',
'[4:v]setpts=PTS-STARTPTS[v5]',
'[x6]trim=start_frame=4669:end_frame=5850,setpts=PTS-STARTPTS[v6]',
'[v0][v1][v2][v3][v4][v5][v6]concat=n=7:v=1:a=0[video]'])
out=ROOT/'output/Dafeiyu-My-Homeland-v2-1080p.mp4'
cmd+=['-filter_complex',fc,'-map','[video]','-map','0:a:0','-c:v','libx264','-preset','fast','-threads','4',
      '-b:v','3400k','-maxrate','3800k','-bufsize','7600k','-pix_fmt','yuv420p','-r','30','-c:a','copy','-t','195',
      '-movflags','+faststart','-color_primaries','bt709','-color_trc','bt709','-colorspace','bt709',
      '-metadata','title=大肥鱼我的家乡 / v2 terminal motion',str(out)]
subprocess.run(cmd,check=True)
assert out.stat().st_size<100_000_000
print('FINAL_ASSEMBLED',out,out.stat().st_size,flush=True)
