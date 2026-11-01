import math,functools
import numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageFilter
from ui import W,H,ROOT,BLUE,ICE,TEXT,BG,font,text,color,clamp,smooth,ease
from fields import raster,rotate,project

@functools.lru_cache(96)
def word_points(word):
    f=font(250,'bold');ww=max(1,int(f.getlength(word))+10)
    im=Image.new('L',(ww,310));d=ImageDraw.Draw(im);d.text((4,-f.getbbox(word)[1]),word,font=f,fill=255)
    im=im.crop(im.getbbox());im.thumbnail((380,130),Image.Resampling.LANCZOS)
    a=np.array(im);yy,xx=np.where(a>80)
    p=np.c_[(xx-im.width/2)/im.width*2.4,(im.height/2-yy)/im.width*2.4,np.zeros(len(xx))]
    rng=np.random.default_rng(sum(map(ord,word)))
    # A thin depth volume makes the lyric a spatial object, not a flat subtitle texture.
    p[:,2]=rng.uniform(-.08,.08,len(p))
    return p.astype('f4'),a[yy,xx]/255.

class LyricSpace:
    def __init__(self,glyph):self.glyph=glyph

    def sculpture(self,im,word,t,rect,mode='wave',progress=1.,gain=1.,alpha=1.,yaw=0.):
        p,b=word_points(word);p=p.copy()
        x=p[:,0].copy();y=p[:,1].copy()
        if mode=='wave':
            p[:,1]+=np.sin(x*4.5-t*2.2)*.08+np.sin(x*10-t*3.)*.025
            p[:,2]+=np.cos(x*3.5-t*1.2)*.13
        elif mode=='orbit':
            a=x*.6+t*.15;p[:,0]=np.sin(a)*1.55;p[:,2]=np.cos(a)*.65-.4
            p[:,1]+=np.sin(x*3+t)*.04
        elif mode=='burst':
            amount=1-progress
            p[:,0]+=np.sign(x)*amount*(.3+abs(x))*1.4
            p[:,1]+=np.sin(x*21+y*30)*amount*.8
            p[:,2]+=np.cos(x*13+y*17)*amount*1.3
        elif mode=='flame':
            p[:,1]+=np.sin(x*11+t*4)*.08
            p[:,2]+=np.cos(y*16-t*2)*.15
        p=rotate(p,yaw=yaw,pitch=math.sin(t*.4)*.035)
        p*=gain
        visible=np.linspace(0,1,len(p))<min(1,progress*1.15)
        picture=raster(p[visible],b[visible],rect,self.glyph,cam=2.7,style='text',phase=int(t*2),alpha=alpha,letter=word)
        im.alpha_composite(picture,(int(rect[0]),int(rect[1])))

    def giant(self,im,word,xy,size=145,ink=ICE,alpha=1.,angle=0,shadow=True):
        f=font(size,'cjk' if any('\u4e00'<=c<='\u9fff' for c in word) else 'bold');w=int(f.getlength(word))+30;h=size+40
        pic=Image.new('RGBA',(w,h));d=ImageDraw.Draw(pic)
        if shadow:d.text((12,8),word,font=f,anchor='lt',fill=(*BG,int(220*alpha)),stroke_width=5,stroke_fill=(*BG,int(220*alpha)))
        d.text((8,4),word,font=f,anchor='lt',fill=(*ink,int(255*alpha)))
        if angle:pic=pic.rotate(angle,Image.Resampling.BICUBIC,expand=True)
        im.alpha_composite(pic,(int(xy[0]),int(xy[1])))

    def glyph_ribbon(self,im,words,t,origin=(960,520),scale=1.,strength=1.):
        d=ImageDraw.Draw(im);cx,cy=origin
        for layer in range(4):
            for i in range(36):
                u=i/36*math.tau+t*(.21+layer*.025)
                dep=1.35+.45*math.sin(u+layer*.9)
                x=cx+math.cos(u)*680*scale/dep
                y=cy+math.sin(u*1.7+layer*.7)*230*scale/dep
                word=words[(i+layer)%len(words)]
                size=int((13+7/dep)*scale)
                text(im,(x,y),word,size,color(ICE if i%5==0 else BLUE,(.3+.55/dep)*strength))

    def phrase(self,im,line,t,xy=(64,946)):
        if line is None:return
        x,y=xy;d=ImageDraw.Draw(im)
        for w in line['words']:
            if w['start']>t:break
            hot=w['start']<=t<=w['end'];age=t-w['start']
            size=25 if hot else 22
            bounce=math.sin(clamp(age/.15)*math.pi)*12 if hot else 0
            text(im,(x,y-bounce),w['word'],size,ICE if hot else color(TEXT,.78),'bold' if hot else 'mono')
            width=font(size,'bold' if hot else 'mono').getlength(w['word'])
            if hot:d.line((x,y+31,x+width,y+31),fill=BLUE,width=2)
            x+=width+15
        text(im,(xy[0],y+49),line['zh'],25,TEXT,'cjk')
