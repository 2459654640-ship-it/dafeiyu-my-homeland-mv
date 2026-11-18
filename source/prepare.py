"""Build render caches from the included editable footage; no AI models required."""
import os
os.environ['OPENBLAS_NUM_THREADS']='1'
from pathlib import Path
import concurrent.futures,json,cv2,numpy as np
from media_style import neon_print
R=Path(__file__).resolve().parents[1];cv2.setNumThreads(1)
def build(item):
 name=item['name'];source=R/f'assets/footage/{name}.mp4';c=cv2.VideoCapture(str(source));n=int(c.get(cv2.CAP_PROP_FRAME_COUNT));w=int(c.get(cv2.CAP_PROP_FRAME_WIDTH));h=int(c.get(cv2.CAP_PROP_FRAME_HEIGHT));assert n>0,source
 temp=R/f'analysis/{name}.tmp.npy';a=np.lib.format.open_memmap(temp,mode='w+',dtype='u1',shape=(n,h,w,3));actual=0
 for i in range(n):
  ok,f=c.read()
  if not ok:break
  a[i]=neon_print(cv2.cvtColor(f,cv2.COLOR_BGR2RGB),item['mv_start']>=222.9,i);actual+=1
 assert actual==n,(name,actual,n)
 a.flush();del a;c.release();temp.replace(R/f'analysis/{name}.npy');print('NEON',name,n,flush=True)
def main():
 schedule=json.loads((R/'analysis/shot-sources.json').read_text());jobs=[e for v in schedule.values() for e in v]
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:list(pool.map(build,jobs))
 # Optional legacy scenic clips are retained as source references only.
 (R/'analysis/cache-style.json').write_text(json.dumps(dict(shader='neon_print_v1',frames_stylized=True,clips=len(jobs)),indent=2));print('ALL FOOTAGE STYLIZED',flush=True)
if __name__=='__main__':main()
