"""Conform non-overlapping official source excerpts to the locked musical edit."""
import json,subprocess,concurrent.futures
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[1]
# Reviewed, non-overlapping source time ranges. Only the selected excerpts are distributed.
SOURCE='https://videos-rockstargames-com.akamaized.net/v4/rk721912/flv/en-us-1080p.mp4'
PICKS={0:[1119.9],1:[760.0],4:[1134.0],6:[1221.5],8:[1142.1],10:[503.0],11:[510.0],14:[1129.0],19:[1104.0],20:[1062.0],22:[920.2],23:[1233.0],25:[1261.0],27:[519.0,529.0,778.0,984.0],29:[948.0],41:[797.0],42:[768.0],44:[924.0],45:[900.0],47:[1281.0],55:[935.0],59:[773.0],60:[1066.0],62:[938.0],63:[743.0],65:[1137.0],68:[783.0]}
def build():
 plan=json.loads((R/'analysis/timeline.json').read_text());schedule={};jobs=[]
 for s in plan:
  if s['index'] not in PICKS:continue
  dur=s['end']-s['start'];items=[]
  for slot,start in enumerate(PICKS[s['index']]):
   name=f"shot-{s['index']:02d}-{slot}";e=dict(name=name,start=start,end=round(start+dur,4),source=SOURCE,slot=slot,mv_start=s['start'],mv_end=s['end']);items.append(e);jobs.append(e)
  schedule[str(s['index'])]=items
 ordered=sorted(jobs,key=lambda x:x['start'])
 for a,b in zip(ordered,ordered[1:]):
  assert a['end']<=b['start']+.001,(a,b)
 (R/'assets/footage').mkdir(exist_ok=True)
 def job(e):
  path=R/f"assets/footage/{e['name']}.mp4";dur=e['end']-e['start']
  if path.exists() and (R/f"analysis/{e['name']}.npy").exists():return
  if not path.exists():subprocess.run(['ffmpeg','-v','error','-ss',str(e['start']),'-i',str(R/'references/extended-look.mp4'),'-t',str(dur),'-vf','crop=1920:800:0:70,scale=1280:534','-an','-map_metadata','-1','-c:v','libx264','-preset','fast','-crf','15','-threads','1','-pix_fmt','yuv420p','-movflags','+faststart',str(path)],check=True)
  raw=subprocess.check_output(['ffmpeg','-v','error','-i',str(path),'-f','rawvideo','-pix_fmt','rgb24','-threads','1','-']);a=np.frombuffer(raw,dtype='u1').reshape(-1,534,1280,3);np.save(R/f"analysis/{e['name']}.npy",a);print(e['name'],e['start'],len(a),flush=True)
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:list(pool.map(job,jobs))
 (R/'analysis/shot-sources.json').write_text(json.dumps(schedule,indent=2));print('COMPLETE',len(jobs),'unique non-overlapping excerpts',flush=True)
if __name__=='__main__':build()
