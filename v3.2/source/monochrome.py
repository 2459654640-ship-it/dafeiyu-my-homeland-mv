"""Original negative-space performance: guitar -> whale -> word -> performer."""
import math
import numpy as np
from PIL import Image,ImageDraw,ImageOps
from ui import W,H,BLUE,ICE,TEXT,font,text,clamp,ease,smooth,Glyphs,BG


class Monochrome:
    def __init__(self,performer,rhythm):self.performer=performer;self.rhythm=rhythm;self.glyph=Glyphs(cw=8,ch=12)

    def label(self,im,word,x,y,size,stroke=0,tilt=0):
        f=font(size,'bold');ww=int(f.getlength(word))+30
        a=Image.new('RGBA',(ww,size+30));d=ImageDraw.Draw(a)
        d.text((8,-f.getbbox(word)[1]+5),word,font=f,fill=(244,247,251,255) if not stroke else (0,0,0,0),
               stroke_width=stroke,stroke_fill=(244,247,251,255))
        if tilt:a=a.rotate(tilt,Image.Resampling.BICUBIC,expand=True)
        im.alpha_composite(a,(int(x),int(y)))

    def draw(self,t,hit,seeds):
        im=Image.new('RGBA',(W,H),(7,9,15,255));d=ImageDraw.Draw(im)
        e=t-110.50;phase=self.rhythm.phase('guitar',t)*.5
        cx=1180+math.sin(t*.57)*65;cy=525;ww,hh=860,985;transition=None
        if 3.81<=e<7.62:
            # A full-frame instrument close-up is a different composition, not another bordered scene.
            q=ease((e-3.81)/.25);ww=int(860+q*750);hh=int(985+q*860);cx=1350;cy=730
        elif 7.62<=e<8.70:transition=('guitar','whale',(e-7.62)/1.08)
        elif 8.70<=e<11.24:transition=('whale','whale',1);ww=1350;hh=1460;cx=1060+math.sin((e-8.70)*1.2)*280;cy=540
        elif 11.24<=e<12.15:transition=('whale','FREE',(e-11.24)/.91);ww=1330;hh=1450;cx=1050;cy=535
        elif 12.15<=e<13.05:transition=('FREE','FREE',1);ww=1440;hh=1530;cx=1060;cy=540
        elif 13.05<=e<14.15:transition=('FREE','guitar',(e-13.05)/1.10)
        hero=self.performer.guitar(phase,t,ww,hh,transition is not None,(244,247,251),hit['guitar'],transition)
        tilt=math.sin(t*.75)*2+hit['snare']*1.6
        hero=hero.rotate(tilt,Image.Resampling.BICUBIC,expand=True)
        ox=int(cx-hero.width/2);oy=int(cy-hero.height/2-hit['kick']*17)
        # The typographic score changes with the composition and gives the silhouette foreground occlusions.
        if e<3.81:
            self.label(im,'OCEAN',-40+math.sin(t*.9)*27,150,285,stroke=2)
            self.label(im,'PLAY',55,610,230,tilt=-3)
        elif e<7.62:
            self.label(im,'SET',-10,112,255,stroke=2,tilt=8)
            self.label(im,'FREE',-20,630,242,tilt=-7)
        elif e<11.24:
            self.label(im,'NO',45,110,170,stroke=2)
            self.label(im,'FINAL',40,315,165,stroke=2)
            self.label(im,'EDGE',45,655,160,tilt=-2)
        else:
            self.label(im,'WE',5,100,275,stroke=2)
            self.label(im,'CREATE',-5,745,190,stroke=2)
        im.alpha_composite(hero,(ox,oy));d=ImageDraw.Draw(im)
        # Fretted strings leave the instrument, turn into long wave contours and carry earlier lyric tokens.
        for k in range(6):
            p=[]
            for i in range(100):
                u=i/99;x=-80+u*2130
                amplitude=(16+90*hit['guitar'])*(1-u*.6)
                y=590+k*12+math.sin(u*12-t*5+k*.35)*amplitude
                if e>7.62:y+=math.sin(u*6-t)*70
                p.append((x,y))
            # Only two contour strings cross the silhouette; the rest pass behind it through clipping.
            if k in [0,5]:d.line(p,fill=(244,247,251,255),width=2)
            for j in range(5):
                u=(t*.16+j*.2+k*.025)%1;i=int(u*99);x,y=p[i]
                if not(ox<x<ox+hero.width and oy<y<oy+hero.height):
                    text(im,(x,y-22),['OUR','SONGS','DREAMS','WORLD','FREE'][j],19,(244,247,251),'bold')
        if e>14.35:
            q=smooth((e-14.35)/.89);ld=ImageDraw.Draw(im)
            for i,r in enumerate(seeds[:450]):
                x=ox+r[0]*hero.width+(r[2]-.5)*q*1250;y=oy+r[1]*hero.height-(r[3]-.5)*q*830
                ld.rectangle((x,y,x+4+8*q,y+4+8*q),fill=(*BLUE,int(250*q)))
        ink=(180,210,255)
        text(im,(54,37),'WORLD.EXPRESSION / guitar → whale → word → world',17,ink)
        text(im,(55,1026),'CODE SILHOUETTE / ocean.runtime',15,ink)
        # Keep the silhouette, motion and detailed guitar, in the same blue terminal material as the rest.
        small=im.convert('RGB').resize((240,90),Image.Resampling.LANCZOS)
        a=np.asarray(small,dtype='f4');v=np.clip((a[:,:,0]*.22+a[:,:,1]*.58+a[:,:,2]*.2-10)/230,0,1)
        chars=self.glyph.field(np.sqrt(v)*.92,style='code',phase=int(t*4))
        background=Image.new('RGBA',(W,H),(*BG,255));background.alpha_composite(chars)
        return background
