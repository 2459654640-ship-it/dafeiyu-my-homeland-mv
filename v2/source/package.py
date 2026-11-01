from pathlib import Path
import zipfile,json,hashlib
ROOT=Path(__file__).resolve().parents[1]
PROJECT=ROOT.parent
OUT=ROOT/'output'
paths=[]
for folder in ['source','assets']:
    paths.extend(p for p in (ROOT/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts)
paths.extend(ROOT/name for name in ['README.md','PRODUCTION.md','VALIDATION.md','requirements.txt'])
paths.append(ROOT/'output/validation-v2.json')
paths.append(PROJECT/'assets/song.mp3')
paths.extend(PROJECT/'analysis'/name for name in ['features.npz','music.json','lyrics.json'])
paths.append(PROJECT/'references/character-NOTICE.txt')
archive=OUT/'Dafeiyu-v2-Editable-Project.zip'
with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=5) as z:
    for p in paths:
        if p.exists():z.write(p,Path('dafeiyu-mv-v2')/p.relative_to(PROJECT))
    z.writestr('dafeiyu-mv-v2/README.md','请先阅读 v2/README.md。\n完整渲染命令：python v2/source/film.py\n')
print('V2_ARCHIVE',archive,archive.stat().st_size)
