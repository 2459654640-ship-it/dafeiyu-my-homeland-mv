from pathlib import Path
import hashlib,json,shutil
r=Path(__file__).resolve().parents[1];out=r/'output';out.mkdir(exist_ok=True)
p=out/'Vice_City_My_Home_1080p60_HQ.mp4';parts=sorted((r/'delivery/parts').glob('*.part'));assert len(parts)==23,len(parts)
with p.open('wb') as dest:
 for part in parts:
  with part.open('rb') as source:shutil.copyfileobj(source,dest,1024*1024)
v=json.loads((r/'delivery/validation.json').read_text());assert p.stat().st_size==v['size_bytes'];assert hashlib.file_digest(p.open('rb'),'sha256').hexdigest()==v['sha256']
(r/'frames').mkdir(exist_ok=True);shutil.copy2(r/'delivery/cover.jpg',r/'frames/chinese-6.4.jpg')
print('Verified complete original finished film:',p.stat().st_size,'bytes; SHA256:',v['sha256'])
