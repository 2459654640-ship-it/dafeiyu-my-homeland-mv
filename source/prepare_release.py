"""Prepare integrity-checked transport parts for the authorized GitHub release job."""
from pathlib import Path
import json,shutil,math
from visuals import R
v=json.loads((R/'output/validation.json').read_text());q=json.loads((R/'output/revision-validation.json').read_text());assert v['full_decode_passed'] and q['new_mask_types']==10 and q['master_sha256']==v['sha256']
p=R/'output/Vice_City_My_Home_1080p60_HQ.mp4';assert p.stat().st_size==v['size_bytes'];dest=R/'delivery/parts';dest.mkdir(exist_ok=True);i=0
with p.open('rb') as f:
 while True:
  b=f.read(64*1024*1024)
  if not b:break
  (dest/f'{i:03d}.part').write_bytes(b);i+=1
for part in dest.glob('*.part'):
 if part.name not in {f'{j:03d}.part' for j in range(i)}:part.unlink()
assert sum(x.stat().st_size for x in dest.glob('*.part'))==v['size_bytes']
(R/'delivery/transport.json').write_text(json.dumps(dict(tag='vice-city-v1.1.0',parts=i,filename=p.name,size_bytes=v['size_bytes'],sha256=v['sha256']),indent=2))
for a,b in [('output/validation.json','delivery/validation.json'),('output/revision-validation.json','delivery/revision-validation.json'),('output/Vice_City_My_Home_Cover.jpg','delivery/cover.jpg')]:shutil.copy2(R/a,R/b)
print('PUBLICATION TRANSPORT READY',i,'parts',v['size_bytes'],'bytes')
