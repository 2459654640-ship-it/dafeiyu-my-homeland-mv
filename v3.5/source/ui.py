from pathlib import Path
import math,functools
import numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageFilter

ROOT=Path(__file__).resolve().parents[1]
W,H=1920,1080
BG=(5,8,16);TEXT=(202,215,235);DIM=(81,99,126);BLUE=(110,143,255);ICE=(180,210,255);BRAND=(77,107,254)
FONT='/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf'
BOLD='/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf'
CJK='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'

def clamp(v):return max(0.,min(1.,float(v)))
def ease(v):v=clamp(v);return 1-(1-v)**3
def smooth(v):v=clamp(v);return v*v*(3-2*v)
def mix(a,b,u):return tuple(int(x+(y-x)*clamp(u)) for x,y in zip(a,b))
def color(c,v=1.):return mix(BG,c,v)

@functools.lru_cache(80)
def font(size=20,kind='mono'):
    return ImageFont.truetype({'mono':FONT,'bold':BOLD,'cjk':CJK}[kind],int(size))

@functools.lru_cache(4000)
def wordsprite(s,size=20,kind='mono',c=TEXT):
    f=font(size,kind);box=f.getbbox(s)
    im=Image.new('RGBA',(max(1,math.ceil(f.getlength(s))+4),size*2))
    ImageDraw.Draw(im).text((0,-box[1]),s,font=f,fill=(*c,255))
    return im

def text(im,xy,s,size=20,c=TEXT,kind='mono',alpha=1.):
    if not s:return
    if kind in ['mono','bold'] and any('\u4e00'<=ch<='\u9fff' for ch in str(s)):kind='cjk'
    sp=wordsprite(str(s),size,kind,tuple(c))
    if alpha<.995:
        sp=sp.copy();sp.putalpha(sp.getchannel('A').point(lambda a:int(a*clamp(alpha))))
    im.alpha_composite(sp,(int(xy[0]),int(xy[1])))

def fittext(im,xy,s,maxw,size=20,c=TEXT,kind='mono'):
    while font(size,kind).getlength(s)>maxw and size>10:size-=1
    text(im,xy,s,size,c,kind)

def wrap(s,width,size=20,kind='cjk'):
    out=[];line=''
    for ch in s:
        if ch=='\n':out.append(line);line='';continue
        if font(size,kind).getlength(line+ch)>width:out.append(line);line=ch
        else:line+=ch
    if line:out.append(line)
    return out

def typed(s,age,rate=24):
    n=max(0,min(len(s),int(age*rate)))
    return s[:n]+('▌' if n<len(s) and int(age*12)%2==0 else '')

def panel(im,box,title='',accent=TEXT,fill=True,level=.55,spinner=None):
    x,y,x2,y2=map(int,box)
    d=ImageDraw.Draw(im)
    if fill:d.rectangle((x,y,x2,y2),fill=(*BG,248))
    d.rectangle((x,y,x2,y2),outline=color(accent,level),width=1)
    for a,b,dx,dy in [(x,y,1,1),(x2,y,-1,1),(x,y2,1,-1),(x2,y2,-1,-1)]:
        d.line((a,b,a+dx*10,b),fill=color(accent,min(1,level+.15)),width=2)
        d.line((a,b,a,b+dy*10),fill=color(accent,min(1,level+.15)),width=2)
    if title:
        tw=font(16).getlength(title)+25
        d.rectangle((x+13,y-10,min(x2-10,x+tw),y+9),fill=BG)
        text(im,(x+21,y-7),title,16,color(accent,min(1,level+.15)))
    if spinner is not None:
        text(im,(x2-36,y-7),'|/-\\'[int(spinner*7)%4],16,color(accent,.75))

def chip(im,xy,s,hot=False,c=BLUE,size=17):
    x,y=map(int,xy);tw=math.ceil(font(size).getlength(s))+18
    d=ImageDraw.Draw(im)
    d.rectangle((x,y,x+tw,y+size+13),fill=c if hot else color(c,.06),outline=color(c,.85 if hot else .35))
    text(im,(x+9,y+5),s,size,BG if hot else color(c,.8),'bold' if hot else 'mono')
    return tw

def cursor(im,xy,t,click=0.,label=None):
    x,y=xy;d=ImageDraw.Draw(im)
    if click>0:
        r=9+(1-click)*32;d.ellipse((x-r,y-r,x+r,y+r),outline=color(ICE,click*.65),width=2)
    d.polygon([(x,y),(x+1,y+24),(x+7,y+17),(x+13,y+29),(x+18,y+26),(x+12,y+15),(x+22,y+14)],fill=TEXT,outline=BG,width=2)
    if label:text(im,(x+27,y+12),label,13,color(TEXT,.65))

class Glyphs:
    def __init__(self,cw=9,ch=15):
        self.cw,self.ch=cw,ch
        self.symbols=' .:;=+*x%#@01<>/[]{}~^|ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        self.ramp=np.array([0,1,2,3,4,5,6,7,8,9,10])
        colors=np.array([BG,(19,30,62),(30,46,89),(45,66,122),(62,87,168),(83,112,210),(109,140,236),(143,171,246),(181,204,251),(219,232,254)])
        self.palette=colors.astype(np.uint8)
        atlas=np.zeros((len(colors),len(self.symbols),ch,cw,4),dtype=np.uint8)
        for level,c in enumerate(colors):
            for j,s in enumerate(self.symbols):
                im=Image.new('RGBA',(cw,ch));d=ImageDraw.Draw(im)
                d.text((0,-1),s,font=font(ch-1),fill=(*map(int,c),255 if level and j else 0))
                atlas[level,j]=np.array(im)
        self.atlas=atlas

    def field(self,values,style='solid',phase=0,alpha=1.,letter=''):
        v=np.clip(values,0,1)
        lev=np.minimum(9,np.ceil(v*9).astype(np.int32))
        if style=='digits':
            yy,xx=np.indices(v.shape);glyph=11+(xx+yy+phase)%2
        elif style=='text':
            yy,xx=np.indices(v.shape);s=letter or 'OCEAN';ids=np.array([self.symbols.index(c) if c in self.symbols else 10 for c in s]);glyph=ids[(xx+yy+phase)%len(ids)]
        elif style=='code':
            yy,xx=np.indices(v.shape);glyph=11+(xx*7+yy*3+phase)%len(self.symbols[11:])
        else:glyph=self.ramp[np.minimum(10,(v*10).astype(int))]
        glyph=np.where(v>.03,glyph,0)
        cells=self.atlas[lev,glyph]
        pixels=cells.transpose(0,2,1,3,4).reshape(v.shape[0]*self.ch,v.shape[1]*self.cw,4).copy()
        if alpha<.995:pixels[:,:,3]=(pixels[:,:,3]*clamp(alpha)).astype('u1')
        return Image.fromarray(pixels)

    def banner(self,s,width=1000,rows=20,style='text',phase=0):
        cols=max(8,int(width/self.cw));f=font(220,'bold')
        im=Image.new('L',(max(1,int(f.getlength(s))+4),280));ImageDraw.Draw(im).text((0,-f.getbbox(s)[1]),s,font=f,fill=255)
        bb=im.getbbox();im=im.crop(bb)
        aspect=im.width/im.height*self.ch/self.cw
        rows=max(3,min(rows,int(cols/aspect)))
        cols=min(cols,max(8,int(rows*aspect)))
        a=np.array(im.resize((cols,rows),Image.Resampling.LANCZOS))/255.
        return self.field(a,style,phase,letter=s)

class Assets:
    def __init__(self):
        self.original={n:Image.open(ROOT/f'assets/char-{n}.png').convert('RGBA') for n in ['greet','blink','point','open']}
        self.cache={}
        self.palette=np.array([(7,12,30),(16,25,64),(30,46,108),(53,72,160),(81,111,204),(124,155,231),(182,204,247),(235,242,254)],dtype=np.uint8)

    def portrait(self,pose,t,width=432,height=320,colorful=False):
        if pose=='greet' and ((t*1.07)%4.8>.0 and (t*1.07)%4.8<.15):pose='blink'
        key=(pose,width,height,colorful)
        if key not in self.cache:
            src=self.original[pose].copy()
            # Retain the entire cell as the animation register; do not recrop each expression differently.
            src.thumbnail((width,height),Image.Resampling.LANCZOS)
            small=src.resize((max(1,src.width//3),max(1,src.height//3)),Image.Resampling.LANCZOS)
            a=np.array(small)
            if not colorful:
                lum=(a[:,:,0]*.24+a[:,:,1]*.56+a[:,:,2]*.20)/255
                levels=np.clip(np.floor(np.sqrt(lum)*7),0,7).astype(int)
                a[:,:,:3]=self.palette[levels]
            a[:,:,3]=np.where(a[:,:,3]>130,255,0)
            self.cache[key]=a
        a=self.cache[key];rows,cols=a.shape[:2]
        yy,xx=np.indices((rows,cols))
        edge=np.clip(np.abs(xx-cols*.50)/(cols*.45),0,1)**2
        lower=np.clip((yy/rows-.20)*1.5,0,1)
        shift=np.sin(t*1.6+yy*.10)*edge*lower*1.8
        dx=shift.copy();dy=np.zeros_like(dx)
        if pose in ['open','point']:
            # Two local arm controls rotate around the shoulders. The face and clasped opening pose stay registered.
            for side in [-1,1]:
                px=cols*(.5+side*.18);py=rows*.51
                weight=np.exp(-((xx/cols-(.5+side*.29))/.20)**2-((yy/rows-.62)/.24)**2)
                angle=math.sin(t*2.45+side*.7)*.12*side
                dx+=-(yy-py)*angle*weight
                dy+=(xx-px)*angle*weight
        idx=np.clip(np.rint(xx-dx).astype(int),0,cols-1)
        idy=np.clip(np.rint(yy-dy).astype(int),0,rows-1)
        warped=a[idy,idx].copy()
        # Pixel seams are part of the display's half-block texture, not a full-screen noise filter.
        im=Image.fromarray(warped).resize((cols*3,rows*3),Image.Resampling.NEAREST)
        return im

    def object(self,name,t,width,height):
        key=('object',name,width,height)
        if key not in self.cache:
            src=Image.open(ROOT/f'assets/{name}.png').convert('RGBA')
            src.thumbnail((max(1,width//2),max(1,height//2)),Image.Resampling.LANCZOS)
            a=np.array(src);lum=(a[:,:,0]*.22+a[:,:,1]*.58+a[:,:,2]*.20)/255.
            levels=np.clip((np.sqrt(lum)*7).astype(int),0,7)
            a[:,:,:3]=self.palette[levels];a[:,:,3]=np.where(a[:,:,3]>150,255,0)
            self.cache[key]=a
        a=self.cache[key];rows,cols=a.shape[:2];yy,xx=np.indices((rows,cols))
        dx=np.zeros((rows,cols));dy=np.zeros((rows,cols))
        if name=='whale':
            tail=np.clip((.50-xx/cols)*2,0,1)
            dy+=np.sin(t*2.1+xx/cols*3.)*tail*rows*.09
            dx+=np.cos(t*2.1+xx/cols*3.)*tail*cols*.018
        else:
            angle=math.sin(t*.65)*.055
            dx+=-(yy-rows/2)*angle;dy+=(xx-cols/2)*angle
        ix=np.rint(xx-dx).astype(int);iy=np.rint(yy-dy).astype(int)
        valid=(ix>=0)&(ix<cols)&(iy>=0)&(iy<rows)
        out=a[np.clip(iy,0,rows-1),np.clip(ix,0,cols-1)].copy();out[~valid,3]=0
        return Image.fromarray(out).resize((cols*2,rows*2),Image.Resampling.NEAREST)

def post(im,t,glow=True):
    rgb=im.convert('RGB')
    if glow:
        sm=rgb.resize((W//4,H//4),Image.Resampling.BILINEAR)
        sm=sm.filter(ImageFilter.GaussianBlur(1.5)).resize((W,H),Image.Resampling.BILINEAR)
        # Screen blend at low gain preserves sharp native terminal text.
        a=np.asarray(rgb,dtype=np.uint16);b=np.asarray(sm,dtype=np.uint16)
        rgb=Image.fromarray(np.minimum(255,a+b//5).astype('u1'))
    return rgb
