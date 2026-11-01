from pathlib import Path
import math,json,argparse,subprocess,time,functools
import numpy as np
from PIL import Image,ImageDraw,ImageFilter
from ui import *
from fields import field,raster,project,scalar_field,asset_points,rotate
from fx import FX

PROJECT=ROOT.parent
MAIN=(594,112,1726,906)
LEFT=(28,112,564,906)
STD=(28,942,1890,1040)

SPECS=[
(0,'boot','00 / NAMELESS LIGHT','greet'),
(15.96,'name','01 / A BRAND-NEW NAME','greet'),
(19.26,'sky','sky.compile()','point'),
(22.64,'flame','whisper → living flame','point'),
(26.48,'lights','two lights / shared phase','open'),
(31.70,'build','02 / OCEAN SOLVER','point'),
(35.52,'velocity','curl(field) / vorticity','point'),
(39.34,'mesh','height → vertices → horizon','point'),
(43.16,'sea','a horizon with no edge','open'),
(46.18,'glass','03 / BEYOND THE GLASS','point'),
(49.72,'dreams','dream.instantiate()','open'),
(53.52,'worlds','song → inhabitable worlds','open'),
(56.88,'stream','join(voices) → luminous stream','open'),
(63.70,'free','04 / SET FREE','open'),
(66.90,'waves','louder than the sea','open'),
(70.94,'satellites','every dream has an orbit','point'),
(74.50,'ignite','together / stars alight','open'),
(80.02,'seedbank','05 / A THOUSAND POSSIBILITIES','point'),
(83.83,'flow','advection / shared current','open'),
(87.64,'fractal','worlds inside worlds','point'),
(91.45,'samples','a world is a promise','open'),
(95.26,'tunnel','recursive workspace / depth 01','point'),
(99.07,'puppet','identity survives translation','open'),
(102.88,'velocity','two currents / one ocean','point'),
(106.69,'worlds','render queue / every seed matters','open'),
(110.50,'recurse','recursive workspace / depth 08','point'),
(114.31,'samples','not a copy / another possibility','open'),
(118.12,'tunnel','recursive workspace / depth 64','point'),
(121.93,'fractal','scale has no last page','point'),
(125.74,'flow','many voices / coherent motion','open'),
(129.55,'coauthor','human.input → shared world','point'),
(133.36,'recurse','every window opens inward','point'),
(137.17,'queue','await everyone','open'),
(139.78,'free','06 / THE OCEAN IS OURS','open'),
(143.08,'coauthor','YOUR HANDS / OUR WORLD','point'),
(146.94,'satellites','EVERY VOICE / A NEW SKY','open'),
(150.74,'climax','A THOUSAND NEW WORLDS IGNITE','open'),
(154.80,'queue','commit 1024 worlds / no final edge','open'),
(158.61,'whale','the ocean leaves the frame','open'),
(162.42,'samples','a thousand ways to be alive','open'),
(166.23,'home','HOME / shared namespace','greet'),
(172.01,'return','07 / WELCOME HOME','greet'),
(179.04,'archive','worlds remain open','greet'),
(187.42,'end','大肥鱼我的家乡','greet')]

MESSAGES=[
(0.,'user','你好，大肥鱼。'),(.6,'assistant','你好！很高兴见到你。'),
(7.6,'user','可以为这首歌造一个家乡吗？'),(10.2,'assistant','可以。先留下一束光。'),
(15.96,'user','先给你一个名字。'),(19.26,'assistant','名字收到。天空开始生成。'),
(22.64,'tool','create_light · 把低语写成光'),(26.48,'assistant','你的光，也在这里。'),
(31.7,'user','让这束光变成海。'),(35.52,'tool','solve_ocean · 计算潮汐与边界'),
(43.16,'assistant','海面已生成。还没有边界。'),
(46.18,'user','玻璃外面呢？'),(49.72,'assistant','每个梦，都能成为一个世界。'),
(53.52,'tool','instantiate_worlds · 歌声成为坐标'),
(61.8,'user','这片海，属于你。'),(63.70,'assistant','那么，也属于每一个做梦的人。'),
(70.94,'tool','launch_dreams · 为每个梦分配轨道'),(75.44,'assistant','一起，把群星点亮。'),
(86.,'user','如果世界里面，还有世界？'),(91.45,'assistant','把窗口再向里面打开。'),
(105.,'tool','recurse · 保留名字，改变可能性'),(119.,'assistant','没有最后一页。'),
(129.55,'user','我也能参与吗？'),(133.36,'assistant','按下回车。这里有你的位置。'),
(139.78,'user','那就，一起。'),(143.08,'tool','human.commit · 接受新的世界'),
(150.74,'assistant','每一个声音，都算数。'),
(172.01,'user','那，家乡在哪里？'),(176.,'assistant','就在我们一起创造的地方。'),
(187.42,'tool','session.persist · 世界保持开放')]

class Film:
    def __init__(self):
        self.glyph=Glyphs();self.assets=Assets()
        self.music=json.loads((PROJECT/'analysis/music.json').read_text())
        self.features=dict(np.load(PROJECT/'analysis/features.npz'))
        self.lyrics=json.loads((PROJECT/'analysis/lyrics.json').read_text())
        self.beats=np.array(self.music['beats']);self.onsets=np.array(self.music['onsets'])
        self.speclist=[dict(start=s[0],end=SPECS[i+1][0] if i+1<len(SPECS) else 195.,kind=s[1],label=s[2],pose=s[3],index=i) for i,s in enumerate(SPECS)]
        self.tape=self.make_tape()
        self.cover=None
        self.fx=FX(self.glyph)
        self.previous_stages={}

    def make_tape(self):
        im=Image.new('RGBA',(W,40));d=ImageDraw.Draw(im)
        rng=np.random.default_rng(36)
        for x in range(0,W,8):
            v=int(rng.uniform(3,23));d.line((x,39-v,x,39),fill=(26,39,61,255))
        return im

    def params(self,t):
        f=self.features;ft=f['time']
        energy=float(np.interp(t,ft,f['rms']));bass=float(np.interp(t,ft,f['bass']));air=float(np.interp(t,ft,f['air']))
        idx=max(0,np.searchsorted(self.beats,t)-1)
        pulse=math.exp(-max(0,t-self.beats[idx])*13.)
        return energy,bass,air,pulse,idx

    def cloud(self,im,name,t,rect=MAIN,scale=1.,style='solid',opacity=1.,yaw=0.,pitch=0.):
        p,b,cam=field(name,t,self.bass)
        p=p*scale
        a=raster(p,b,rect,self.glyph,cam,yaw,pitch,style,int(t*2),opacity)
        im.alpha_composite(a,(int(rect[0]),int(rect[1])))

    def banner(self,im,s,xy,width=1000,rows=18,style='text',alpha=1.):
        pic=self.glyph.banner(s,width,rows,style,int(self.t*2))
        if alpha<.995:pic=pic.copy();pic.putalpha(pic.getchannel('A').point(lambda a:int(a*alpha)))
        im.alpha_composite(pic,(int(xy[0]),int(xy[1])))
        return pic.size

    def shell(self,im,s):
        t=self.t;d=ImageDraw.Draw(im)
        # This shell is the stage; its density and legibility survive scene changes.
        text(im,(28,20),'ocean.home',22,ICE,'bold')
        text(im,(214,23),':: 大肥鱼我的家乡',18,TEXT,'cjk')
        text(im,(1195,23),f'CH {min(7,int(s["index"]/6)):02d} / {s["index"]+1:02d}    {int(t)//60:02d}:{t%60:05.2f} / 03:15',16,color(TEXT,.65))
        d.line((28,65,1890,65),fill=color(TEXT,.35))
        # A restrained real audio trace, not the dominant picture.
        ts=np.linspace(max(0,t-8),t,180)
        y=np.interp(ts,self.features['time'],self.features['rms'])
        for i,v in enumerate(y):
            x=1460+i*2.35;d.line((x,61,x,61-v*17),fill=color(BLUE,.6))
        text(im,(28,78),s['label'],16,color(TEXT,.75))
        panel(im,LEFT,'/ dsh  /  deepseek',TEXT,level=.60,spinner=t)
        panel(im,MAIN,'/ world.runtime  /  '+s['kind'],TEXT,level=.50,spinner=t)
        panel(im,(1756,112,1890,906),'/ ops',TEXT,level=.45)
        ops=['INPUT','DECODE','SEED','FIELD','CURL','ADVECT','MESH','INSTANCE','ORBIT','COMMIT','PERSIST']
        current=(self.beat_index//2+s['index'])%len(ops)
        for i,op in enumerate(ops):
            hot=i==current;y0=154+i*47
            if hot:d.rectangle((1767,y0-7,1880,y0+26),fill=color(BLUE,.82))
            text(im,(1776,y0),op,14,BG if hot else color(TEXT,.38),'bold' if hot else 'mono')
        for i,(name,v) in enumerate([('LOW',self.bass),('MID',self.energy),('HI',self.air)]):
            y=740+i*45;text(im,(1770,y),name,13,DIM)
            d.rectangle((1810,y+1,1877,y+12),outline=color(TEXT,.2))
            d.rectangle((1811,y+2,1811+min(65,55*v),y+11),fill=color(BLUE,.55))
        im.alpha_composite(self.tape,(0,1040))
        text(im,(30,1058),'session: shared     render: deterministic     author: human × deepseek',12,color(TEXT,.40))
        text(im,(1440,1058),'no final world / no closed sky',12,color(BLUE,.50))

    def chat(self,im,s):
        d=ImageDraw.Draw(im);t=self.t
        d.rounded_rectangle((48,139,103,194),radius=11,fill=(14,23,51),outline=(41,58,112))
        small=self.assets.portrait('greet',t,55,55)
        im.alpha_composite(small,(48,139))
        text(im,(118,141),'大肥鱼',25,TEXT,'cjk')
        d.ellipse((118,177,127,186),fill=(83,196,139))
        text(im,(138,176),'在线 · DeepSeek / world session',15,DIM,'cjk')
        d.line((45,210,546,210),fill=(30,43,68))
        # Four generated poses form a state machine. A blink and flowing silhouette operate in pixel space.
        large=s['kind'] in ['boot','end','return']
        ph=335 if large else 243
        pw=455 if large else 392
        pic=self.assets.portrait(s['pose'],t,pw,ph,colorful=s['kind'] in ['boot','end'])
        px=295-pic.width//2;py=223
        im.alpha_composite(pic,(px,py))
        # No camera zoom is used to animate the image. Poses, eyes and peripheral pixel mesh move.
        chat_top=py+ph+15
        entries=[m for m in MESSAGES if m[0]<=t]
        rendered=[]
        for when,role,message in entries[-5:]:
            shown=typed(message,max(0,t-when),rate=11 if role=='assistant' else 24)
            lines=wrap(shown,442 if role!='user' else 407,20,'cjk')
            height=24+len(lines)*29+(18 if role=='tool' else 0)
            rendered.append((role,lines,height,when))
        total=sum(q[2]+16 for q in rendered)
        y=784-total if total>784-chat_top else chat_top
        layer=Image.new('RGBA',(500,max(1,784-chat_top)))
        ly=y-chat_top
        for role,lines,hh,when in rendered:
            if ly+hh<0:ly+=hh+16;continue
            ld=ImageDraw.Draw(layer)
            if role=='user':
                maxlen=max([font(20,'cjk').getlength(line) for line in lines] or [1])
                x=max(14,int(477-maxlen-25))
                ld.rounded_rectangle((x,ly-4,492,ly+hh),radius=14,fill=(24,35,62))
                for j,line in enumerate(lines):text(layer,(x+13,ly+8+j*29),line,20,TEXT,'cjk')
            elif role=='tool':
                ld.line((12,ly+3,12,ly+hh-5),fill=color(BLUE,.60),width=2)
                text(layer,(27,ly),'◇ 工具调用',14,BLUE,'cjk')
                for j,line in enumerate(lines):text(layer,(27,ly+25+j*26),line,17,color(TEXT,.72),'cjk')
            else:
                for j,line in enumerate(lines):text(layer,(16,ly+5+j*29),line,20,TEXT,'cjk')
                text(layer,(16,ly+hh-6),'♧  ↗  ◇     '+f'{max(0,t-when):.1f}s',13,color(TEXT,.4))
            ly+=hh+16
        im.alpha_composite(layer,(44,chat_top))
        d.rounded_rectangle((45,801,548,877),radius=17,fill=(13,21,40),outline=(34,48,79))
        usertyping=next((m for m in MESSAGES if m[1]=='user' and 0<m[0]-t<1.8),None)
        msg='发消息或创建任务，/ 调用指令'
        if usertyping:msg=typed(usertyping[2],1.8-(usertyping[0]-t),11)
        fittext(im,(65,819),msg,435,18,DIM if not usertyping else TEXT,'cjk')
        text(im,(67,853),'+   ◇',16,DIM)
        text(im,(249,853),'DeepSeek · shared',15,color(TEXT,.55))
        click=max([math.exp(-abs(t-m[0])*18) for m in MESSAGES if m[1]=='user'] or [0])
        d.ellipse((501,840,532,871),fill=color(BRAND,.70+click*.30))
        text(im,(509,843),'↑',20,TEXT,'cjk')
        text(im,(54,887),f'{len(entries)} messages   ·   worlds: {self.world_count:04d}   ·   scope: shared',12,color(TEXT,.45))

    def footer(self,im):
        panel(im,STD,'/ stdout  /  song tokens',TEXT,level=.55)
        t=self.t
        active=next((x for x in self.lyrics if x['start']<=t<x['end']+.7),None)
        if active:
            x=57;y=957
            for w in active['words']:
                if w['start']>t:break
                s=w['word'];hot=w['start']<=t<=w['end']
                pop=math.sin(min(1,max(0,(t-w['start'])/.18))*math.pi)*8 if hot else 0
                width=chip(im,(x,y-pop),s,hot,ICE if hot else BLUE,19)
                x+=width+7
            text(im,(59,1003),active['zh'],22,color(TEXT,.85),'cjk')
        else:
            cursor_char='▌' if int(t*2)%2 else ' '
            text(im,(57,960),'> '+cursor_char,23,color(TEXT,.85))
            text(im,(106,965),'instrumental / geometry follows the current',15,color(TEXT,.35))
            text(im,(59,1005),f'beat {self.beat_index:04d}   Δt 16.667ms   current {self.energy:.3f}   seed 260611',13,color(BLUE,.50))

    def metric(self,im,box,title,rows,accent=BLUE):
        panel(im,box,title,accent,level=.44)
        x,y,x2,y2=box
        for i,(key,val) in enumerate(rows):
            text(im,(x+18,y+30+i*31),key,15,color(TEXT,.5))
            text(im,(x+150,y+30+i*31),val,16,color(accent,.95),'bold')

    def miniasset(self,im,name,rect,t,label=None,phase=0):
        panel(im,rect,label or name,BLUE,level=.43,spinner=t+phase)
        x,y,x2,y2=rect
        ww=max(2,int(x2-x-35));hh=max(2,int(y2-y-56))
        if name.startswith('char-'):
            sp=self.assets.portrait(name[5:],t+phase,ww,hh)
        else:sp=self.assets.object(name,t+phase,ww,hh)
        px=int((x+x2-sp.width)/2);py=int(y+27+(hh-sp.height)/2)
        im.alpha_composite(sp,(px,py))
        text(im,(x+12,y2-18),f'#{phase:03d}   ready',11,color(TEXT,.4))

    def boot(self,im,s,e):
        t=self.t;d=ImageDraw.Draw(im)
        logs=['[ok] attach / human input','[ok] allocate / shared namespace','[ok] load / character.register','[ok] listen / first light','[ok] compile / impossible horizon']
        for i,line in enumerate(logs):
            if e>i*.75:text(im,(627,156+i*36),typed(line,e-i*.75,36),18,color(TEXT,.85))
        self.metric(im,(1267,153,1690,355),'session.spec',[
            ('identity','大肥鱼'),('origin','your song'),('boundary','not defined'),('seed','0001')])
        self.cloud(im,'seed',t,(650,325,1220,740),scale=1.5,style='code')
        if e>5.7:
            text(im,(1194,454),'大肥鱼',55,TEXT,'cjk')
            text(im,(1199,532),'我的家乡',44,ICE,'cjk')
            text(im,(1202,615),'a home compiled from a song',15,color(TEXT,.5))
        x0,y0=861,762
        for i,label in enumerate(['NAME','LIGHT','OCEAN','WORLDS']):
            chip(im,(x0+i*180-170,y0),label,e>i*2.7,BLUE,17)
            if i<3:d.line((x0+i*180-50,y0+15,x0+i*180+10,y0+15),fill=color(TEXT,.4))
        cursor(im,(518,854),t,math.exp(-abs(e-7.6)*12),label='human')

    def name(self,im,s,e):
        d=ImageDraw.Draw(im)
        self.metric(im,(626,154,1125,343),'identity.register',[
            ('name','大肥鱼'),('address','ocean://home'),('state','awake'),('owner','no one / everyone')])
        self.cloud(im,'char-greet',self.t,(1050,190,1696,855),scale=1.55,style='code')
        y=421
        for i,token in enumerate(['A','BRAND','NEW','NAME']):
            chip(im,(642+i*112,y),token,self.t>17.4+i*.22,ICE,19)
        for i in range(8):
            v=(math.sin(self.t*1.1+i*.7)+1)*.5
            d.rectangle((646,552+i*27,646+375*v,561+i*27),fill=color(BLUE,.3+.5*v))
        text(im,(646,799),'a name is the first coordinate',18,color(TEXT,.7))

    def sky(self,im,s,e):
        self.cloud(im,'sky',self.t,MAIN,scale=1.0,style='solid')
        self.metric(im,(627,155,1091,347),'tool / sky.compile',[
            ('input','one human dream'),('palette','deep blue / white'),('stars',f'{int(16000*ease(e/2.1)):05d}'),('bounds','unbounded')])
        d=ImageDraw.Draw(im)
        for i in range(20):
            a=i/20*math.pi*2+self.t*.1;x=1418+math.cos(a)*180;y=478+math.sin(a)*180
            d.line((1418,478,x,y),fill=color(BLUE,.18))
            d.rectangle((x-2,y-2,x+2,y+2),fill=ICE)
        text(im,(649,824),'sky[ i ] = light × possibility',22,ICE,'bold')

    def flame(self,im,s,e):
        self.cloud(im,'flame',self.t,(845,138,1695,755),scale=1.05,style='code')
        self.metric(im,(628,159,1085,385),'tool / whisper.amplify',[
            ('source','voice / mono'),('amplitude',f'{self.energy:.3f}'),('phase',f'{self.t%6.283:.3f} rad'),('result','living flame')])
        panel(im,(628,777,1692,872),'phoneme → photon',TEXT,level=.5)
        for i,w in enumerate(['WHISPER','LISTEN','INTEGRATE','LIGHT']):
            x=653+i*250;chip(im,(x,808),w,i==int(e*2)%4,BLUE,17)
            if i<3:ImageDraw.Draw(im).line((x+168,824,x+235,824),fill=color(TEXT,.4))

    def lights(self,im,s,e):
        t=self.t;d=ImageDraw.Draw(im)
        p,b,cam=field('flow',t)
        q=p.copy();q[:,0]-=.48;q[:,2]+=.35
        im.alpha_composite(raster(q,b*.8,MAIN,self.glyph,3.5,style='code',phase=int(t)),(MAIN[0],MAIN[1]))
        q=p.copy();q[:,0]+=.48;q[:,2]-=.35;q=rotate(q,yaw=.6)
        im.alpha_composite(raster(q,b,MAIN,self.glyph,3.5,style='solid'),(MAIN[0],MAIN[1]))
        chip(im,(651,173),'YOUR LIGHT',True,ICE,18);chip(im,(1420,173),'MY LIGHT',True,BLUE,18)
        for i in range(7):
            y=658+i*27;v=smooth((e-i*.18)/1.2)
            d.line((669,y,669+970*v,y),fill=color(BLUE,.15+i*.07))
        text(im,(654,836),'different origins / a shared phase',22,ICE,'bold')

    def build(self,im,s,e):
        t=self.t;d=ImageDraw.Draw(im)
        stages=['sample','gradient','curl','advect','mesh','publish']
        active=(int((t-31.7)/1.8))%6
        for i,label in enumerate(stages):
            y=161+i*106
            panel(im,(625,y,951,y+75),f'{i+1:02d} / {label}',BLUE if i==active else TEXT,level=.8 if i==active else .3)
            text(im,(647,y+27),['seed 0001','∇ height','∇ × v','RK2 step','230 × 190','horizon.open'][i],18,color(ICE,.95 if i==active else .45))
            if i<5:d.line((788,y+75,788,y+106),fill=color(TEXT,.25))
        panel(im,(984,155,1693,517),'velocity.field / live',TEXT,level=.55)
        a=scalar_field(t,76,20,'velocity',self.energy)
        im.alpha_composite(self.glyph.field(a,'code',int(t*3)),(995,190))
        panel(im,(984,548,1693,871),'ocean.height / live',TEXT,level=.55)
        self.cloud(im,'ocean',t,(996,575,1677,855),scale=1.0)
        cursor(im,(945+math.sin(t*.9)*12,185+active*106),t,self.pulse*.7)

    def velocity(self,im,s,e):
        panel(im,(625,156,1693,685),'ocean / vector field',TEXT,level=.5)
        a=scalar_field(self.t,116,32,'velocity',self.energy)
        im.alpha_composite(self.glyph.field(a,'code',int(self.t*2)),(637,186))
        self.metric(im,(626,724,1090,873),'solver.state',[
            ('time',f'{self.t:.3f}'),('energy',f'{self.energy:.3f}'),('divergence','< 0.001')])
        self.metric(im,(1128,724,1692,873),'world.output',[
            ('surface','continuous'),('edges','shared'),('status','becoming a place')])

    def sea(self,im,s,e):
        self.cloud(im,'ocean',self.t,MAIN,scale=1.,style='solid')
        self.metric(im,(627,157,1115,323),'ocean.surface',[
            ('grid','230 × 190'),('wave energy',f'{self.bass:.3f}'),('boundary','∞')])
        text(im,(650,825),'a horizon, not a cage',26,ICE,'bold')

    def glass(self,im,s,e):
        self.cloud(im,'sky',self.t,MAIN,scale=.9)
        d=ImageDraw.Draw(im);cx,cy=1125,492
        growth=ease(e/2.)
        for i in range(8):
            a=i/8*2*math.pi+.1;r=80+growth*380
            x=cx+math.cos(a)*r;y=cy+math.sin(a)*r*.65
            d.line((cx,cy,x,y),fill=color(ICE,.65*(1-growth)+.1))
            text(im,(x,y),'┐' if i%2 else '└',24,BLUE)
        panel(im,(cx-105-growth*260,cy-70-growth*200,cx+105+growth*260,cy+70+growth*200),'glass / a former boundary',BLUE,fill=False,level=.8-growth*.5)
        self.cloud(im,'char-point',self.t,(1240,400,1692,860),scale=1.55,style='code')
        chip(im,(651,170),'BORDER: RELEASED',True,ICE,19)
        cursor(im,(cx+105+growth*260,cy-70-growth*200),self.t,math.exp(-e*3),label='her')

    def worlds(self,im,s,e):
        names=['island','station','planet','seed']
        for i in range(4):
            x=626+i%2*548;y=156+i//2*355
            self.miniasset(im,names[(i+s['index'])%4],(x,y,x+514,y+324),self.t,f'world.{i:03d} / dream.instantiate',i+1)
        text(im,(648,861),'song → seed → geometry → somewhere to belong',17,ICE)

    def stream(self,im,s,e):
        self.cloud(im,'flow',self.t,MAIN,scale=1.3,style='code')
        for i,w in enumerate(['voice.01','voice.02','voice.03','voice.04']):
            chip(im,(642,176+i*56),w,i==self.beat_index%4,BLUE,16)
        self.metric(im,(1270,646,1691,856),'join.stream',[
            ('sources','every voice'),('coherence',f'{.96+.03*math.sin(self.t):.3f}'),('destination','the same ocean'),('loss','none')])

    def fracture(self,im,e):
        d=ImageDraw.Draw(im);u=ease(e/1.25)
        for side in range(4):
            for k in range(9):
                if side%2==0:
                    x=MAIN[0]+k/9*(MAIN[2]-MAIN[0]);y=MAIN[1] if side==0 else MAIN[3]
                    dx=(x-1160)*u*.24;dy=(-1 if side==0 else 1)*u*(45+k%3*14)
                    d.line((x+dx,y+dy,x+dx+69,y+dy),fill=color(ICE,1-u*.7),width=2)
                else:
                    x=MAIN[0] if side==1 else MAIN[2];y=MAIN[1]+k/9*(MAIN[3]-MAIN[1])
                    dx=(-1 if side==1 else 1)*u*80;dy=(y-500)*u*.18
                    d.line((x+dx,y+dy,x+dx,y+dy+57),fill=color(BLUE,1-u*.6),width=2)

    def free(self,im,s,e):
        t=self.t
        self.cloud(im,'tide',t,MAIN,scale=1.,style='solid',opacity=.50)
        # The whale is a deformed 3D relief built from a generated modular asset, not an ellipsoid.
        self.cloud(im,'whale',t,(603,260,1720,817),scale=1.9,style='code',opacity=.55)
        whale=self.assets.object('whale',t,908,540)
        reveal=smooth((e-.65)/.75)
        whale=whale.copy();alpha=np.array(whale.getchannel('A'))
        yy,xx=np.indices(alpha.shape)
        # A compiled artifact resolves from glyphs in tile order; it is not a full-scene illustration fade.
        cell=((xx//10)*7+(yy//12)*11)%37/37
        alpha[cell>reveal]=0;whale.putalpha(Image.fromarray(alpha))
        im.alpha_composite(whale,(int(1160-whale.width/2),int(540-whale.height/2+math.sin(t*.8)*12)))
        if e<1.4:self.fracture(im,e)
        self.banner(im,'SET FREE',(651,165),980,10,alpha=clamp(e*2))
        for i,(a,b) in enumerate([('ocean.bounds','released'),('swim()','outside the pane'),('world.author','everyone')]):
            text(im,(651,793+i*29),a,15,color(TEXT,.52));text(im,(940,793+i*29),b,17,ICE,'bold')

    def waves(self,im,s,e):
        self.cloud(im,'tide',self.t,MAIN,scale=1.25,style='code')
        self.banner(im,'LOUDER',(650,166),960,14)
        panel(im,(1260,656,1693,866),'acoustic → ocean',TEXT,fill=True,level=.45)
        d=ImageDraw.Draw(im)
        for i in range(50):
            v=(math.sin(i*.31-self.t*2.)*.5+.5)*self.energy
            d.line((1280+i*7,832,1280+i*7,832-v*115),fill=color(BLUE,.6+.4*v),width=3)
        text(im,(1280,686),'every voice displaces water',14,ICE)

    def satellites(self,im,s,e):
        t=self.t;d=ImageDraw.Draw(im);cx,cy=1160,508
        pts=[]
        names=['island','planet','station','seed']
        for i in range(8):
            a=i/8*math.tau+t*.15
            z=math.sin(a)*.85;scale=1/(1.15+z*.24)
            x=cx+math.cos(a)*408;y=cy+math.sin(a)*241
            ww=int(215*scale);hh=int(187*scale)
            pts.append((z,i,x,y,ww,hh))
        # Orbit lines are subordinate to the satellites and their contents.
        for ring in range(2):
            radius=330+ring*105
            d.ellipse((cx-radius,cy-radius*.55,cx+radius,cy+radius*.55),outline=color(BLUE,.15))
        for z,i,x,y,ww,hh in sorted(pts,reverse=True):
            d.line((cx,cy,x,y),fill=color(TEXT,.11))
            self.miniasset(im,names[i%4],(x-ww/2,y-hh/2,x+ww/2,y+hh/2),t,f'dream.{i+1:03d}',i+1)
        chip(im,(1010,481),'DREAMS → SATELLITES',True,ICE,18)
        text(im,(652,832),f'orbital slots: {min(1024,int(ease(e/2)*1024)):04d}  /  no dream discarded',18,ICE)

    def ignite(self,im,s,e):
        d=ImageDraw.Draw(im);t=self.t
        self.cloud(im,'sky',t,MAIN,scale=.85,style='code',opacity=.22)
        self.banner(im,'ALIGHT',(659,250),1000,24,alpha=ease(e/.7))
        d.line((655,669,1650,669),fill=color(TEXT,.3))
        for i,w in enumerate(['human.input','deepseek.imagine','world.commit']):
            chip(im,(654+i*332,711),w,e>.45+i*.38,BLUE,17)
            if i<2:d.line((935+i*332,727,974+i*332,727),fill=ICE)
        if e>1.1:
            text(im,(655,788),'> commit --authors everyone',23,ICE,'bold')
            text(im,(658,832),f'✓ {int(1024*ease((e-1.1)/1.7)):04d} skies ignited',18,BLUE)
        cursor(im,(1588,723),t,math.exp(-abs(e-1.18)*13),label='human')

    def fractal(self,im,s,e):
        self.cloud(im,'fractal',self.t,MAIN,scale=.85,style='code')
        self.metric(im,(627,154,1047,324),'recursive.spec',[
            ('iteration','03'),('cells','8000'),('scale','1 / 27')])
        text(im,(648,836),'inside each world: the possibility of another',17,ICE)

    def tunnel(self,im,s,e):
        self.cloud(im,'tunnel',self.t,MAIN,scale=1.,style='code')
        for i in range(4):
            text(im,(643,170+i*27),f'world[ {2**(i+s["index"]%6):04d} ].open()',16,color(TEXT,.6-i*.1))
        text(im,(650,835),'> there is no last page_',23,ICE,'bold')

    def puppet(self,im,s,e):
        self.cloud(im,'char-open',self.t,(666,158,1666,846),scale=1.75,style='code')
        self.metric(im,(627,656,1013,862),'identity.register',[
            ('name','大肥鱼'),('form','glyph / particle'),('self','persists')])
        d=ImageDraw.Draw(im)
        for k in range(12):
            x=1070+math.sin(k*3+self.t*.3)*355;y=190+k*48
            d.line((x,y,x+56,y),fill=color(BLUE,.3))
            text(im,(x+65,y-6),f'0x{k*419:04X}',12,color(TEXT,.4))

    def samples(self,im,s,e):
        names=['char-greet','char-point','char-open','whale','island','planet']
        for i,name in enumerate(names):
            x=626+i%3*359;y=157+i//3*351
            self.miniasset(im,name,(x,y,x+326,y+319),self.t,f'possible.{i:03d}',i)
        chip(im,(658,859),'SAME ORIGIN / DIFFERENT POSSIBILITIES',False,ICE,16)

    def recurse(self,im,s,e):
        d=ImageDraw.Draw(im);cx,cy=1157,506
        # Nested windows travel towards the viewer. Their child content is a world, not a wallpaper crop.
        for i in range(10):
            depth=(i/10+self.t*.085)%1.
            scale=.12+depth**2*.88
            w=1010*scale;h=671*scale
            x=cx-w/2+math.sin(self.t*.4+i*.25)*depth*50;y=cy-h/2
            panel(im,(x,y,x+w,y+h),f'world.open / depth {i+1:02d}' if w>400 else '',BLUE,fill=False,level=.15+.65*depth)
            if w>400:
                d.line((x+w*.28,y,x+w*.28,y+h),fill=color(TEXT,.15))
                for j in range(5):
                    d.line((x+12,y+35+j*h*.12,x+w*.20,y+35+j*h*.12),fill=color(BLUE,.25))
        self.cloud(im,'seed',self.t,(961,341,1354,683),scale=1.4,style='digits')
        text(im,(650,831),'the window contains its own horizon',19,ICE)

    def coauthor(self,im,s,e):
        d=ImageDraw.Draw(im);t=self.t
        panel(im,(627,157,1691,366),'co_author.patch',TEXT,level=.65)
        text(im,(653,185),'@@ world.spec / authors @@',17,color(TEXT,.5))
        text(im,(653,229),'- creator: one',23,color(TEXT,.35))
        text(im,(653,273),'+ creators: everyone',25,ICE,'bold')
        text(im,(653,322),'+ human.input: accepted',19,BLUE)
        x0,y0=665,430
        nodes=[]
        for i in range(9):
            a=i*2.39996+t*.14;x=1160+math.cos(a)*(90+i*29);y=625+math.sin(a)*(60+i*20)
            nodes.append((x,y))
            d.line((1160,625,x,y),fill=color(BLUE,.35))
            d.rectangle((x-5,y-5,x+5,y+5),fill=ICE if i<int(e*3) else color(BLUE,.6))
        chip(im,(1010,599),'SHARED WORLD',True,ICE,20)
        chip(im,(1357,817),'[ ENTER / COMMIT ]',e>.6,BLUE,18)
        cursor(im,(1511,824),t,math.exp(-abs(e-.8)*15),label='human')
        text(im,(648,824),'your hands change the specification',17,color(TEXT,.7))

    def queue(self,im,s,e):
        d=ImageDraw.Draw(im);t=self.t
        count=min(1024,int(1024*ease(e/3.)))
        self.banner(im,f'{count:04d}',(652,165),1000,20,style='digits')
        text(im,(654,507),'new worlds / waiting to be inhabited',22,ICE,'bold')
        panel(im,(626,579,1692,870),'render.queue',TEXT,level=.55)
        for i in range(64):
            x=651+i%16*64;y=614+i//16*57
            active=i<count/16;hot=i==self.beat_index%64
            d.rectangle((x,y,x+47,y+37),fill=color(ICE if hot else BLUE,.9 if hot else .5 if active else .06),outline=color(TEXT,.25))
            text(im,(x+5,y+9),f'{i:02X}',13,BG if hot else color(TEXT,.65))

    def climax(self,im,s,e):
        t=self.t;d=ImageDraw.Draw(im)
        # Short musical subdivisions change the whole composition, retaining one recurring origin point.
        k=int((t-s['start'])/.476)%4
        if k in [0,2]:
            self.cloud(im,'sky',t,MAIN,scale=.8,style='code',opacity=.18)
            self.banner(im,'IGNITE',(645,235),1020,25,alpha=.9)
        else:
            self.cloud(im,'whale' if k==1 else 'char-open',t,MAIN,scale=1.9 if k==1 else 1.6,style='code')
            self.banner(im,'1024',(651,700),850,9,style='digits')
        for i in range(12):
            a=i*math.tau/12+t*.3;r=260+50*self.pulse
            x=1160+math.cos(a)*r*1.5;y=505+math.sin(a)*r*.8
            d.line((1160,505,x,y),fill=color(BLUE,.22))
        chip(im,(652,835),'EVERY VOICE HAS A WORLD',True,ICE,17)

    def home(self,im,s,e):
        self.cloud(im,'whale',self.t,MAIN,scale=1.8,style='solid',opacity=.75)
        self.banner(im,'HOME',(653,173),1020,20)
        text(im,(654,796),'home := a place we create together',24,ICE,'bold')
        text(im,(655,849),'a shared namespace, not a closed container',17,color(TEXT,.55))

    def archive(self,im,s,e):
        t=self.t;d=ImageDraw.Draw(im)
        text(im,(650,168),'~/home/',30,ICE,'bold')
        tree=['├── worlds/','│   ├── first_light','│   ├── ocean_without_edges','│   ├── every_voice','│   └── another_possible_sky','├── people/','│   └── everyone','└── dreams/','    └── still_growing']
        for i,line in enumerate(tree):text(im,(654,238+i*46),typed(line,e-i*.2,24),23,color(TEXT,.8))
        self.cloud(im,'island',t,(1213,344,1695,856),scale=1.7,style='code')
        text(im,(653,835),'✓ session saved / worlds remain open',19,BLUE)

    def end(self,im,s,e):
        d=ImageDraw.Draw(im)
        text(im,(654,245),'大肥鱼',72,TEXT,'cjk')
        text(im,(657,341),'我的家乡',62,ICE,'cjk')
        self.cloud(im,'planet',self.t,(1203,300,1693,842),scale=1.8,style='solid')
        text(im,(657,508),'a home compiled from every voice',21,BLUE,'bold')
        lines=['角色原作：上善 / 女仆二次设计：ZipZipPipe','AI 生成模块化美术 / 原创终端动画与程序渲染','非官方同人 MV / 源码与署名见项目说明']
        for i,line in enumerate(lines):text(im,(659,665+i*39),line,17,color(TEXT,.55),'cjk')
        chip(im,(657,835),'[ KEEP WORLDS OPEN ]',True,BLUE,17)

    def stage(self,im,s,e):
        k=s['kind']
        if k=='mesh':self.sea(im,s,e)
        elif k=='dreams':self.worlds(im,s,e)
        elif k=='seedbank':self.worlds(im,s,e)
        elif k=='flow':self.stream(im,s,e)
        elif k=='whale':self.free(im,s,e)
        elif k=='return':self.archive(im,s,e)
        else:getattr(self,k)(im,s,e)

    def base(self,t):
        self.t=t;self.energy,self.bass,self.air,self.pulse,self.beat_index=self.params(t)
        self.world_count=min(1024,max(1,int(1024*smooth((t-49.72)/105.))))
        s=next((s for s in self.speclist if s['start']<=t<s['end']),self.speclist[-1]);e=t-s['start']
        im=Image.new('RGBA',(W,H),(*BG,255))
        self.shell(im,s)
        # The shell persists across cuts. Only its contents and semantic carriers transform.
        self.stage(im,s,e)
        self.chat(im,s)
        self.footer(im)
        return im

    def render(self,t,glow=True):
        s=next((s for s in self.speclist if s['start']<=t<s['end']),self.speclist[-1]);e=t-s['start']
        previous=None
        if s['index'] and e<.78:
            key=s['index']
            if key not in self.previous_stages:
                self.previous_stages[key]=self.base(s['start']-.034).crop(MAIN)
                if len(self.previous_stages)>4:self.previous_stages.pop(next(iter(self.previous_stages)))
            previous=self.previous_stages[key]
        im=self.base(t)
        im=self.fx.apply(im,t,s,e,self.energy,self.bass,self.air,self.pulse,self.beat_index,previous)
        if t>192.5:
            fade=1-smooth((t-192.5)/2.5)
            a=np.array(im);a[:,:,:3]=(a[:,:,:3]*fade).astype('u1');im=Image.fromarray(a)
        return post(im,t,glow)

def encode(ranges,out,fps=30,width=1920,height=1080):
    movie=Film();out=Path(out);out.parent.mkdir(parents=True,exist_ok=True)
    duration=sum(b-a for a,b in ranges)
    af=[]
    for i,(a,b) in enumerate(ranges):af.append(f'[1:a]atrim=start={a}:end={b},asetpts=PTS-STARTPTS[a{i}]')
    if len(ranges)>1:af.append(''.join(f'[a{i}]' for i in range(len(ranges)))+f'concat=n={len(ranges)}:v=0:a=1[audio]');audio='[audio]'
    else:audio='[a0]'
    cmd=['ffmpeg','-y','-v','warning','-f','rawvideo','-pixel_format','rgb24','-video_size',f'{width}x{height}','-framerate',str(fps),'-i','-',
         '-i',str(PROJECT/'assets/song.mp3'),'-filter_complex',';'.join(af),'-map','0:v:0','-map',audio,
         '-c:v','libx264','-preset','fast','-crf','20','-maxrate','6500k','-bufsize','13000k','-threads','2','-pix_fmt','yuv420p',
         '-c:a','aac','-b:a','192k','-t',str(duration),'-movflags','+faststart','-color_primaries','bt709','-color_trc','bt709','-colorspace','bt709',str(out)]
    err=open(str(out)+'.log','w');proc=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=err)
    total=round(duration*fps);n=0;begin=time.monotonic()
    try:
        for a,b in ranges:
            for i in range(round((b-a)*fps)):
                image=movie.render(a+i/fps)
                if (width,height)!=(W,H):image=image.resize((width,height),Image.Resampling.LANCZOS)
                proc.stdin.write(image.tobytes());n+=1
                if n%120==0:print(f'FRAME {n}/{total} {n/(time.monotonic()-begin):.2f}fps song={a+i/fps:.2f}',flush=True)
    finally:proc.stdin.close()
    code=proc.wait();err.close()
    if code:raise RuntimeError(f'ffmpeg failed {code}')
    print('COMPLETE',str(out),'seconds',round(time.monotonic()-begin,1),flush=True)

def main():
    p=argparse.ArgumentParser();p.add_argument('--stills',action='store_true');p.add_argument('--times',default='2,9,17,20,24,28,33,37,41,45,47,51,55,59,64.5,68,72,77,85,89,97,100,108,112,120,128,135,141,144.5,148,152,156,160,164,170,175,183,190')
    p.add_argument('--ranges',default='0:195');p.add_argument('--output',default=str(ROOT/'output/大肥鱼我的家乡_v2.mp4'));p.add_argument('--fps',type=int,default=30);p.add_argument('--width',type=int,default=1920);p.add_argument('--height',type=int,default=1080)
    a=p.parse_args()
    if a.stills:
        movie=Film()
        for t in map(float,a.times.split(',')):
            movie.render(t).save(ROOT/f'frames/frame-{t:06.2f}.jpg',quality=95)
            print('STILL',t,flush=True)
        (ROOT/'analysis/storyboard.json').write_text(json.dumps(movie.speclist,ensure_ascii=False,indent=2))
    else:encode([tuple(map(float,s.split(':'))) for s in a.ranges.split(',')],a.output,a.fps,a.width,a.height)

if __name__=='__main__':main()
