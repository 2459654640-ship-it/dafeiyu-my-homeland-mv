"""Package portable sources and original AI-assisted artwork without render caches."""
from pathlib import Path
import json,zipfile,shutil
R=Path(__file__).resolve().parents[1];OUT=R/'output';OUT.mkdir(exist_ok=True)
def timecode(t):
 ms=round(t*1000);return f'{ms//3600000:02d}:{ms//60000%60:02d}:{ms//1000%60:02d},{ms%1000:03d}'
lyrics=json.loads((R/'analysis/lyrics.json').read_text());sub='\n'.join(f"{i+1}\n{timecode(l['start'])} --> {timecode(min(l['end']+.28,lyrics[i+1]['start']-.01) if i+1<len(lyrics) else l['end']+.28)}\n{l['en']}\n{l['zh']}\n" for i,l in enumerate(lyrics));(OUT/'Vice_City_My_Home_Bilingual.srt').write_text(sub,encoding='utf-8-sig')
cover=R/'frames/chinese-6.4.jpg'
if cover.exists():shutil.copy2(cover,OUT/'Vice_City_My_Home_Cover.jpg')
else:
 from render import Composer
 Composer().frame(6.4).save(OUT/'Vice_City_My_Home_Cover.jpg',quality=95)
files=[R/x for x in ['README.md','SOURCES.md','LICENSE','requirements.txt','requirements-analysis.txt']]+sorted((R/'source').glob('*.py'))
files+=sorted(f for f in (R/'assets').rglob('*') if f.is_file() and not f.name.startswith('official-'))
files += [R/'analysis'/x for x in ['lyrics.json','hits.json','shot-sources.json','timeline.json','cache-style.json']]
with zipfile.ZipFile(OUT/'Vice_City_My_Home_Editable_Project.zip','w') as z:
 for f in files:z.write(f,Path('Vice_City_My_Home')/f.relative_to(R),compress_type=zipfile.ZIP_STORED if f.suffix.lower() in ['.mp4','.mp3','.png'] else zipfile.ZIP_DEFLATED,compresslevel=2)
 z.write(OUT/'Vice_City_My_Home_Bilingual.srt','Vice_City_My_Home/Vice_City_My_Home_Bilingual.srt')
with zipfile.ZipFile(OUT/'Vice_City_My_Home_AI_Assets.zip','w') as z:
 for f in sorted((R/'assets').glob('*.png')):z.write(f,Path('AI_Assets')/f.name,compress_type=zipfile.ZIP_STORED)
 z.write(R/'SOURCES.md','AI_Assets/SOURCES.md',compress_type=zipfile.ZIP_DEFLATED)
for f in OUT.glob('*.zip'):
 with zipfile.ZipFile(f) as z:assert z.testzip() is None
 print(f.name,f.stat().st_size)
