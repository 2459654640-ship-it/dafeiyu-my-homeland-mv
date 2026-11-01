from pathlib import Path
import zipfile,json

ROOT=Path(__file__).resolve().parents[1];PROJECT=ROOT.parent;OUT=ROOT/'output'
paths=[]
for folder in ['source','assets']:
    paths.extend(p for p in (ROOT/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts)
paths.extend(ROOT/name for name in ['README.md','PRODUCTION.md','HISTORY-SOURCES.md','CUES.md','VALIDATION.md','requirements.txt'])
paths.extend(ROOT/'analysis'/name for name in ['percussion.npz','hits.json','shot-plan.json','cues.json','source-sha256.json'])
paths.extend(ROOT/'output'/name for name in ['validation-v3.json','browser-validation.json'])
paths.append(PROJECT/'assets/song.mp3')
paths.extend(PROJECT/'analysis'/name for name in ['features.npz','music.json','lyrics.json'])
paths.append(PROJECT/'references/character-NOTICE.txt')
archive=OUT/'Dafeiyu-v3-Editable-Project.zip'
with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=5) as z:
    for p in paths:
        if p.exists():z.write(p,Path('dafeiyu-mv-v3')/p.relative_to(PROJECT))
    z.writestr('dafeiyu-mv-v3/README.md','请先阅读 v3/README.md。\n完整渲染命令：python v3/source/render.py --parallel-master\n')
print('V3_ARCHIVE',archive,archive.stat().st_size)
