from pathlib import Path
import json,shutil,zipfile,hashlib

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output'
OUT.mkdir(exist_ok=True)
lines=json.loads((ROOT/'analysis/lyrics.json').read_text())
def stamp(t,vtt=False):
    ms=round(t*1000)
    return f'{ms//3600000:02d}:{ms//60000%60:02d}:{ms//1000%60:02d}{"." if vtt else ","}{ms%1000:03d}'
(OUT/'大肥鱼我的家乡_双语字幕.srt').write_text('\n\n'.join(f'{i+1}\n{stamp(x["start"])} --> {stamp(x["end"]+.30)}\n{x["en"]}\n{x["zh"]}' for i,x in enumerate(lines))+'\n')
(OUT/'lyrics.vtt').write_text('WEBVTT\n\n'+'\n\n'.join(f'{stamp(x["start"],True)} --> {stamp(x["end"]+.30,True)}\n{x["en"]}\n{x["zh"]}' for x in lines)+'\n')
cover=ROOT/'render/frame-009.60.jpg'
if cover.exists():shutil.copyfile(cover,OUT/'cover.jpg')
manifest={}
for p in sorted((ROOT/'assets').glob('*')):
    if p.is_file():manifest[str(p.relative_to(ROOT))]=hashlib.sha256(p.read_bytes()).hexdigest()
(ROOT/'assets/SHA256SUMS.json').write_text(json.dumps(manifest,indent=2))
include=[]
for folder in ['source','assets','docs']:
    include.extend(p for p in (ROOT/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts)
include.extend(ROOT/name for name in ['README.md','requirements-render.txt','requirements-analysis.txt','requirements.lock.txt'])
include.extend(ROOT/'analysis'/name for name in ['features.npz','music.json','lyrics.json','storyboard.json'])
include.append(ROOT/'references/character-NOTICE.txt')
include.append(OUT/'review.html')
archive=OUT/'大肥鱼我的家乡_可编辑工程.zip'
with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=5) as z:
    for p in include:
        if p.is_file():z.write(p,Path('ocean-of-worlds')/p.relative_to(ROOT))
print('PACKAGE_COMPLETE',archive,archive.stat().st_size)
