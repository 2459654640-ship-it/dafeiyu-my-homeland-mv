from pathlib import Path
import math,functools,json
import numpy as np,cv2
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1];W,H=1920,1080;BG=(2,3,8);PINK=(255,42,153);CYAN=(42,231,255);GOLD=(255,176,71);WHITE=(241,239,245);LIME=(190,255,69)
cv2.setNumThreads(1)
def clamp(x):return max(0.,min(1.,float(x)))
def smooth(x):x=clamp(x);return x*x*(3-2*x)
def col(c,a):return tuple(int(v*clamp(a)) for v in c)
@functools.lru_cache(128)
def font(n,kind='display'):
 paths={'display':str(R/'assets/Display.ttf'),'cond':str(R/'assets/BarlowCondensed-ExtraBold.ttf'),'en':'/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf','italic':'/usr/share/fonts/truetype/dejavu/DejaVuSans-BoldOblique.ttf','zh':str(R/'assets/NotoSansCJK-Regular.ttc'),'zhbold':str(R/'assets/NotoSansCJK-Bold.ttc')}
 return ImageFont.truetype(paths[kind],int(n),index=2 if kind in ['zh','zhbold'] else 0)
@functools.lru_cache(3000)
def sprite(s,n,kind,c):
 f=font(n,kind);box=f.getbbox(s);a=Image.new('RGBA',(max(1,math.ceil(f.getlength(s))+12),n+30));ImageDraw.Draw(a).text((5,-box[1]+4),s,font=f,fill=(*c,255));return a
def text(im,xy,s,n=30,c=WHITE,kind='display',alpha=1):
 a=sprite(str(s),int(n),kind,tuple(c))
 if alpha<.999:a=a.copy();a.putalpha(a.getchannel('A').point(lambda z:int(z*clamp(alpha))))
 im.alpha_composite(a,(int(xy[0]),int(xy[1])))
def center(im,y,s,n,c=WHITE,kind='display',alpha=1):text(im,((W-font(n,kind).getlength(s))/2,y),s,n,c,kind,alpha)
def rotation(p,yaw=0,pitch=0,roll=0):
 p=np.asarray(p,dtype='f4');cy,sy=math.cos(yaw),math.sin(yaw);cp,sp=math.cos(pitch),math.sin(pitch);cr,sr=math.cos(roll),math.sin(roll)
 mat=np.array([[cy,0,-sy],[0,1,0],[sy,0,cy]],dtype='f4')@np.array([[1,0,0],[0,cp,-sp],[0,sp,cp]],dtype='f4')@np.array([[cr,-sr,0],[sr,cr,0],[0,0,1]],dtype='f4')
 return p@mat
class Graphics:
 def __init__(self):
  self.rng=np.random.default_rng(6418);self.seeds=self.rng.random((800,7));self.buildings=self.rng.random((72,5));self.u=np.linspace(0,1,52);self.cache={};self.media={}
  schedule=R/'analysis/shot-sources.json';self.schedule=json.loads(schedule.read_text()) if schedule.exists() else {}
  if not self.schedule:
   for m in json.loads((R/'analysis/footage.json').read_text()):self.media[m['name'].replace('official-','')]=np.load(R/f"analysis/{m['name']}.npy",mmap_mode='r')
 def scene(self,name,t,w=1920,h=1080,slot=0):
  entry=self.schedule.get(str(self.shot['index']),[])
  if entry:
   item=entry[min(slot,len(entry)-1)];key=item['name']
   if key not in self.media:self.media[key]=np.load(R/f'analysis/{key}.npy',mmap_mode='r')
   a=self.media[key];phase=clamp((t-self.shot['start'])/(self.shot['end']-self.shot['start']));i=min(len(a)-1,int(phase*len(a)));frame=np.asarray(a[i])
  else:
   a=self.media[name];i=min(len(a)-1,int(max(0,t-self.shot['start'])*24));frame=np.asarray(a[i])
  # Cinematic crop traverses a single coherent view, not separate body-part cameras.
  hh,ww=frame.shape[:2];cw=min(ww,int(hh*w/h));ch=min(hh,int(ww*h/w));x=int((ww-cw)*(.5+.35*math.sin(t*.15)));y=int((hh-ch)*(.5+.2*math.cos(t*.13)))
  return cv2.resize(frame[y:y+ch,x:x+cw],(w,h),interpolation=cv2.INTER_LINEAR)
 @functools.lru_cache(40)
 def matte(self,name,w,h):
  if name=='portal':a=Image.open(R/'assets/unified-mask.png').convert('L');a=a.crop(a.getbbox())
  else:a=Image.open(R/f'assets/{name}.png').getchannel('A');a=a.crop(a.getbbox())
  scale=min(w/a.width,h/a.height);a=a.resize((round(a.width*scale),round(a.height*scale)),Image.Resampling.LANCZOS)
  arr=np.asarray(a).copy();edge=cv2.morphologyEx(arr,cv2.MORPH_GRADIENT,np.ones((5,5),np.uint8));return arr,edge
 @functools.lru_cache(72)
 def colored(self,name,w,h,c,c2,style):
  a,edge=self.matte(name,w,h);hh,ww=a.shape;u=np.linspace(0,1,hh,dtype='f4')[:,None,None]
  grad=np.broadcast_to(np.array(c,dtype='f4')[None,None,:]*(1-u)+np.array(c2,dtype='f4')[None,None,:]*u,(hh,ww,3)).copy()
  if style in ['ink','art']:
   src=Image.open(R/f'assets/{name}.png').convert('RGBA');src=src.crop(src.getchannel('A').getbbox()).resize((ww,hh),Image.Resampling.LANCZOS);rgb=np.array(src)[:,:,:3].copy()
   if style=='ink':rgb=(grad*np.clip((cv2.cvtColor(rgb,cv2.COLOR_RGB2GRAY)/255.-.1)*1.4,0,1)[:,:,None]).astype('u1')
  else:rgb=(grad*(.025 if style=='outline' else .65)).astype('u1')
  edges=(grad*(edge/255.)[:,:,None]*.8).astype('u1');return a,grad,edges,cv2.add(rgb,edges)
 def mask(self,im,t,name='portal',clip='vice-city',cx=1150,cy=480,w=1000,h=930,c=PINK,c2=CYAN,style='video',opacity=1,roll=0):
  a,grad,edges,base=self.colored(name,w,h,tuple(c),tuple(c2),style);hh,ww=a.shape;x=int(cx-ww/2);y=int(cy-hh/2)
  if style in ['video','opening-transform','lead-transform']:
   frame=self.scene(clip,t,ww,hh);lum=cv2.cvtColor(frame,cv2.COLOR_RGB2GRAY).astype('f4')/255;rgb=np.clip(frame.astype('f4')*.36+grad*(.12+lum[:,:,None]*.66),0,255).astype('u1');rgb=cv2.add(rgb,edges)
   if style in ['opening-transform','lead-transform']:
    art=self.colored(name,w,h,tuple(c),tuple(c2),'art')[3];phase=smooth((t-(1.65 if style=='opening-transform' else self.shot['start']+1.35))/1.35);yy=np.arange(hh,dtype='f4')[:,None,None];scan=phase*(hh+120)-60
    blend=np.clip((scan-yy+35)/70,0,1);rgb=(art*(1-blend)+rgb*blend).astype('u1')
    if 0<phase<1:
     beam=np.exp(-((yy-scan)/13)**2);rgb=np.clip(rgb.astype('f4')+beam*np.array(CYAN,dtype='f4')*.85,0,255).astype('u1')
  else:rgb=base
  rgba=np.empty((hh,ww,4),dtype='u1');rgba[:,:,:3]=rgb;rgba[:,:,3]=a if opacity>=.999 else (a*opacity).astype('u1');layer=Image.fromarray(rgba)
  if roll:
   layer=layer.rotate(roll,Image.Resampling.BICUBIC,expand=True);x=round(cx-layer.width/2);y=round(cy-layer.height/2)
  im.alpha_composite(layer,(x,y))
 @functools.lru_cache(8)
 def logo_sprite(self,height):
  a=Image.open(R/'assets/official-gta-vi-logo.png').convert('RGBA');return a.resize((round(a.width*height/a.height),height),Image.Resampling.LANCZOS)
 def official_logo(self,im,t,cx,cy,height,opacity=1):
  a=self.logo_sprite(height).copy();a.putalpha(a.getchannel('A').point(lambda v:round(v*clamp(opacity))));im.alpha_composite(a,(round(cx-a.width/2),round(cy-a.height/2)))
 def stars(self,im,t,c,drive=.6):
  d=ImageDraw.Draw(im)
  for i,r in enumerate(self.seeds[:int(70+150*drive)]):
   x=(r[0]*2100-t*(10+drive*60)/(r[2]+.3))%2100-90;y=r[1]*900;ll=2+drive*r[3]*16
   d.line((x,y,x+ll,y),fill=col(c,(.12+r[4]*.4)*drive),width=1)
 def project(self,p,t,yaw=0,pitch=0,roll=0,focal=1080,center=(960,480)):
  p=rotation(p,yaw,pitch,roll);z=5.5-p[:,2];scale=focal/np.maximum(.3,z);return np.stack((center[0]+p[:,0]*scale,center[1]-p[:,1]*scale,z),axis=1)
 def lines(self,d,q,c,width=1):
  pts=[]
  for x,y,z in q:
   if z>.35 and -3000<x<4900 and -2200<y<3300:pts.append((x,y))
   else:
    if len(pts)>1:d.line(pts,fill=c,width=width)
    pts=[]
  if len(pts)>1:d.line(pts,fill=c,width=width)
 def road(self,im,t,c,c2,drive=1,water=False):
  d=ImageDraw.Draw(im);pitch=.23+math.sin(t*.11)*.035;steer=math.sin(t*.115)*.65
  zs=np.linspace(-30,4.8,75)
  for j in range(-6,7):
   p=np.c_[j*.72+np.sin(zs*.16+t*.23)*steer,np.full(len(zs),-1.4),zs]
   if water:p[:,1]+=np.sin(zs*1.8+t*2+j*.5)*.07
   self.lines(d,self.project(p,t,pitch=pitch),col(c,.25 if j%3 else .8),3 if j%3==0 else 2)
  for i in range(42):
   z=4.8-((i*.85-t*(3.3+drive))%35)
   xs=np.linspace(-5,5,35);p=np.c_[xs+math.sin(z*.16+t*.23)*steer,np.full(len(xs),-1.4),np.full(len(xs),z)]
   if water:p[:,1]+=np.sin(xs*2+z*1.8+t*2)*.07
   self.lines(d,self.project(p,t,pitch=pitch),col(c2,.13+((z+30)/35)*.25))
  if water:return
  # Moving headlights and compact 3D vehicle bodies follow the road's own perspective.
  for i,r in enumerate(self.seeds[:24]):
   z=4.0-((r[0]*33-t*(1.5+r[2]*1.8))%33);x=(int(r[1]*5)-2)*1.05+math.sin(z*.16+t*.23)*steer
   p=np.array([[x-.24,-1.32,z],[x+.24,-1.32,z],[x+.24,-1.12,z],[x-.24,-1.12,z],[x-.18,-.98,z-.35],[x+.18,-.98,z-.35]])
   q=self.project(p,t,pitch=pitch)
   if q[:,2].min()<.45:continue
   d.polygon([tuple(q[j,:2]) for j in [0,1,2,5,4,3]],fill=(3,7,15),outline=col(c,.75),width=1)
   for a,b in [(0,1),(3,2),(3,4),(2,5),(4,5)]:self.lines(d,q[[a,b]],col(c2,.7),2)
   for j in [0,1]:
    x1,y1,z1=q[j];d.line((x1,y1,x1,y1+min(100,60/z1)),fill=col(WHITE,.8),width=2)
 def skyline(self,im,t,c,c2,drive=1):
  d=ImageDraw.Draw(im);yaw=math.sin(t*.07)*.16
  for i,r in enumerate(self.buildings):
   z=-17+((i//12)*3.0+t*.65)%19;x=(i%12-5.5)*1.0;h=.45+r[0]*3.0;w=.28+r[1]*.3;bottom=-1.0
   p=np.array([[x-w,bottom,z],[x+w,bottom,z],[x+w,bottom+h,z],[x-w,bottom+h,z],[x-w,bottom,z-.5],[x+w,bottom,z-.5],[x+w,bottom+h,z-.5],[x-w,bottom+h,z-.5]])
   q=self.project(p,t,yaw=yaw,center=(960,520))
   if q[:,2].min()<.5:continue
   d.polygon([tuple(q[k,:2]) for k in [0,1,2,3]],fill=(9,8,24),outline=col(c,.6+.3*r[2]))
   for a,b in [(2,6),(3,7),(6,7)]:self.lines(d,q[[a,b]],col(c2,.38))
   rows=[bottom+.15+j*.22 for j in range(int(h*4)) if (j+i+int(t*1.1))%4]
   if rows:
    windows=np.array([[[x-w*.65,y,z+.01],[x+w*.65,y,z+.01]] for y in rows]);qq=self.project(windows.reshape(-1,3),t,yaw=yaw,center=(960,520)).reshape(-1,2,3)
    for qwindow in qq:self.lines(d,qwindow,col(c2,.35+r[3]*.6),3)
 def palm(self,im,x,y,size,t,c,side=1):
  d=ImageDraw.Draw(im);u=self.u;trunk=[(x+side*math.sin(v*1.3)*size*.12,y-v*size) for v in u];d.line(trunk,fill=col(c,.6),width=max(2,int(size*.013)));hx,hy=trunk[-1]
  for j in range(9):
   a=-math.pi+j*math.pi/8+math.sin(t*.6+j)*.08;ln=size*(.35+.12*math.sin(j*2.1));pts=[]
   for v in u:
    xx=hx+math.cos(a)*ln*v;yy=hy+math.sin(a)*ln*v+v*v*size*.27;pts.append((xx,yy))
   d.line(pts,fill=col(c,.6),width=max(1,int(size*.009)))
   for k in range(3,43,4):
    px,py=pts[k];z=k/52;d.line((px,py,px+side*ln*.12*(1-z),py+size*.06),fill=col(c,.45),width=2)
 def palms(self,im,t,c,drive=1):
  for side in [-1,1]:
   for j in range(5):
    z=(j/5+t*.055)%1;s=60+z*z*590;x=960+side*(200+z*z*1000);y=440+z*z*600;self.palm(im,x,y,s,t+j,c,side)
 def rings(self,im,t,c,hit=0):
  d=ImageDraw.Draw(im);a=np.linspace(0,math.tau,220)
  for j in range(12):
   rad=1.2+(j*.27+t*.4)%3.4;p=np.c_[np.cos(a)*rad,np.sin(a)*rad*.7,np.full(len(a),j*.13)]
   q=self.project(p,t,yaw=math.sin(t*.16)*.35,pitch=.2,roll=t*.02)
   self.lines(d,q,col(c,.12+.25*j/12),2 if j%4==0 else 1)
 def ribbons(self,im,t,c,c2,hit=0):
  d=ImageDraw.Draw(im);u=np.linspace(-3,3,150)
  for i in range(6):
   p=np.c_[u*2.0,np.sin(u*1.4+t*.65+i*.7)*(.6+i*.12),np.cos(u*.65+t*.27+i*.4)*1.5+i*.22]
   q=self.project(p,t,yaw=math.sin(t*.08)*.35,roll=math.sin(t*.18)*.22,center=(960,470))
   self.lines(d,q,col(c if i%2 else c2,.35+.18*hit),2+i%2)
   for k in range(5):
    j=int((t*(24+i*2)+k*29+i*13)%145);self.lines(d,q[j:j+4],WHITE if k%2 else c,4)
 def tunnel(self,im,t,c,c2,hit=0):
  d=ImageDraw.Draw(im)
  for j in range(22):
   phase=(j/22+t*.18)%1;rad=.3+phase**2*12
   pts=np.array([[-rad*.72,rad,0],[rad*.72,rad,0],[rad*.18,-rad,0],[-rad*.18,-rad,0],[-rad*.72,rad,0]])
   q=self.project(pts,t,roll=math.sin(t*.2)*.3,center=(960,450))
   self.lines(d,q,col(c if j%3 else c2,(1-phase)*(.25+hit*.5)),2 if j%3 else 5)
 def aperture(self,im,t,c,c2,slot=0):
  frame=self.scene('vice-city',t,1600,900,slot);f=frame.astype('f4');gray=cv2.cvtColor(frame,cv2.COLOR_RGB2GRAY).astype('f4')/255
  # A moving cinematic gate, distinct from the whole-person mattes.
  grad=np.linspace(0,1,900,dtype='f4')[:,None,None];g=np.array(c,dtype='f4')*(1-grad)+np.array(c2,dtype='f4')*grad
  rgb=np.clip(f*.65+g*(gray[:,:,None]*.28),0,255).astype('u1');age=t-self.shot['start'];yaw=.1*math.sin(age*.55);roll=.055*math.sin(age*.4)
  pts=rotation([[-4.2,2.35,.2],[4.2,2.35,.2],[4.2,-2.35,.2],[-4.2,-2.35,.2]],yaw=yaw,roll=roll)
  q=self.project(pts,t,focal=1000,center=(960,470))[:,:2]
  mat=cv2.getPerspectiveTransform(np.array([[0,0],[1600,0],[1600,900],[0,900]],dtype='f4'),q.astype('f4'))
  src=np.dstack([rgb,np.full((900,1600),255,dtype='u1')]);a=cv2.warpPerspective(src,mat,(W,H));im.alpha_composite(Image.fromarray(a));ImageDraw.Draw(im).line([tuple(p) for p in np.vstack([q,q[0]])],fill=c,width=3)
 def burst(self,im,age,c,c2,power=1):
  if not 0<=age<1.4:return
  d=ImageDraw.Draw(im);q=age/1.4
  for i,r in enumerate(self.seeds[:190]):
   a=r[0]*math.tau;dist=age*(400+1500*r[1])*power;x=960+math.cos(a)*dist;y=470+math.sin(a)*dist*.6
   ll=10+q*80;d.line((x-math.cos(a)*ll,y-math.sin(a)*ll*.6,x,y),fill=col(c if i%3 else c2,1-q),width=2 if i%8 else 4)
 def typography(self,im,word,t,c,x=70,y=180,size=230,outline=False):
  f=font(size,'display');a=Image.new('RGBA',(int(f.getlength(word))+25,size+40));d=ImageDraw.Draw(a)
  d.text((7,-f.getbbox(word)[1]+4),word,font=f,fill=(0,0,0,0) if outline else (*c,255),stroke_width=2 if outline else 0,stroke_fill=(*c,255))
  im.alpha_composite(a,(int(x),int(y)))
 def shutters(self,im,t,c,hit):
  if hit<.35:return
  d=ImageDraw.Draw(im)
  for i in range(6):
   x=(i*375+t*80)%2300-190;d.polygon([(x,-50),(x+6+hit*10,-50),(x-330,930),(x-336-hit*10,930)],fill=col(c,hit*.28))
 def grade(self,im,t,kick,snare,glow=True):
  a=np.asarray(im.convert('RGB'));scale=1+kick*.022+snare*.01;dx=math.sin(t*14)*snare*4;dy=kick*6
  m=np.array([[1/scale,0,W/2-W/2/scale+dx],[0,1/scale,H/2-H/2/scale+dy]],dtype='f4');a=cv2.warpAffine(a,m,(W,H),flags=cv2.INTER_LINEAR|cv2.WARP_INVERSE_MAP,borderValue=BG)
  if glow:
   sm=cv2.resize(a,(480,270));sm=cv2.GaussianBlur(sm,(0,0),1.7);sm=cv2.resize(sm,(W,H));a=cv2.addWeighted(a,1,sm,.19,0)
  return Image.fromarray(a).convert('RGBA')
