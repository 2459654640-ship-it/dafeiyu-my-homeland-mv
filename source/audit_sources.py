"""Verify official publisher metadata and match each used excerpt to the official master."""
from pathlib import Path
import json,cv2,numpy as np,hashlib
R=Path(__file__).resolve().parents[1];cv2.setNumThreads(1)
v=json.loads((R/'references/extended-verified.json').read_text())['data']['video'];html=(R/'references/rockstar-verified.html').read_text();assert v['id']=='rk721912' and v['game']['title']=='Grand Theft Auto VI' and 'rk721912' in html
source=R/'references/extended-look.mp4';c=cv2.VideoCapture(str(source));fps=c.get(cv2.CAP_PROP_FPS);schedule=json.loads((R/'analysis/shot-sources.json').read_text());checks=[]
for entries in schedule.values():
 for e in entries:
  clip=cv2.VideoCapture(str(R/f"assets/footage/{e['name']}.mp4"));count=int(clip.get(cv2.CAP_PROP_FRAME_COUNT));scores=[]
  for index in [0,count//2,max(0,count-2)]:
   clip.set(cv2.CAP_PROP_POS_FRAMES,index);ok,b=clip.read();assert ok
   tm=e['start']+index/30;best=0
   for delta in [-1,0,1]:
    c.set(cv2.CAP_PROP_POS_FRAMES,max(0,round(tm*fps)+delta));ok,a=c.read();assert ok;a=cv2.resize(a[70:870,:],(1280,534));err=np.mean((a.astype('f4')-b.astype('f4'))**2);best=max(best,10*np.log10(255**2/max(err,1e-6)))
   scores.append(round(float(best),2))
  clip.release();assert min(scores)>24,(e['name'],scores);checks.append(dict(name=e['name'],source_start=e['start'],source_end=e['end'],sample_psnr_db=scores));print(e['name'],scores,flush=True)
c.release()
report=dict(publisher='Rockstar Games',official_page='https://www.rockstargames.com/VI',official_metadata='https://videos.rockstargames.com/v4/rk721912/data/en_us-context-embed.json',title=v['title'],game=v['game']['title'],video_id=v['id'],official_video_linked_from_official_site=True,source_sha256=hashlib.file_digest(source.open('rb'),'sha256').hexdigest(),excerpt_count=len(checks),checks=checks)
(R/'analysis/official-source-audit.json').write_text(json.dumps(report,indent=2));print('OFFICIAL SOURCE AND ALL EXCERPTS VERIFIED',flush=True)
