from director import FilmV3
from ui import *
from PIL import ImageDraw
class StableGuitar(FilmV3):
 def render(self,t,glow=True):
  im=super().render(t,glow)
  if (31.7<=t<39.34) or (162.42<=t<166.23):
   im=im.convert('RGBA');ImageDraw.Draw(im).rectangle((0,932,W,H),fill=(3,7,18,255))
   en,zh=('COMPILE / PLAY','编译这首歌，让世界开始演奏。') if t<100 else ('CODA / ONE MORE SKY','再演奏一次，再打开一片天空。')
   for value,size,y,kind,c in [(en,30,962,'mono',ICE),(zh,48,1010,'cjk',TEXT)]:text(im,((W-font(size,kind).getlength(value))/2,y),value,size,c,kind)
  return im.convert('RGB')
if __name__=='__main__':
 import render
 render.FilmV3=StableGuitar;render.main()
