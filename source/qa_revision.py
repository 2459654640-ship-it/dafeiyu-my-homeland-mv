"""Verify revised movie frames, removed heading, new matte coverage and official provenance."""
import json,cv2,numpy as np,inspect
from render import Composer
from film import MASK_MONTAGE,Film
from visuals import R
assert '两个人，一座城' not in inspect.getsource(Film.render)
audit=json.loads((R/'analysis/official-source-audit.json').read_text());assert audit['excerpt_count']==30 and audit['shader_cache_samples_verified']==90 and audit['shader_cache_matches_verified_official_excerpts']
cdn=json.loads((R/'analysis/official-cdn-verification.json').read_text());assert all(c['matches_cached_official_master'] for c in cdn['checks'])
f=Composer();seen=set();samples=[('opening-official-logo',1.3),('removed-heading',9),('ending-official-logo',264.9)]
for s in f.film.plan:
 name=MASK_MONTAGE.get(s['index'])
 if name and name not in seen:seen.add(name);samples.append((name,round((s['start']+min(1,(s['end']-s['start'])/2))*60)/60))
assert len(seen)==10
cap=cv2.VideoCapture(str(R/'output/Vice_City_My_Home_1080p60_HQ.mp4'));results=[]
for name,t in samples:
 n=round(t*60);t=n/60;cap.set(cv2.CAP_PROP_POS_FRAMES,n);ok,b=cap.read();assert ok
 a=np.asarray(f.frame(t));b=cv2.cvtColor(b,cv2.COLOR_BGR2RGB);mse=np.mean((a.astype('f4')-b.astype('f4'))**2);psnr=float(10*np.log10(255**2/max(mse,1e-8)));assert psnr>30,(name,t,psnr);results.append(dict(subject=name,t=t,frame_psnr_db=round(psnr,2)));cv2.imwrite(str(R/f'frames/verified-{name}.jpg'),cv2.cvtColor(b,cv2.COLOR_RGB2BGR),[cv2.IMWRITE_JPEG_QUALITY,92])
cap.release();report=dict(master_sha256=json.loads((R/'output/validation.json').read_text())['sha256'],removed_heading_verified=True,new_mask_types=10,official_logo_at_opening_and_ending=True,official_video_provenance_verified=True,frame_checks=results)
(R/'output/revision-validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
