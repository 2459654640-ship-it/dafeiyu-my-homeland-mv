from pathlib import Path
import math,json,functools
import numpy as np
from PIL import Image,ImageDraw,ImageFilter,ImageFont
from film import Film
from ui import *
from fields import field,raster,project,rotate
from rhythm import Rhythm,LyricClock
from performer import Performer
from opening import Opening
from lyric_space import LyricSpace
from history import History,MILESTONES
from spectacle import Spectacle
from monochrome import Monochrome

WIDE=(0,52,1920,1000)
PLAN=[
(0.,'opening','OPEN / 大东北 → 大肥鱼'),(10.60,'boot','BOOT / ocean.home'),
(15.96,'dock','A BRAND-NEW NAME'),(19.26,'sky','SKY / draw a horizon'),
(22.64,'dock','WHISPER → FLAME'),(26.48,'lights','YOUR LIGHT / MY LIGHT'),
(31.70,'perform','GUITAR / worlds begin moving'),(39.34,'dive','OCEAN / no final edge'),
(46.18,'glass','BEYOND THE GLASS'),(49.72,'galaxy','A UNIVERSE OUT OF A DREAM'),
(53.52,'city','SONGS BECOME WORLDS'),(56.88,'ribbon','A SHINING STREAM'),
(63.70,'ocean','I AM THE OCEAN'),(66.90,'louder','LOUDER THAN THE SEA'),
(70.94,'satellite','DREAM → SATELLITE'),(74.50,'alight','TOGETHER / STARS ALIGHT'),
(80.02,'history_signal','HISTORY / ideas learn to connect'),
(87.64,'history_search','HISTORY / errors and search'),
(95.26,'history_vision','HISTORY / learning to see and act'),
(102.88,'history_attention','HISTORY / words see one another'),
(110.50,'silhouette','PERFORM / black and white'),
(125.74,'history_open','HISTORY / open branches'),
(129.55,'coauthor','HUMAN / your turn'),(133.36,'portals','LAUNCH / no closed window'),
(139.78,'ocean','THE OCEAN IS OURS'),(143.08,'hands','YOUR HANDS / DRAW THE WORLD'),
(146.94,'voices','EVERY VOICE / SKY ALIGHT'),(150.74,'ignite','A THOUSAND NEW WORLDS IGNITE'),
(154.80,'fugue','WORLDS / across the frame'),(158.61,'jellyfish','CURRENT / living networks'),
(162.42,'perform','CODA / one more sky'),(166.23,'home','HOME / a shared world'),
(172.01,'return','RETURN / welcome home'),(179.04,'archive','ARCHIVE / keep worlds open'),
(187.42,'end','大肥鱼我的家乡')]

class FilmV3(Film):
    def __init__(self):
        super().__init__()
        self.rhythm=Rhythm();self.clock=LyricClock(self.lyrics);self.performer=Performer()
        self.opener=Opening(self.performer);self.type3d=LyricSpace(self.glyph);self.history=History()
        self.plan=[dict(start=x[0],end=PLAN[i+1][0] if i+1<len(PLAN) else 195.,mode=x[1],label=x[2],index=i) for i,x in enumerate(PLAN)]
        self.seeds=np.random.default_rng(250120).random((560,7));self.ui_cache={};self.shard_cache={}
        self.props=['island','station','planet','citadel','moebius','jellyfish','orrery','origami','portal','relay','loom','seed']
        self.spectacle=Spectacle();self.monochrome=Monochrome(self.performer,self.rhythm)

    def params(self,t):
        e,b,a,p,i=super().params(t)
        if hasattr(self,'rhythm'):
            self.hit=self.rhythm.state(t);p=max(self.hit['kick'],self.hit['snare']*.75)
        return e,b,a,p,i

    def context(self,t):
        self.t=t;self.energy,self.bass,self.air,self.pulse,self.beat_index=self.params(t)
        self.world_count=min(1024,max(1,int(1024*smooth((t-49.72)/105.))))

    def stars(self,im,t,drive=.6):
        d=ImageDraw.Draw(im)
        for i,r in enumerate(self.seeds[:int(190+230*drive)]):
            depth=.5+r[2]*1.7;speed=34+drive*90
            x=(r[0]*2200+t*speed/depth)%2240-160
            y=r[1]*1080+math.sin(t*.3+r[3]*6)*12
            length=(2+r[4]*9)*drive/depth
            c=color(ICE if i%13==0 else BLUE,(.2+r[5]*.55)*drive)
            d.line((x,y,x-length,y),fill=(*c,185),width=1)
            if i%35==0:text(im,(x+3,y-6),f'{i:03X}',11,c)

    def free_footer(self,im,t):
        line=self.clock.active(t)
        if line:
            d=ImageDraw.Draw(im)
            # A stable, unobtrusive reading layer remains available while the lyric itself participates in space.
            for y in range(928,H):
                a=int(190*clamp((y-928)/80));d.line((0,y,W,y),fill=(2,5,12,a))
            self.type3d.phrase(im,line,t,(65,949))

    def chrome(self,im,s):
        text(im,(48,24),'ocean.home / '+s['mode'],16,color(ICE,.65))
        text(im,(1580,27),f'{int(self.t)//60:02d}:{self.t%60:05.2f} / 03:15',15,color(TEXT,.55))
        if not s['mode'].startswith('history'):
            text(im,(49,1045),'大肥鱼我的家乡  /  shared worlds',14,color(TEXT,.4),'cjk')

    def dock(self,t,boot_age=None):
        self.context(t)
        s=next((s for s in self.speclist if s['start']<=t<s['end']),self.speclist[-1])
        im=Image.new('RGBA',(W,H),(*BG,255));self.shell(im,s)
        if boot_age is None:self.stage(im,s,t-s['start'])
        else:self.boot(im,s,max(0,boot_age))
        self.chat(im,s);self.footer(im)
        return self.fx.apply(im,t,s,t-s['start'],self.energy,self.bass,self.air,self.pulse,self.beat_index,None)

    def actor(self,im,name,t,cx=1450,cy=530,width=730,height=900,alpha=1.):
        a=self.performer.actor(name,t,width,height)
        if alpha<.995:a=a.copy();a.putalpha(a.getchannel('A').point(lambda x:int(x*alpha)))
        im.alpha_composite(a,(int(cx-a.width/2),int(cy-a.height/2+math.sin(t*1.7)*8)))

    def card(self,name,t,width=270,height=205,label='world',active=False):
        # Asset raster size is quantized to avoid building thousands of nearly-identical cache entries.
        width=max(96,int(width/16)*16);height=max(80,int(height/16)*16)
        pic=Image.new('RGBA',(width,height),(4,8,18,235));d=ImageDraw.Draw(pic)
        d.rectangle((0,0,width-1,height-1),outline=color(ICE if active else BLUE,.85 if active else .5),width=2 if active else 1)
        text(pic,(10,8),label,12,ICE)
        d.line((0,29,width,29),fill=color(BLUE,.25))
        a=self.assets.object(name,t,width-28,height-54)
        pic.alpha_composite(a,((width-a.width)//2,32+(height-54-a.height)//2))
        text(pic,(11,height-18),'scope: shared / ready',10,color(TEXT,.42))
        return pic

    def plane(self,im,pic,corners):
        q=np.asarray(corners,float)
        left=max(-300,int(np.floor(q[:,0].min())));top=max(-300,int(np.floor(q[:,1].min())))
        right=min(W+300,int(np.ceil(q[:,0].max())));bot=min(H+300,int(np.ceil(q[:,1].max())))
        if right<=0 or bot<=0 or left>=W or top>=H or right-left<2 or bot-top<2:return
        if right-left>2600 or bot-top>1800:return
        dst=q-[left,top];src=np.array([[0,0],[pic.width,0],[pic.width,pic.height],[0,pic.height]],float)
        A=[];b=[]
        for (x,y),(u,v) in zip(dst,src):
            A.extend([[x,y,1,0,0,0,-u*x,-u*y],[0,0,0,x,y,1,-v*x,-v*y]]);b.extend([u,v])
        try:co=np.linalg.solve(A,b)
        except np.linalg.LinAlgError:return
        warped=pic.transform((right-left,bot-top),Image.Transform.PERSPECTIVE,co,Image.Resampling.BILINEAR)
        im.alpha_composite(warped,(left,top))

    def world_planes(self,im,t,n=16,drive=1.,words=False):
        d=ImageDraw.Draw(im);cards=[]
        for i in range(n):
            a=i/n*math.tau+t*.16
            r=2.55+.35*math.sin(i*1.3)
            cx=math.cos(a)*r;cy=math.sin(a*1.4+i*.2)*1.2;z=math.sin(a)*1.05
            if n>18:
                cx=((i%7)-3)*.95+math.sin(t*.3+i)*.25
                cy=((i//7)-1.5)*.72;z=-.2+math.sin(i*.9+t*.22)*1.35
            cards.append((z,i,cx,cy))
        for z,i,cx,cy in sorted(cards):
            yaw=math.sin(t*.3+i*.7)*.38
            local=np.array([[-.55,.37,0],[.55,.37,0],[.55,-.37,0],[-.55,-.37,0]])
            local=rotate(local,yaw=yaw);local+=[cx,cy,z]
            den=3.5-local[:,2]
            q=np.c_[960+local[:,0]*1150/den,495-local[:,1]*1150/den]
            if q[:,0].max()<0 or q[:,0].min()>W:continue
            size=int(np.clip(240*3/(3.5-z),150,450))
            name=self.props[i%len(self.props)]
            label=(['DREAM','OCEAN','VOICE','WORLD','OUR','SKY'][i%6] if words else f'world.{i:03d}')
            pic=self.card(name,t+i*.5,size,int(size*.76),label,active=i==self.beat_index%n)
            self.plane(im,pic,q)
            x,y=q.mean(0);d.line((960,500,x,y),fill=color(BLUE,.12),width=1)

    def waves(self,im,t,word='OCEAN',age=1.,louder=False):
        self.cloud(im,'tide' if louder else 'ocean',t,(0,145,W,1035),scale=1.22,style='solid',opacity=.72)
        self.type3d.sculpture(im,word,t,(-60,180,1980,820),mode='wave',progress=ease(age/.6),gain=1.6,alpha=.95,yaw=math.sin(t*.18)*.17)
        d=ImageDraw.Draw(im)
        # Letter packets travel along the crests rather than occupying a fixed caption rectangle.
        for j in range(5):
            for i in range(23):
                x=80+i*87+(t*(20+j*7)%87)
                y=591+j*54+math.sin(x*.007+t*(.8+j*.09))*45
                text(im,(x,y),word[i%len(word)],int(17+j*2),color(ICE if (i+j)%7==0 else BLUE,.32+j*.09))

    def streams(self,im,t,words=None):
        words=words or ['OUR','COLORS','JOIN','A','SHINING','STREAM']
        self.cloud(im,'flow',t,(-140,-40,2060,1060),scale=1.65,style='solid',opacity=.48)
        self.type3d.glyph_ribbon(im,words,t,(960,496),scale=1.15,strength=1.)

    def explosion(self,im,t,age,origin=(960,500),power=1.):
        if age<0 or age>1.4:return
        d=ImageDraw.Draw(im);u=clamp(age/1.4)
        for i,r in enumerate(self.seeds[:150]):
            a=r[0]*math.tau;v=(310+r[1]*1300)*power
            radius=age*v;x=origin[0]+math.cos(a)*radius;y=origin[1]+math.sin(a)*radius*.64
            c=color(ICE if i%5==0 else BLUE,(1-u)*(.35+r[2]*.65))
            length=10+age*70
            d.line((x-math.cos(a)*length,y-math.sin(a)*length*.64,x,y),fill=(*c,int(250*(1-u))),width=2 if i%6 else 3)
            if i%14==0:text(im,(x,y),['FREE','01','WORLD','*'][i%4],16,c)
        for k in range(3):
            radius=(age*(820+k*260))
            d.ellipse((origin[0]-radius,origin[1]-radius*.55,origin[0]+radius,origin[1]+radius*.55),outline=color(ICE,(1-u)*.50/(k+1)),width=2)

    def shattered_window(self,im,t,age):
        if age<0:return
        if 'escape' not in self.shard_cache:self.shard_cache['escape']=self.dock(63.5)
        src=self.shard_cache['escape'];q=clamp(age/1.05)
        if q>=1:return
        for y in range(4):
            for x in range(8):
                box=(x*240,y*270,(x+1)*240,(y+1)*270);tile=src.crop(box)
                px=(x+.5)*240-W/2;py=(y+.5)*270-H/2
                phase=ease(clamp((q-(x+y)%3*.025)/.93))
                dx=px*phase*.85;dy=py*phase*.75
                tile=tile.rotate((x-y)*phase*7,Image.Resampling.BICUBIC,expand=True)
                tile.putalpha(int(255*(1-q)**1.4))
                im.alpha_composite(tile,(int(box[0]+dx-(tile.width-240)/2),int(box[1]+dy-(tile.height-270)/2)))

    def global_fx(self,im,t,s):
        mode=s['mode'];h=self.hit;d=ImageDraw.Draw(im)
        quiet=mode in ['opening','boot','return','archive','end','dock']
        n=100 if quiet else 300
        for i,r in enumerate(self.seeds[:n]):
            phase=(r[0]+t*(.07+r[4]*.12))%1
            x=r[1]*W;y=r[2]*H
            if not quiet:
                a=r[1]*math.tau+t*.025;radius=phase*1450
                x=960+math.cos(a)*radius;y=500+math.sin(a)*radius*.62
            c=color(ICE if i%17==0 else BLUE,(.22+r[3]*.45)*(1-phase)*(.5 if quiet else 1))
            if i%19==0:text(im,(x,y),f'{i:03X}',11,c)
            else:d.line((x,y,x-3-r[5]*10,y),fill=c,width=1)
        if not quiet:
            amp=h['kick']*.018+h['snare']*.008
            if amp>.005:
                for k in range(8):
                    x=70+k*253;length=20+140*h['snare']
                    d.line((x,77,x+length,77),fill=color(ICE,amp*15),width=2)
            if h['snare']>.42:
                yy=95+int(self.seeds[self.beat_index%560,0]*800)
                d.line((0,yy,W,yy),fill=color(BLUE,h['snare']*.3),width=1)

    def performance(self,im,t,mono=False):
        d=ImageDraw.Draw(im);phase=self.rhythm.phase('guitar',t)*.5
        cx=1100+math.sin(t*.8)*90;cy=527
        hero=self.performer.guitar(phase,t,850,970,silhouette=mono,ink=(242,247,255),drive=self.hit['guitar'])
        ox=int(cx-hero.width/2);oy=int(cy-hero.height/2-self.hit['kick']*13)
        if not mono:
            # Three moving edge afterimages provide attack/release without substituting a static image zoom.
            for k in [3,2,1]:
                ghost=hero.copy();ghost.putalpha(ghost.getchannel('A').point(lambda a:int(a*.035)))
                im.alpha_composite(ghost,(ox+k*15,oy+k*3))
        im.alpha_composite(hero,(ox,oy))
        source=(cx+50,cy+40)
        for k in range(8):
            x0,y0=source;points=[]
            for i in range(60):
                u=i/59;x=x0+(i-8)*20
                y=y0+math.sin(u*8-t*4+k*.8)*(25+70*self.hit['guitar'])*(1-u)+k*9
                points.append((x,y))
            d.line(points,fill=(220,229,249) if mono else color(BLUE,.35+.5*self.hit['guitar']),width=1 if k%2 else 2)
        if mono:
            # A few very large lyric shapes are negative-space partners in the performance.
            self.type3d.giant(im,'OCEAN',(45,215),128,ICE,angle=0)
            self.type3d.giant(im,'SET FREE',(60,674),100,ICE,angle=-5)
            for i in range(20):
                x=60+i*95;yy=H-95-math.sin(t*1.4+i*.5)*15
                d.line((x,yy,x+50,yy),fill=(225,233,247),width=2)
            # One authored expanding inversion replaces frequent full-screen strobing.
            if t>=118.12:
                mask=Image.new('L',(W,H));md=ImageDraw.Draw(mask);r=ease((t-118.12)/.46)*2400
                md.ellipse((source[0]-r,source[1]-r,source[0]+r,source[1]+r),fill=255)
                a=np.array(im);inv=a.copy();inv[:,:,:3]=255-inv[:,:,:3]
                im=Image.composite(Image.fromarray(inv),im,mask)
            if t>124.85:
                q=smooth((t-124.85)/.89)
                # Black/white performance breaks into blue data blocks on the way out.
                layer=Image.new('RGBA',(W,H));ld=ImageDraw.Draw(layer)
                for i,r in enumerate(self.seeds[:340]):
                    x=ox+r[0]*hero.width;y=oy+r[1]*hero.height
                    x+=(r[2]-.5)*q*1100;y-=(r[3]-.5)*q*700
                    ld.rectangle((x,y,x+6,y+6),fill=(*BLUE,int(240*q)))
                im.alpha_composite(layer)
        return im

    def history_scene(self,im,t,mode,e):
        d=ImageDraw.Draw(im)
        if mode=='history_signal':
            at=np.interp(e,[0,2.0,3.8,5.5,7.62],[0,1,2,3,3.6]);idx=min(3,int(at+.15))
            self.history.road(im,t,at);self.history.neurons(im,t,self.hit['snare']);self.history.label(im,idx)
            self.cloud(im,'relay',t,(-90,405,630,1010),scale=1.65,style='solid',opacity=.58)
        elif mode=='history_search':
            idx=4 if e<3.81 else 5;self.history.road(im,t,4+e/3.81)
            if e<3.81:self.history.tree(im,t,self.pulse,reverse=True)
            else:self.history.board(im,t,self.hit['kick'],go=False)
            self.history.label(im,idx)
        elif mode=='history_vision':
            idx=6 if e<3.81 else 7;self.history.road(im,t,6+e/3.81)
            if e<3.81:
                self.cloud(im,'char-flight',t,(280,95,1880,970),scale=1.5,style='solid',opacity=.75)
                for k in range(6):
                    x=680+k*170;y=220+math.sin(t*.4+k)*210
                    panel(im,(x,y,x+140,y+160),f'feature.{k}',BLUE,fill=False,level=.45)
                    for j in range(5):d.line((x+15,y+40+j*22,x+125,y+40+j*22),fill=color(BLUE,.25+j*.1))
            else:self.history.board(im,t,self.hit['snare'],go=True)
            self.history.label(im,idx)
        elif mode=='history_attention':
            idx=8 if e<3.81 else 9;self.history.road(im,t,8+e/3.81);self.history.attention(im,t,self.pulse);self.history.label(im,idx)
            self.cloud(im,'loom',t,(-130,410,660,1020),scale=1.7,style='solid',opacity=.45)
        else:
            idx=10 if e<1.7 else 11;self.history.road(im,t,10+e/1.7);self.history.label(im,idx)
            self.world_planes(im,t,24,words=False)
            chip(im,(68,841),'WEIGHTS / OPEN BRANCHES',True,BLUE,21)
            if e>1.7:chip(im,(72,902),'DeepSeek-R1 / MIT',True,ICE,23)

    def render(self,t,glow=True):
        self.context(t)
        s=next((s for s in self.plan if s['start']<=t<s['end']),self.plan[-1]);mode=s['mode'];e=t-s['start']
        im=Image.new('RGBA',(W,H),(*BG,255));self.stars(im,t,.50)
        self.spectacle.background(im,t,self.hit,mode)
        if mode=='opening':
            im=self.opener.draw(t,self.pulse)
            if t>9.526:im=self.opener.collapse(im,t,self.dock(t,boot_age=0))
        elif mode=='boot':im=self.dock(t,boot_age=e)
        elif mode=='dock':
            im=self.dock(t)
            if t>22.64:
                self.type3d.sculpture(im,'FLAME',t,(1050,320,1990,930),mode='flame',gain=1.15,alpha=.42)
        elif mode=='sky':
            self.cloud(im,'sky',t,WIDE,scale=1.1,style='solid',opacity=.55)
            self.actor(im,'launch',t,1480,530,780,940)
            self.type3d.sculpture(im,'SKY',t,(-50,170,1400,800),mode='orbit',gain=1.45,progress=ease(e/.7))
        elif mode=='lights':
            self.streams(im,t,['YOUR','LIGHT','MY','LIGHT'])
            self.actor(im,'present',t,500,550,720,920)
            self.type3d.giant(im,'YOUR LIGHT',(965,155),73,ICE)
            self.type3d.giant(im,'NEXT TO MINE',(926,770),55,BLUE)
        elif mode=='perform':
            self.cloud(im,'flow',t,(-150,70,2070,1010),scale=1.45,style='code',opacity=.35)
            self.world_planes(im,t,8)
            im=self.performance(im,t)
            self.type3d.giant(im,'COMPILE / PLAY',(50,111),54,ICE)
        elif mode=='dive':
            self.waves(im,t,'OCEAN',e,louder=True)
            self.cloud(im,'origami',t,(800,110,2080,880),scale=1.65,opacity=.4)
            self.type3d.glyph_ribbon(im,['CREATE','ADVECT','MESH','OPEN'],t,(960,530),.9,.6)
        elif mode=='glass':
            im=self.dock(t)
            release=smooth((e-.25)/1.1)
            if release>0:
                wider=Image.new('RGBA',(W,H),(*BG,255));self.stars(wider,t,.7);self.spectacle.background(wider,t,self.hit,mode);self.world_planes(wider,t,12)
                self.actor(wider,'reach',t,1120,530,1000,1030)
                self.type3d.sculpture(wider,'BEYOND',t,(-100,170,1500,700),mode='burst',progress=release,gain=1.3)
                if release<1:
                    # Fold the live terminal out to the sides of the emerging world.
                    ww=int(W*(1-release));left=im.crop((0,0,W//2,H)).resize((max(1,ww//2),H))
                    right=im.crop((W//2,0,W,H)).resize((max(1,ww//2),H))
                    wider.alpha_composite(left,(0,0));wider.alpha_composite(right,(W-right.width,0))
                im=wider
        elif mode in ['galaxy','satellite','voices','fugue']:
            self.world_planes(im,t,24 if mode in ['voices','fugue'] else 16,words=True)
            key='SATELLITE' if mode=='satellite' else 'VOICE' if mode=='voices' else 'WORLDS'
            if mode=='satellite':age=self.clock.age(t,10,'SATELLITE')
            elif mode=='voices':age=self.clock.age(t,14,'VOICE')
            else:age=e
            if age>0:self.type3d.sculpture(im,key,t,(320,200,1620,760),mode='orbit',gain=1.25,progress=ease(age/.45),alpha=.85)
            if mode=='galaxy':self.actor(im,'present',t,395,700,500,640,alpha=.9)
        elif mode=='city':
            self.cloud(im,'citadel',t,(380,-150,2060,1100),scale=1.65,style='solid')
            self.type3d.glyph_ribbon(im,['YOUR','SONGS','BECAME','THE','WORLDS'],t,(1000,530),1.12,.75)
            self.actor(im,'flight',t,420,625,780,700)
        elif mode=='ribbon':self.streams(im,t)
        elif mode=='ocean':
            line=8 if t<100 else 12
            age_o=self.clock.age(t,line,'OCEAN');age_f=self.clock.age(t,line,'FREE')
            self.waves(im,t,'OCEAN',max(0,age_o),True)
            if age_o>.1:
                whale=self.assets.object('whale',t,1170,670)
                im.alpha_composite(whale,(int(1120-whale.width/2+math.sin(t*.55)*65),int(475-whale.height/2)))
            if age_f>=0:
                self.shattered_window(im,t,age_f);self.explosion(im,t,age_f,(960,510),1.1)
                self.type3d.sculpture(im,'FREE',t,(-100,140,1800,830),mode='burst',progress=ease(age_f/.6),gain=1.6,alpha=.95)
            if t>100:self.actor(im,'reach',t,440,600,650,860,alpha=.9)
        elif mode=='louder':
            self.waves(im,t,'LOUDER',max(0,self.clock.age(t,9,'LOUDER')),True)
            self.type3d.glyph_ribbon(im,['NOW','ALL','OUR','SONGS','SEA'],t,(980,450),1.25,.65)
        elif mode=='alight':
            self.cloud(im,'sky',t,WIDE,scale=1.,style='solid',opacity=.4)
            self.world_planes(im,t,18,words=True)
            age=self.clock.age(t,11,'ALIGHT')
            self.type3d.sculpture(im,'TOGETHER' if age<0 else 'ALIGHT',t,(0,140,W,850),mode='burst' if age>0 else 'orbit',progress=ease(max(0,age if age>0 else e)/.6),gain=1.4)
            if age>0:self.explosion(im,t,age,(960,480),1.2)
        elif mode.startswith('history'):self.history_scene(im,t,mode,e)
        elif mode=='silhouette':
            im=self.monochrome.draw(t,self.hit,self.seeds)
        elif mode=='coauthor':
            self.world_planes(im,t,12)
            self.actor(im,'present',t,1275,520,880,980)
            self.type3d.giant(im,'YOUR TURN',(65,240),95,ICE)
            self.type3d.giant(im,'[ ENTER ]',(77,585),72,BLUE)
            cursor(im,(453,643),t,self.hit['snare'],label='human')
        elif mode=='portals':
            self.cloud(im,'tunnel',t,WIDE,scale=1.0,style='code',opacity=.5)
            self.world_planes(im,t,21)
            self.actor(im,'flight',t,960+math.sin(e*.6)*450,520,650,790)
            self.type3d.giant(im,'NO CLOSED WINDOW',(61,85),57,ICE)
        elif mode=='hands':
            self.actor(im,'present',t,1405,510,900,1030)
            self.cloud(im,'citadel',t,(-280,130,1390,1015),scale=1.6,style='solid',opacity=.62)
            age=self.clock.age(t,13,'HANDS')
            self.type3d.sculpture(im,'HANDS',t,(-50,80,1480,650),mode='wave',progress=ease(max(0,age)/.4),gain=1.35)
            age_w=self.clock.age(t,13,'WORLD')
            if age_w>0:self.explosion(im,t,age_w,(1050,440),.65)
        elif mode=='ignite':
            age=self.clock.age(t,15,'IGNITE')
            self.world_planes(im,t,28,words=True)
            self.actor(im,'triumph',t,1400,550,950,1000,alpha=.95)
            self.type3d.sculpture(im,'THOUSAND' if age<0 else 'IGNITE',t,(-300,10,1620,880),mode='burst',progress=1 if age<0 else ease(age/.5),gain=1.8,alpha=1.)
            if age>0:self.explosion(im,t,age,(900,440),1.5)
        elif mode=='jellyfish':
            self.cloud(im,'jellyfish',t,(-300,-180,2220,1120),scale=1.7,style='solid',opacity=.85)
            self.type3d.glyph_ribbon(im,['WORLDS','KEEP','GROWING'],t,(960,520),1.3,.7)
            self.actor(im,'turn',t,430,670,640,780,alpha=.9)
        elif mode=='home':
            self.world_planes(im,t,28)
            self.type3d.sculpture(im,'HOME',t,(-250,50,2110,950),mode='wave',gain=1.9,progress=1,alpha=1.)
            self.actor(im,'triumph',t,950,585,720,850,alpha=.78)
        elif mode in ['return','archive']:
            background=im;self.world_planes(background,t,10)
            page=self.dock(t)
            q=ease(e/.7) if mode=='return' else 1.
            ww=int(1370*q);hh=int(770*q)
            if ww>1:
                page=page.resize((ww,hh),Image.Resampling.LANCZOS)
                background.alpha_composite(page,((W-ww)//2,(H-hh)//2))
                ImageDraw.Draw(background).rectangle(((W-ww)//2,(H-hh)//2,(W+ww)//2,(H+hh)//2),outline=color(ICE,.5),width=1)
            im=background
        else:
            self.world_planes(im,t,10)
            hero=self.performer.greeting(t,820);im.alpha_composite(hero,(int(1430-hero.width/2),int(495-hero.height/2)))
            # A composed credit card, with all principal credits on screen.
            shade=Image.new('RGBA',(W,H));sd=ImageDraw.Draw(shade)
            sd.rounded_rectangle((45,120,1080,975),radius=14,fill=(3,7,17,232))
            im.alpha_composite(shade)
            d=ImageDraw.Draw(im)
            text(im,(88,160),'OCEAN.HOME / FINAL CREDITS',19,color(BLUE,.85))
            face=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc',102)
            d.text((80,214),'大肥鱼我的家乡',font=face,fill=(*ICE,255))
            d.line((90,365,985,365),fill=color(BLUE,.65),width=2)
            credits=['音乐原作：《大东北我的家乡》','改编：梨茗子','角色原作：上善（鲸鱼娘）','女仆形象设计：ZipZipPipe','视觉制作：AI 生图素材 · 字符艺术 · 代码渲染与动画','视觉研究参考：MisakaZentai《world.execute(me)》','代码剪影表现参考：《Bad Apple!!》','非官方同人音乐影像 · 角色相关美术遵循 CC BY-NC-SA 4.0']
            for i,caption in enumerate(credits):
                text(im,(92,407+i*55),caption,24 if i<4 else 22,TEXT,'cjk')
            text(im,(92,900),'让每一个声音，都成为一个新的世界。',25,ICE,'cjk')
        self.context(t)
        if mode not in ['opening','boot','silhouette']:
            if mode not in ['dock','return','archive','end']:
                im=self.spectacle.camera(im,t,self.hit,mode)
            self.global_fx(im,t,s)
            if mode not in ['dock','return','archive','end']:
                self.chrome(im,s);self.free_footer(im,t)
        if t>192.5:
            fade=1-smooth((t-192.5)/2.5);a=np.array(im);a[:,:,:3]=(a[:,:,:3]*fade).astype('u1');im=Image.fromarray(a)
        return post(im,t,glow and mode!='silhouette')
