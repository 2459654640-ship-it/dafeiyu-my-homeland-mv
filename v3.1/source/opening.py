import math
import numpy as np
from PIL import Image,ImageDraw,ImageFilter,ImageFont
from ui import W,H,BG,TEXT,BLUE,ICE,font,text,color,smooth,ease,clamp

class Opening:
    def __init__(self,performer):
        self.performer=performer;self.title_cache={}
        self.r=np.random.default_rng(1986).random((420,5))

    def glyph(self,ch,size=152,ink=ICE):
        key=(ch,size,ink)
        if key not in self.title_cache:
            im=Image.new('RGBA',(size+42,size+55));d=ImageDraw.Draw(im)
            d.text((18,8),ch,font=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc',size),anchor='lt',fill=(*ink,255))
            self.title_cache[key]=im
        return self.title_cache[key]

    def title(self,im,t,base_y=826,size=140):
        phrase='大东北我的家乡';final='大肥鱼我的家乡';spacing=size+18;x0=(W-7*spacing)/2
        age=t-6.1939;progress=smooth(age/1.788);d=ImageDraw.Draw(im)
        for i,ch in enumerate(phrase):
            x=x0+i*spacing;y=base_y
            enter=clamp((t-1.0739-i*.07)/.42)
            if enter<=0:continue
            spring=math.exp(-enter*5)*math.sin(enter*13)*15
            if i not in [1,2] or age<0:
                sp=self.glyph(ch,size)
                if enter<1:
                    sp=sp.copy();sp.putalpha(sp.getchannel('A').point(lambda a:int(a*enter)))
                im.alpha_composite(sp,(int(x),int(y+(1-enter)*130+spring)));continue
            old=self.glyph(ch,size);new=self.glyph(final[i],size)
            if progress<1:
                for k in range(7):
                    y0=int(k*old.height/7);y1=int((k+1)*old.height/7)
                    slat=old.crop((0,y0,old.width,y1));q=ease(clamp((progress-k*.025)/.8))
                    dx=(-1 if i==1 else 1)*q*(65+k*22);dy=math.sin(k*.7+i)*q*100
                    slat=slat.rotate((k-3)*q*7,Image.Resampling.BICUBIC,expand=True)
                    slat.putalpha(slat.getchannel('A').point(lambda a:int(a*(1-progress))))
                    im.alpha_composite(slat,(int(x+dx),int(y+y0+dy)))
            if progress>.12:
                sp=new.copy();a=np.array(sp.getchannel('A'));yy,xx=np.indices(a.shape)
                cells=((xx//11)*7+(yy//13)*13)%43/43.
                a[cells>clamp((progress-.12)/.75)]=0;sp.putalpha(Image.fromarray(a))
                im.alpha_composite(sp,(int(x),int(y+(1-progress)*40)))
            if .1<progress<.9:d.line((x+18,y+size*progress,x+size+20,y+size*progress),fill=(*ICE,225),width=3)
        if 5.6<t<8.5:text(im,(x0+spacing+15,base_y-44),'- 东北   + 肥鱼',22,color(ICE,.8),'cjk')

    def draw(self,t,pulse):
        im=Image.new('RGBA',(W,H),(*BG,255));d=ImageDraw.Draw(im)
        s=max(0,t/.56);scale=max(.02,min(1.15,1-math.exp(-s*6)*math.cos(s*9))) if t<.8 else 1.
        for i,r in enumerate(self.r):
            angle=r[0]*math.tau+t*.05;radius=(r[1]*900+t*80)%980
            x=960+math.cos(angle)*radius;y=490+math.sin(angle)*radius*.57
            c=color(ICE if i%9==0 else BLUE,.2+r[2]*.4)
            if i%15==0:text(im,(x,y),'01'[i%2],14,c)
            else:d.line((x,y,x+3+r[3]*6,y),fill=(*c,210),width=1)
        for k in range(3):
            rad=230+k*180+pulse*38
            d.ellipse((960-rad,475-rad*.62,960+rad,475+rad*.62),outline=color(BLUE,.2+.08*k),width=1)
        hero=self.performer.greeting(t,1000)
        if scale!=1:hero=hero.resize((max(2,int(hero.width*scale)),max(2,int(hero.height*scale))),Image.Resampling.LANCZOS)
        x=int(960-hero.width/2);y=int(490-hero.height/2+(1-clamp(t/.5))*450)
        if t<.65:
            for n in [3,2,1]:
                ghost=hero.copy();ghost.putalpha(ghost.getchannel('A').point(lambda a:int(a*.09)))
                im.alpha_composite(ghost,(x+n*9,y+n*25))
        im.alpha_composite(hero,(x,y))
        text(im,(61,39),'DEEPSEEK / OCEAN.HOME',18,color(ICE,.75))
        text(im,(1520,42),'original / new world',14,color(TEXT,.5))
        shade=Image.new('RGBA',(W,H));sd=ImageDraw.Draw(shade)
        for yy in range(748,H):
            sd.line((0,yy,W,yy),fill=(3,6,16,int(185*smooth((yy-748)/260))))
        im.alpha_composite(shade)
        self.title(im,t)
        return im

    def collapse(self,scene,t,dock):
        u=smooth((t-9.526)/1.074)
        if u<=0:return scene
        if u>=1:return dock
        w=int(W*(1-u)+515*u);h=int(H*(1-u)+420*u);x=int(u*38);y=int(u*125)
        card=scene.resize((max(2,w),max(2,h)),Image.Resampling.LANCZOS)
        base=dock.copy();card.putalpha(card.getchannel('A').point(lambda v:int(v*(1-u*.15))))
        base.alpha_composite(card,(x,y))
        ImageDraw.Draw(base).rectangle((x,y,x+w,y+h),outline=(*ICE,220),width=2)
        return base
