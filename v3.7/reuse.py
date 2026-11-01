from pathlib import Path
import subprocess,shutil,zipfile
r=Path('/workspace/ocean-of-worlds/v3.7');repo=r.parent/'github-publish';name='Dafeiyu-My-Homeland-v3.7-1080p60-Master.mp4';out=r/'output'/name
# Reuse the original coded performance for 3.81s; accelerate only the first two history nodes.
# The remaining history, including Harness and latest model, keeps its full duration.
base=r.parent/'v3.6/output/Dafeiyu-My-Homeland-v3.6-1080p60-Master.mp4';code=r.parent/'v3.1/output/code.mp4'
filters="[0:v]trim=start=0:end=110.5,setpts=PTS-STARTPTS[a];[1:v]trim=start=0:end=3.81,setpts=PTS-STARTPTS[b];[0:v]trim=start=110.5:end=118.12,setpts=(PTS-STARTPTS)/2,fps=60[c];[0:v]trim=start=118.12:end=195,setpts=PTS-STARTPTS[d];[a][b][c][d]concat=n=4:v=1:a=0,fps=60[v]"
cmd=['ffmpeg','-y','-v','warning','-filter_complex_threads','1','-threads','1','-i',str(base),'-threads','1','-i',str(code),'-filter_complex',filters,'-map','[v]','-map','0:a','-c:v','libx264','-preset','veryfast','-crf','13','-maxrate','45M','-bufsize','90M','-threads','3','-pix_fmt','yuv420p','-c:a','copy','-t','195','-movflags','+faststart',str(out)]
subprocess.run(cmd,check=True);print('RENDERED',flush=True)
for n in ['validate.py','check-player.cjs']:
 p=r/'source'/n;p.write_text(p.read_text().replace('v3.6-1080','v3.7-1080').replace('validation-v3.6.json','validation-v3.7.json'))
for cmd in [['/workspace/ocean-of-worlds/.venv/bin/python','source/validate.py'],['node','source/check-player.cjs']]:subprocess.run(cmd,cwd=r,check=True)
(repo/'v3.7').mkdir(exist_ok=True);shutil.copy2(__file__,repo/'v3.7/reuse.py');shutil.copy2(out,repo/'masters'/name)
readme='复用 v3.1 代码剪影演奏的前 3.81 秒，放在 110.50–114.31 秒；ChatGPT 与 DeepSeek 早期模型共用接下来 3.81 秒，R1、Harness 与最新模型仍保持原来时长。其余镜头和原音轨保留。原模型信息源及美术署名同 v3.6。\n'
(repo/'v3.7/README.md').write_text(readme)
with zipfile.ZipFile(r.parent/'v3.6/output/Dafeiyu-v3.6-Editable-Project.zip') as z,zipfile.ZipFile(repo/'downloads/Dafeiyu-v3.7-Editable-Project.zip','w',zipfile.ZIP_DEFLATED) as dst:
 for n in z.namelist():dst.writestr(n,z.read(n))
 dst.writestr('v3.7/README.md',readme);dst.write(__file__,'v3.7/reuse.py')
old=(repo/'README.md').read_text();(repo/'README.md').write_text('# 大肥鱼我的家乡 · v3.7\n\n[高清成品](https://github.com/2459654640-ship-it/dafeiyu-my-homeland-mv/raw/refs/heads/main/masters/'+name+')\n\n'+readme+'\n<details><summary>历史版本与素材</summary>\n'+old+'\n</details>')
subprocess.run(['git','add','README.md','v3.7','masters/'+name,'downloads/Dafeiyu-v3.7-Editable-Project.zip'],cwd=repo,check=True);subprocess.run(['git','commit','-m','Reuse short coded guitar performance and condense early history nodes'],cwd=repo,check=True);subprocess.run(['git','push','origin','main'],cwd=repo,check=True)
print('DELIVERED',name,flush=True)
