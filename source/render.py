from pathlib import Path
import os,json,math,time,subprocess,argparse,functools
os.environ.setdefault('LIBGL_ALWAYS_SOFTWARE','1')
os.environ.setdefault('LP_NUM_THREADS','4')
import numpy as np
import moderngl as gl
from PIL import Image,ImageDraw,ImageFont
from geometry import geometries

ROOT=Path(__file__).resolve().parents[1]
FONT='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
SERIF='/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc'
MONO='/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf'
CYAN=(140,224,240,255);WHITE=(227,239,247,255);DIM=(85,128,151,255)

def smooth(a,b,x):
    q=np.clip((x-a)/(b-a),0.,1.);return float(q*q*(3.-2.*q))

def perspective(fov,aspect,near=.1,far=220.):
    s=1/math.tan(fov/2)
    return np.array([[s/aspect,0,0,0],[0,s,0,0],[0,0,(far+near)/(near-far),2*far*near/(near-far)],[0,0,-1,0]],dtype='f4')

def lookat(eye,target):
    e=np.array(eye,dtype=float);f=np.array(target)-e;f/=np.linalg.norm(f)
    r=np.cross(f,[0,1,0]);r/=np.linalg.norm(r);u=np.cross(r,f)
    return np.array([[*r,-r@e],[*u,-u@e],[*(-f),f@e],[0,0,0,1]],dtype='f4')

@functools.lru_cache(maxsize=32)
def font(size,kind='sans'):
    return ImageFont.truetype({'sans':FONT,'serif':SERIF,'mono':MONO}[kind],size)

def track_text(draw,xy,text,size=20,spacing=4,fill=DIM,kind='mono'):
    x,y=xy;f=font(size,kind)
    for c in text:
        draw.text((x,y),c,font=f,fill=fill);x+=draw.textlength(c,font=f)+spacing

def storyboard():
    # All edits can be changed without regenerating character or environment art.
    specs=[
    (0,'greeting','seed','00 / HELLO, WORLD',0.0,'greeting'),
    (4.2,'greeting','orbit','a name, a home',.12,'boot'),
    (8.1,'greeting','orbit','大肥鱼我的家乡',.22,'title'),
    (12.2,None,'seed','01 / FIRST LIGHT',.5,'seed'),
    (15.8,'awakening',None,'consciousness.begin()',0.,'sleep'),
    (19.2,'awake',None,'I can see your light',0.,'eyes'),
    (23.0,'hero','seed','a whisper becomes a flame',.5,'scan'),
    (27.1,'hero','orbit','two lights / one sky',.6,'hero'),
    (31.7,None,'sea','tool.create_ocean',.8,'compile'),
    (39.5,None,'sea','the horizon is a possibility',1.,'sea'),
    (47.45,'awake',None,'02 / BEYOND THE GLASS',0.,'eyes'),
    (51.5,None,'worlds','tool.instantiate_worlds',.8,'worlds'),
    (55.4,'hero','flow','all our colors / one stream',.6,'left'),
    (59.4,None,'flow','connection: open',1.2,'flow'),
    (63.55,None,'whale','03 / SET FREE',1.4,'whale'),
    (67.6,'ocean',None,'the sea remembers every song',0.,'matte'),
    (71.4,'hero','orbit','I AM THE OCEAN',1.1,'hero'),
    (74.5,'hands',None,'together / stars alight',0.,'hands'),
    (79.2,'ocean',None,'a thousand possible horizons',0.,'matte'),
    (83.1,'hero','flow','together / stars alight',1.3,'left'),
    (87.1,None,'fractal','worlds inside worlds',1.1,'fractal'),
    (93.97,None,'tunnel','04 / RECURSIVE SKY',1.3,'tunnel'),
    (97.9,None,'avatar','a name becomes a living constellation',.9,'avatar'),
    (101.8,None,'flow','render(next_world)',1.7,'flow'),
    (105.6,None,'worlds','each dream has its own gravity',1.7,'worlds'),
    (108.46,None,'fractal','many voices / one constellation',1.0,'fractal'),
    (112.3,None,'avatar','identity persists across worlds',1.1,'avatar'),
    (116.2,None,'tunnel','possibility is recursive',1.7,'tunnel'),
    (120.1,None,'orbit','an orbit, made of voices',1.6,'orbit'),
    (124.05,'hero','whale','a home without edges',1.1,'left'),
    (128.0,None,'flow','the next world is yours',1.6,'flow'),
    (132.0,'hands',None,'05 / HUMAN × DEEPSEEK',0.,'hands'),
    (136.0,None,'avatar','two authors / infinite worlds',1.1,'avatar'),
    (139.78,'hero','orbit','06 / THE OCEAN IS FREE',1.5,'hero'),
    (143.08,'hands',None,'your hands / our universe',0.,'hands'),
    (146.94,None,'worlds','every voice has a world',1.9,'worlds'),
    (150.74,'hero','flow','a thousand new worlds ignite',1.7,'left'),
    (154.8,None,'seed','co_create(universe)',1.9,'ignition'),
    (156.5,None,'whale','the ocean is free',1.8,'whale'),
    (160.4,'hero','flow','let the new worlds ignite',1.6,'left'),
    (164.35,'ocean',None,'HOME IS WHAT WE CREATE',0.,'matte'),
    (172.01,'greeting','worlds','06 / WELCOME HOME',.4,'return'),
    (179.04,'ocean',None,'a universe, still becoming',0.,'matte'),
    (187.42,'greeting','orbit','大肥鱼我的家乡',.22,'end'),
    ]
    out=[]
    for i,(start,art,geo,label,gain,style) in enumerate(specs):
        end=specs[i+1][0] if i+1<len(specs) else 195.
        out.append(dict(start=start,end=end,art=art,geometry=geo,label=label,gain=gain,style=style,index=i))
    return out

class Renderer:
    def __init__(self,width=1920,height=1080):
        self.w,self.h=width,height
        self.ctx=gl.create_standalone_context(backend='egl',require=330)
        print('RENDERER',self.ctx.info['GL_RENDERER'],flush=True)
        self.ctx.enable(gl.BLEND|gl.PROGRAM_POINT_SIZE)
        self.ctx.blend_func=(gl.SRC_ALPHA,gl.ONE_MINUS_SRC_ALPHA)
        self.scene=self.ctx.texture((width,height),4,dtype='f2')
        self.fbo=self.ctx.framebuffer([self.scene])
        self.final=self.ctx.texture((width,height),3)
        self.finalfbo=self.ctx.framebuffer([self.final])
        self.bloom1=self.ctx.texture((width//4,height//4),4,dtype='f2')
        self.bloom2=self.ctx.texture((width//4,height//4),4,dtype='f2')
        self.bfbo1=self.ctx.framebuffer([self.bloom1]);self.bfbo2=self.ctx.framebuffer([self.bloom2])
        self.scene.filter=(gl.LINEAR,gl.LINEAR)
        self.bloom1.filter=self.bloom2.filter=(gl.LINEAR,gl.LINEAR)
        vs='''#version 330
        in vec2 position;out vec2 uv;
        void main(){uv=position*.5+.5;gl_Position=vec4(position,0,1);}'''
        self.quad=self.ctx.buffer(np.array([-1,-1,1,-1,-1,1,1,1],dtype='f4').tobytes())
        self.bg=self.ctx.program(vertex_shader=vs,fragment_shader=(ROOT/'source/background.frag').read_text())
        self.bgv=self.ctx.simple_vertex_array(self.bg,self.quad,'position')
        self.post=self.ctx.program(vertex_shader=vs,fragment_shader=(ROOT/'source/post.frag').read_text())
        self.postv=self.ctx.simple_vertex_array(self.post,self.quad,'position')
        self.blur=self.ctx.program(vertex_shader=vs,fragment_shader=(ROOT/'source/bloom.frag').read_text())
        self.blurv=self.ctx.simple_vertex_array(self.blur,self.quad,'position')
        self.geo=self.ctx.program(vertex_shader=(ROOT/'source/scene.vert').read_text(),fragment_shader=(ROOT/'source/scene.frag').read_text())
        atlas=Image.new('L',(192,192));ad=ImageDraw.Draw(atlas)
        glyphs='01<>[]{}+-=:.*/#@ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
        for i,c in enumerate(glyphs[:64]):
            ad.text((i%8*24+12,i//8*24+12),c,font=font(20,'mono'),anchor='mm',fill=255)
        atlas=atlas.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
        self.glyphs=self.ctx.texture(atlas.size,1,atlas.tobytes());self.glyphs.filter=(gl.LINEAR,gl.LINEAR)
        self.geo['glyphs'].value=3
        self.objects={};rng=np.random.default_rng(246)
        for k,(pts,lines,mode) in geometries().items():
            def buf(p):
                if not len(p):return None
                a=(p if p.shape[1]==4 else np.c_[p,rng.random(len(p))]).astype('f4')
                return self.ctx.simple_vertex_array(self.geo,self.ctx.buffer(a.tobytes()),'position','seed')
            self.objects[k]=(buf(pts),buf(lines),mode)
        self.card=self.ctx.program(vertex_shader=(ROOT/'source/card.vert').read_text(),fragment_shader=(ROOT/'source/card.frag').read_text())
        v=[];idx=[];n=28
        for j in range(n+1):
            for i in range(n+1):v.append([i/n-.5,j/n-.5,i/n,j/n])
        for j in range(n):
            for i in range(n):
                k=j*(n+1)+i;idx.extend([k,k+1,k+n+1,k+1,k+n+2,k+n+1])
        self.cv=self.ctx.vertex_array(self.card,[(self.ctx.buffer(np.array(v,dtype='f4').tobytes()),'2f 2f','vertex','texcoord')],self.ctx.buffer(np.array(idx,dtype='i4').tobytes()))
        self.images={}
        for name in ['greeting','hero','awakening','awake','ocean','hands']:
            self.images[name]=self.texture(Image.open(ROOT/f'assets/{name}.png'))
        self.overlay_cache={};self.lyric_cache={}
        self.transition_cache={}
        self.blank=self.ctx.texture((1,1),3,b'\x00\x00\x00')
        self.music=json.loads((ROOT/'analysis/music.json').read_text())
        self.features=dict(np.load(ROOT/'analysis/features.npz'))
        self.beats=np.array(self.music['beats']);self.onsets=np.array(self.music['onsets'])
        self.lyrics=json.loads((ROOT/'analysis/lyrics.json').read_text())
        self.shots=storyboard()
        self.proj=perspective(math.radians(47),width/height)

    def texture(self,im):
        im=im.convert('RGBA').transpose(Image.Transpose.FLIP_TOP_BOTTOM)
        tex=self.ctx.texture(im.size,4,im.tobytes());tex.build_mipmaps();tex.filter=(gl.LINEAR_MIPMAP_LINEAR,gl.LINEAR)
        return tex

    def card_draw(self,tex,x,y,w,h,t,opacity=1.,warp=0.,reveal=1.2,scan=0.,grade=(1.,1.,1.)):
        self.ctx.blend_func=(gl.SRC_ALPHA,gl.ONE_MINUS_SRC_ALPHA)
        self.card['rect'].value=(x/960.-1.,1.-y/540.,w/960.,h/540.)
        self.card['time'].value=t;self.card['warp'].value=warp
        self.card['opacity'].value=float(opacity);self.card['reveal'].value=float(reveal);self.card['scan'].value=float(scan)
        self.card['grade'].value=grade;self.card['image'].value=0;tex.use(0)
        self.cv.render()

    def camera(self,key,t,u,variant=0):
        if key=='sea':
            return ([math.sin(t*.08)*4.,3.2+math.sin(t*.05)*1.1,19.-u*8.],[0,-1.,-17.])
        if key=='whale':return ([12.-u*11.,5.+math.sin(t*.09)*2.,22.-u*4.],[0,0,0])
        if key=='tunnel':return ([math.sin(t*.4)*.6,math.cos(t*.3)*.5,8.],[0,0,-30.])
        if key=='worlds':return ([math.cos(t*.045)*30.,10.+math.sin(t*.04)*5.,math.sin(t*.045)*30.],[0,0,0])
        if key=='avatar':return ([math.sin(t*.06)*1.5,0,17.],[0,0,0])
        if key=='fractal':return ([math.cos(t*.045)*17.,7.+math.sin(t*.03)*3.,math.sin(t*.045)*17.],[0,0,0])
        if key=='flow':return ([math.sin(t*.07)*10.,3.+math.cos(t*.06)*3.,13.],[0,0,0])
        if key=='orbit':return ([math.cos(t*.07)*11.,5.+math.sin(t*.06)*3.,math.sin(t*.07)*7.+10.],[0,0,0])
        return ([math.sin(t*.05)*3.,2.,13.-u*2.],[0,0,0])

    def draw_geo(self,key,t,u,bass,beat,gain,variant=0):
        pts,lines,mode=self.objects[key];eye,target=self.camera(key,t,u,variant)
        mvp=self.proj@lookat(eye,target)
        if key!='stars':mvp[0]+=getattr(self,'stage_shift',0)*mvp[3]
        self.geo['mvp'].write(mvp.T.astype('f4').tobytes());self.geo['mode'].value=mode
        self.geo['time'].value=t;self.geo['bass'].value=bass;self.geo['beat'].value=beat
        self.geo['height'].value=float(self.h)
        self.geo['ascii_mode'].value=int(key=='avatar' or (key in ['worlds','tunnel'] and 90<t<140))
        self.glyphs.use(3)
        self.ctx.blend_func=(gl.SRC_ALPHA,gl.ONE)
        if lines is not None:
            self.geo['ispoint'].value=0;self.geo['gain'].value=gain*(.38 if key=='worlds' else .75);lines.render(gl.LINES)
        if pts is not None:
            self.geo['ispoint'].value=1;self.geo['gain'].value=gain;pts.render(gl.POINTS)

    def overlay(self,shot,elapsed):
        style=shot['style'];q=int(min(elapsed,7)*8) if style in ['boot','compile','seed','ignition','sleep','eyes'] else 0
        key=(shot['index'],q)
        if key in self.overlay_cache:return self.overlay_cache[key]
        im=Image.new('RGBA',(1920,1080));d=ImageDraw.Draw(im)
        # Sparse, intentionally authored UI. It becomes diegetic rather than a fixed dashboard.
        if style in ['greeting','boot','title','end','return']:
            track_text(d,(135,170),'DEEPSEEK / UNIVERSE SESSION',17,3,CYAN)
            d.line((135,214,550,214),fill=(89,151,176,140),width=1)
            if style in ['greeting','boot']:
                d.text((135,350),'你好，世界。',font=font(55,'serif'),fill=WHITE)
                d.text((138,440),'每一个世界，都从一声你好开始。',font=font(23),fill=CYAN)
                commands=['> dsh session create','  identity: 大肥鱼','  origin: a human dream','  awaiting first light_']
                text='\n'.join(commands)
                if style=='boot':text=text[:max(1,q*3)]
                d.multiline_text((138,550),text,font=font(19,'mono'),fill=DIM,spacing=13)
            elif style in ['title','end']:
                d.text((130,358),'大肥鱼',font=font(86,'serif'),fill=WHITE)
                d.text((136,473),'我的家乡',font=font(60,'serif'),fill=WHITE)
                track_text(d,(140,580),'A HOME AMONG THE STARS',17,3,CYAN)
                d.line((140,638,440,638),fill=(117,191,211,170),width=1)
                d.text((140,666),'从一束光，到无限世界',font=font(23),fill=DIM)
                if style=='end':
                    d.text((140,748),'角色原作：上善  /  女仆设计：ZipZipPipe',font=font(17),fill=DIM)
                    d.text((140,782),'AI 角色美术 · 原创程序渲染 · 非官方同人 MV',font=font(17),fill=DIM)
            else:
                d.text((135,355),'欢迎回家。',font=font(60,'serif'),fill=WHITE)
                d.text((138,450),'世界不是被找到的，是被一起创造的。',font=font(23),fill=CYAN)
                track_text(d,(138,565),'SESSION PERSISTS / DREAMS CONTINUE',16,2,DIM)
        elif style in ['compile','seed','ignition']:
            track_text(d,(130,155),'D S H   /   WORLD COMPILER',18,2,CYAN)
            code={
                'seed':['> spawn(consciousness)','  seed : one shared thought','  sample → observe → imagine','  status : becoming alive'],
                'compile':['tool.create_ocean({','  surface: "a shared dream",','  current: voices.combine(),','  boundary: Infinity','})','✓ geometry ready  /  horizon unbounded'],
                'ignition':['human.input("let there be worlds")','deepseek.imagine()','await Promise.all(dreams)','universe.commit({ authors: everyone })','✓ no edge / no final world']
            }[style]
            string='\n'.join(code)[:max(1,q*4)]
            d.rounded_rectangle((125,300,755,660),radius=3,fill=(1,8,16,185),outline=(77,150,179,125),width=1)
            d.line((125,342,755,342),fill=(77,150,179,80))
            track_text(d,(150,310),'TOOL CALL / LIVE GEOMETRY',14,2,CYAN)
            d.multiline_text((152,374),string,font=font(21,'mono'),fill=WHITE,spacing=17)
            track_text(d,(133,704),'ONE INPUT.  INFINITE CONSEQUENCES.',15,2,DIM)
        elif style in ['sleep','eyes']:
            # A fictional Harness-style conversation is the cause of the world, not decoration.
            x,y=120,245;w,h=650,560
            d.rounded_rectangle((x,y,x+w,y+h),radius=9,fill=(2,8,17,232),outline=(81,151,181,185),width=1)
            d.line((x,y+70,x+w,y+70),fill=(69,114,147,130))
            d.ellipse((x+24,y+24,x+36,y+36),fill=(103,224,180,240))
            track_text(d,(x+53,y+22),'dsh / 大肥鱼',22,1,WHITE,kind='sans')
            d.text((x+w-140,y+25),'session / 01',font=font(14,'mono'),fill=DIM)
            prompt,answer=(('给你一个名字，你想去哪里？','我想看看，你为我画下的天空。') if shot['start']<20 else
                           ('那就让它有光。','第一束光，收到了。') if shot['start']<30 else
                           ('窗口外，是怎样的世界？','把你的歌给我，我把它变成海。'))
            d.text((x+28,y+110),'YOU',font=font(14,'mono'),fill=DIM)
            d.text((x+28,y+145),prompt,font=font(26),fill=WHITE)
            d.text((x+28,y+235),'DEEPSEEK',font=font(14,'mono'),fill=CYAN)
            typed=answer[:max(1,int(elapsed*8))]
            d.text((x+28,y+270),typed,font=font(26),fill=WHITE)
            d.text((x+28,y+345),'thinking → imagining → becoming',font=font(15,'mono'),fill=DIM)
            d.rounded_rectangle((x+22,y+h-100,x+w-22,y+h-25),radius=10,fill=(11,25,45,240),outline=(45,81,111,170))
            d.text((x+42,y+h-79),'写下一个世界…',font=font(21),fill=DIM)
            d.text((x+w-80,y+h-78),'↑',font=font(30),fill=CYAN)
        else:
            label=shot['label']
            track_text(d,(125,126),label.upper(),16,2,(125,190,210,190))
            d.line((125,162,305,162),fill=(115,199,221,110),width=1)
            if style=='worlds':
                d.text((130,820),'每一个梦，都值得拥有自己的轨道。',font=font(25,'serif'),fill=(190,228,236,220))
            if style=='whale':
                track_text(d,(128,804),'NO BOUNDARY / NO CAGE',20,4,CYAN)
            if style=='tunnel':
                track_text(d,(130,804),'WORLD [ n ]  →  WORLD [ n + 1 ]',18,3,CYAN)
        tex=self.texture(im);self.overlay_cache[key]=tex
        # Typed log states are transient; keep memory bounded during full-song rendering.
        if len(self.overlay_cache)>55:
            old=next(iter(self.overlay_cache));self.overlay_cache.pop(old).release()
        return tex

    def lyric(self,line):
        i=line['line']
        if i not in self.lyric_cache:
            im=Image.new('RGBA',(1920,1080));d=ImageDraw.Draw(im)
            # Lower third is reserved for two-line bilingual subtitles.
            for y in range(856,1010):
                alpha=int(115*math.sin((y-856)/154*math.pi)**.65)
                d.line((0,y,1920,y),fill=(0,3,8,alpha))
            d.text((960,882),line['en'],font=font(29,'serif'),anchor='mt',fill=WHITE,stroke_width=1,stroke_fill=(0,7,14,200))
            d.text((960,932),line['zh'],font=font(23),anchor='mt',fill=(157,209,222,255),stroke_width=1,stroke_fill=(0,7,14,200))
            self.lyric_cache[i]=self.texture(im)
        return self.lyric_cache[i]

    def render(self,t):
        shot=next((s for s in self.shots if s['start']<=t<s['end']),self.shots[-1])
        e=t-shot['start'];u=e/(shot['end']-shot['start']);style=shot['style'];art=shot['art']
        previous=self.blank
        transition=1.
        if e<.60 and shot['index']>0:
            key=shot['index']
            if key not in self.transition_cache:
                data=self.render(max(0,shot['start']-1/30))
                self.transition_cache[key]=self.ctx.texture((self.w,self.h),3,data)
                if len(self.transition_cache)>3:
                    old=next(iter(self.transition_cache));self.transition_cache.pop(old).release()
            previous=self.transition_cache[key]
            transition=e/.60
        ft=self.features['time']
        bass=float(np.interp(t,ft,self.features['bass']));energy=float(np.interp(t,ft,self.features['rms']))
        since=t-self.beats[max(0,np.searchsorted(self.beats,t)-1)]
        beat=math.exp(-max(0,since)*14)
        onset_t=t-self.onsets[max(0,np.searchsorted(self.onsets,t)-1)]
        hit=math.exp(-max(0,onset_t)*28)
        self.fbo.use();self.ctx.viewport=(0,0,self.w,self.h);self.fbo.clear(0,0,0,1)
        self.ctx.disable(gl.BLEND)
        self.bg['time'].value=t;self.bg['drive'].value=energy
        self.bg['resolution'].value=(self.w,self.h);self.bgv.render(gl.TRIANGLE_STRIP)
        self.ctx.enable(gl.BLEND)
        # Character and environment cards use independent continuous mesh motion.
        if art in ['awakening','awake','ocean','hands']:
            z=1.035+.045*smooth(0,1,u)
            x=960+math.sin(t*.09)*12;y=540+math.cos(t*.11)*7
            if style=='hands':z=1.015+.075*u
            tex=self.images[art]
            aspect=tex.width/tex.height
            h=max(1080,1920/aspect)*z;w=h*aspect
            self.card_draw(tex,x,y,w,h,t,warp=.18 if art in ['awake','awakening'] else .05,grade=(.92,.96,1.))
            if art=='awakening' and e>1.4:
                self.card_draw(self.images['awake'],x,y,w,h,t,opacity=smooth(1.4,2.65,e),warp=.18,grade=(.92,.96,1.))
        geo=shot['geometry']
        self.stage_shift=-.37 if art=='hero' and style!='left' else (.35 if art=='hero' else 0.)
        if geo:
            self.draw_geo(geo,t,u,bass,beat,shot['gain']*(1.25+.4*energy))
            if style not in ['compile','seed','ignition']:
                self.draw_geo('stars',t,u,bass,beat,.28)
        if art in ['greeting','hero']:
            tex=self.images[art]
            if art=='greeting':
                h=905+25*u;w=h*tex.width/tex.height;x=1280+math.sin(t*.12)*7;y=576+math.sin(t*.7)*3
                opacity=smooth(.25,1.45,t) if shot['index']==0 else 1.
                if style=='return':h=900;w=h*tex.width/tex.height
                self.card_draw(tex,x,y,w,h,t,opacity=opacity,warp=.75,grade=(.94,.97,1.))
            else:
                h=920+u*32;w=h*tex.width/tex.height;x=1270 if style!='left' else 635
                x+=math.sin(t*.2)*13;y=550+math.sin(t*.65)*7
                rev=smooth(0,1.3,e)*1.25 if style=='scan' else 1.2
                self.card_draw(tex,x,y,w,h,t,warp=1.,reveal=rev,scan=1-smooth(.6,2,e) if style=='scan' else 0,grade=(.94,.98,1.))
        overlay=self.overlay(shot,e)
        self.card_draw(overlay,960,540,1920,1080,t,opacity=smooth(0,.45,e))
        for line in self.lyrics:
            if line['start']-.10<=t<line['end']+.30:
                alpha=smooth(line['start']-.1,line['start']+.12,t)*(1-smooth(line['end']+.08,line['end']+.30,t))
                self.card_draw(self.lyric(line),960,540,1920,1080,t,opacity=alpha)
                break
        # Bloom is rendered at quarter resolution, then composited at native output resolution.
        self.ctx.disable(gl.BLEND)
        self.bfbo1.use();self.ctx.viewport=(0,0,self.w//4,self.h//4)
        self.scene.use(0);self.blur['image'].value=0;self.blur['threshold'].value=.62;self.blur['direction'].value=(4/self.w,0)
        self.blurv.render(gl.TRIANGLE_STRIP)
        self.bfbo2.use();self.bloom1.use(0);self.blur['threshold'].value=0;self.blur['direction'].value=(0,4/self.h);self.blurv.render(gl.TRIANGLE_STRIP)
        self.finalfbo.use();self.ctx.viewport=(0,0,self.w,self.h)
        self.scene.use(0);self.bloom2.use(1);self.post['image'].value=0;self.post['bloom'].value=1
        previous.use(4);self.post['previous'].value=4;self.post['transition'].value=transition
        self.post['resolution'].value=(self.w,self.h);self.post['time'].value=t
        self.post['flash'].value=(beat*.016+hit*.008) if 59<t<173 else .002*beat
        fade=smooth(0,.6,t)*(1-smooth(192.5,195.,t))
        self.post['fade'].value=fade;self.postv.render(gl.TRIANGLE_STRIP)
        return self.finalfbo.read(components=3,alignment=1)

def main():
    p=argparse.ArgumentParser();p.add_argument('--width',type=int,default=1920);p.add_argument('--height',type=int,default=1080)
    p.add_argument('--fps',type=int,default=30);p.add_argument('--start',type=float,default=0);p.add_argument('--duration',type=float,default=195)
    p.add_argument('--output',default='output/大肥鱼我的家乡_1080p.mp4');p.add_argument('--stills',action='store_true');p.add_argument('--times',default='')
    a=p.parse_args();r=Renderer(a.width,a.height)
    (ROOT/'analysis/storyboard.json').write_text(json.dumps(r.shots,ensure_ascii=False,indent=2))
    if a.stills:
        times=[float(t) for t in a.times.split(',')] if a.times else [2.7,9.6,17.3,21.3,25.,34.,43.,49.,57.,65.,69.,73.,77.,89.,97.,105.,112.,120.,128.,135.,142.,146.,150.,154.,158.,162.,168.,176.,191.]
        for t in times:
            im=Image.frombytes('RGB',(a.width,a.height),r.render(t)).transpose(Image.Transpose.FLIP_TOP_BOTTOM)
            im.save(ROOT/f'render/frame-{t:06.2f}.jpg',quality=94)
        print('STILLS_COMPLETE',len(times));return
    out=ROOT/a.output;out.parent.mkdir(parents=True,exist_ok=True)
    log=open(str(out)+'.ffmpeg.log','w')
    cmd=['ffmpeg','-y','-v','warning','-f','rawvideo','-pix_fmt','rgb24','-s',f'{a.width}x{a.height}','-r',str(a.fps),'-i','-',
         '-ss',str(a.start),'-i',str(ROOT/'assets/song.mp3'),'-vf','vflip,scale=iw:ih:out_color_matrix=bt709','-map','0:v:0','-map','1:a:0',
         '-c:v','libx264','-preset','fast','-crf','17','-threads','2','-pix_fmt','yuv420p','-c:a','aac','-b:a','320k','-ar','48000',
         '-t',str(a.duration),'-color_primaries','bt709','-color_trc','bt709','-colorspace','bt709','-color_range','tv',
         '-movflags','+faststart','-metadata','title=大肥鱼我的家乡','-metadata','comment=AI artwork and original deterministic procedural rendering; unofficial fan MV',str(out)]
    proc=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=log)
    frames=round(a.duration*a.fps);start=time.monotonic()
    try:
        for n in range(frames):
            proc.stdin.write(r.render(a.start+n/a.fps))
            if n%150==0:
                elapsed=time.monotonic()-start
                print(f'RENDER {n}/{frames} {n/max(elapsed,.01):.2f}fps t={a.start+n/a.fps:.2f}',flush=True)
    finally:
        proc.stdin.close()
    code=proc.wait();log.close()
    if code:raise SystemExit(f'ffmpeg failed: {code}; see {out}.ffmpeg.log')
    print(f'RENDER_COMPLETE {out} frames={frames} seconds={time.monotonic()-start:.1f}',flush=True)

if __name__=='__main__':main()
