"""Pad a single final frame lost to filter EOF, then normalize the H.264 level.

No existing frame or audio packet is re-encoded. The appended frame is copied
visually from the existing final fade frame.
"""
import json,subprocess,cv2
from pathlib import Path
from visuals import R
(R/'frames').mkdir(exist_ok=True)
p=R/'output/Vice_City_My_Home_1080p60_HQ.mp4'
probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-of','json',str(p)]));v=next(s for s in probe['streams'] if s['codec_type']=='video');n=int(v['nb_frames']);assert n in [16189,16190],n
output=R/'output/master-verified-header.mp4'
if n==16189:
 c=cv2.VideoCapture(str(p));c.set(cv2.CAP_PROP_POS_FRAMES,n-1);ok,frame=c.read();assert ok;c.release();last=R/'frames/final-fade-frame.png';cv2.imwrite(str(last),frame)
 tail=R/'output/tail-one-frame.mp4'
 subprocess.run(['ffmpeg','-y','-v','error','-loop','1','-i',str(last),'-r','60','-frames:v','1','-an','-c:v','libx264','-preset','ultrafast','-crf','12','-level:v','5.1','-pix_fmt','yuv420p','-color_primaries','bt709','-color_trc','bt709','-colorspace','bt709','-video_track_timescale','60000',str(tail)],check=True)
 concat=R/'analysis/tail-conform.txt';concat.write_text(f"file '{p.as_posix()}'\nduration {n/60:.9f}\nfile '{tail.as_posix()}'\nduration {1/60:.9f}\n")
 cmd=['ffmpeg','-y','-v','warning','-f','concat','-safe','0','-i',str(concat),'-i',str(p),'-map','0:v:0','-map','1:a:0','-map_metadata','1','-c','copy']
else:cmd=['ffmpeg','-y','-v','warning','-i',str(p),'-map','0','-c','copy']
subprocess.run(cmd+['-bsf:v','h264_metadata=level=5.1','-video_track_timescale','60000','-t','269.84','-movflags','+faststart',str(output)],check=True)
q=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-of','json',str(output)]));vv=next(s for s in q['streams'] if s['codec_type']=='video');assert int(vv['nb_frames'])==16190,vv;output.replace(p);print('FINAL TAIL AND H264 HEADER VERIFIED',vv['nb_frames'],vv['duration'],vv['level'])
