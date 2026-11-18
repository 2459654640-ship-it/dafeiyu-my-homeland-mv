import math,json,bisect,functools
import numpy as np,cv2
from PIL import Image,ImageDraw
from visuals import *
class Film:
 def __init__(self):
  self.g=Graphics();self.lyrics=json.loads((R/'analysis/lyrics.json').read_text());self.hits=json.loads((R/'analysis/hits.json').read_text());self.tracks={k:np.array([x['t'] for x in v]) for k,v in self.hits.items()};self.strength={k:np.array([x['s'] for x in v]) for k,v in self.hits.items()};self.plan=[]
  starts=[(0,'title'),(7.4,'portal'),(14.8,'road'),(22.3,'palms'),(29.7,'hotel')]
  v1=['drive','city','hotel','radio','bay','traffic','keys','palms'];ch=['chorus','cityburst','fastcar','anything','chorus','heat','corner','free'];v2=['smile','subscription','billboards','blackout','gates','price','scandal','fact'];bridge=['shore','dreamers','names','sunrise']
  for l in self.lyrics:
   i=l['index'];sec=l['section']
   if sec=='verse1':mode=v1[i]
   elif sec=='chorus1':mode=ch[i-8]
   elif sec=='verse2':mode=v2[i-16]
   elif sec=='chorus2':mode=ch[i-24]
   elif sec=='chorus2_extra':mode=ch[i-24]
   elif sec=='bridge':mode=bridge[i-32]
   else:mode=ch[min(7,i-36)]
   starts.append((l['start'],mode))
  starts += [(64.9,'build'),(100.2,'reels'),(107.6,'duet'),(113,'road'),(206.5,'silence'),(213,'ignition'),(219,'launch'),(259,'home'),(264,'credits')]
  # Instrumental edits land on detected drum transients, then alternate geometry and unique cinema gates.
  for a,b in [(15,29),(100.5,107),(113,117),(214,222.5)]:
   for j,target in enumerate(np.arange(a,b,2.25)):
    hh=self.tracks['kick'];near=hh[(hh>=target-.18)&(hh<=target+.18)];beat=float(near[np.argmin(abs(near-target))]) if len(near) else float(target)
    if min(abs(beat-x[0]) for x in starts)>.85:starts.append((round(beat,4),'rush' if j%2==0 else 'tunnel'))
  starts.sort()
  for i,(a,m) in enumerate(starts):self.plan.append(dict(start=a,end=starts[i+1][0] if i+1<len(starts) else 269.84,mode=m,index=i))
  self.cache={};self.seeds=np.random.default_rng(617).random((380,7))
 def pulse(self,k,t,decay=15):
  a=self.tracks[k];i=np.searchsorted(a,t,side='right')-1
  if i<0:return 0.,0
  return float(min(1,self.strength[k][i]/1.8)*math.exp(-(t-a[i])*decay)),int(i)
 def subtitle(self,im,t):
  line=next((l for l in self.lyrics if l['start']<=t<l['end']+.28),None)
  if not line:return
  d=ImageDraw.Draw(im);d.rectangle((0,942,W,H),fill=(2,3,8,248))
  words=line['words'];size=53;total=sum(font(size,'cond').getlength(w['word']) for w in words)+12*(len(words)-1)
  if total>1740:size=int(size*1740/total);total=sum(font(size,'cond').getlength(w['word']) for w in words)+12*(len(words)-1)
  x=(W-total)/2
  for w in words:
   hot=w['start']<=t<=w['end'];text(im,(x,952),w['word'],size,PINK if hot else WHITE,'cond');x+=font(size,'cond').getlength(w['word'])+12
  n=40
  while font(n,'zh').getlength(line['zh'])>1740:n-=1
  center(im,1017,line['zh'],n,(212,222,234),'zh')
 def label(self,im,upper,lower,t,c,xy=(80,180),big=205):
  age=t-self.current_shot['start'];xx=xy[0]-(1-smooth(age/.45))*140
  self.g.typography(im,upper,t,WHITE,xx,xy[1],big)
  text(im,(xy[0]+8,xy[1]+big+24),lower,34,c,'cond')
 def role(self,im,t,name,c,c2,cx=1370,style='ink',alpha=.82):
  if name in ['jason','lucia']:name=[name,name+'-walk',name+('-lean' if name=='jason' else '-turn')][self.current_shot['index']%3]
  self.g.mask(im,t,name,'vice-city',cx+math.sin(t*.5)*22,490+math.sin(t*.7)*8,850,920,c,c2,style,alpha)
 def poster(self,im,t,clip,c,c2,name='portal',cx=1180,w=1070,style='video'):
  if name=='portal' and self.current_shot['mode']!='title':name=['jason','lucia-walk','jason-lean','lucia-turn'][self.current_shot['index']%4]
  self.g.mask(im,t,name,clip,cx,480,w,930,c,c2,style,.95)
 def billboard(self,im,t,title,subtitle,c,price=False):
  card=Image.new('RGBA',(1500,600),(6,7,18,250));d=ImageDraw.Draw(card)
  d.rectangle((3,3,1496,596),outline=c,width=4)
  self.g.typography(card,title,t,c,75,80,185)
  text(card,(90,310),subtitle,44,WHITE,'cond')
  if price:text(card,(90,415),'$ 9.99 / MONTH',80,c,'display')
  else:
   for i in range(27):
    x=90+i*45;d.rectangle((x,440,x+18+(i%3)*4,525),fill=col(c,.23+(i%4)*.16))
  yaw=math.sin(t*.22)*.28;roll=math.sin(t*.13)*.04
  pts=rotation([[-3.8,1.5,.4],[3.8,1.5,.4],[3.8,-1.5,.4],[-3.8,-1.5,.4]],yaw=yaw,roll=roll)
  q=self.g.project(pts,t,focal=1200,center=(920,470))[:,:2]
  src=np.array([[0,0],[1500,0],[1500,600],[0,600]],dtype='f4');mat=cv2.getPerspectiveTransform(src,q.astype('f4'))
  warped=cv2.warpPerspective(np.asarray(card),mat,(W,H),flags=cv2.INTER_LINEAR);im.alpha_composite(Image.fromarray(warped))
  d=ImageDraw.Draw(im)
  for j in range(7):
   x=(t*150+j*340)%2300-170;y=815+math.sin(t*.6+j)*65
   d.line((x,y,x+220,y-30),fill=col(c,.35),width=2)
   text(im,(x,y-38),['BUY','SELL','LIVE','REPEAT'][j%4],33,col(c,.6),'cond')
 def filmstrip(self,im,t,e,c):
  # Individual apertures traverse a diagonal film path. Only the designated source sequence appears per shot.
  for i in range(4):
   x=int(-440+((t*145+i*525)%2500));y=int(140+i*140+math.sin(t*.6+i)*35)
   a=Image.fromarray(self.g.scene('vice-city',t,590,340,slot=i)).convert('RGBA')
   a=a.rotate(-13+i*6,Image.Resampling.BICUBIC,expand=True)
   im.alpha_composite(a,(x,y));ImageDraw.Draw(im).line((x,y+30,x+a.width,y),fill=c,width=2)
 def render(self,t,shot=None,with_subtitles=True):
  s=shot or next((a for a in self.plan if a['start']<=t<a['end']),self.plan[-1]);m=s['mode'];e=t-s['start'];self.g.shot=s;self.current_shot=s
  kick,bi=self.pulse('kick',t);snare,_=self.pulse('snare',t);hat,_=self.pulse('hat',t,26);bass,_=self.pulse('bass',t,8)
  verse2=117.7<=t<150.52;final=222.9<=t<259;quiet=179.9<=t<219
  c,c2=(LIME,PINK) if verse2 else (GOLD,PINK) if final else (CYAN,(143,81,255)) if quiet else (PINK,CYAN)
  im=Image.new('RGBA',(W,H),(*BG,255));self.g.stars(im,t,c,.3 if quiet else .65)
  if m in ['rush','tunnel']:
   self.g.tunnel(im,t,c,c2,kick)
   if m=='rush':self.g.aperture(im,t,c,c2);self.g.typography(im,'VICE CITY',t,WHITE,65,650,210,outline=True)
   else:self.g.ribbons(im,t,c,c2,kick);center(im,330,'VI',340,WHITE);text(im,(90,105),'AFTER DARK / NO LIMITS',45,c2,'cond')
  elif m=='title':
   self.g.skyline(im,t*.5,c,c2);self.g.mask(im,t,'opening-poster','vice-city',1300,480,1070,930,c,c2,'opening-transform',smooth(t/.45));q=smooth((e-.5)/1.5)
   text(im,(92,145),'VICE CITY',245,WHITE,'display',q);text(im,(102,410),'MY HOME',147,c,'display',q);text(im,(108,594),'罪城，我的家乡',43,WHITE,'zh',q)
   text(im,(109,735),'OCEAN DRIVE  /  AFTER DARK',30,c2,'cond',q)
   self.g.burst(im,t-2.9,c,c2,.8)
  elif m=='portal':
   self.g.tunnel(im,t,c,c2,kick);self.g.ribbons(im,t,c,c2,kick)
   self.g.mask(im,t,'jason','vice-city',505,475,850,850,c,c2,'lead-transform',.98)
   self.g.mask(im,t,'lucia','vice-city',1430,475,850,850,c2,c,'lead-transform',.98)
   center(im,53,'TWO SOULS / ONE CITY',77,WHITE);center(im,833,'JASON  ×  LUCIA',64,c)
  elif m in ['drive','city','chorus','cityburst','anything','corner','home']:
   self.g.skyline(im,t,c,c2);self.g.rings(im,t,c,kick)
   clip='vice-city' if m not in ['home','corner'] else 'port-gellhorn'
   name='portal' if m in ['portal','drive','city','cityburst','anything'] else ('jason-walk' if s['index']%2==0 else 'lucia-turn')
   self.poster(im,t,clip,c,c2,name,cx=1130+math.sin(t*.18)*190)
   if m in ['chorus','home']:
    self.g.typography(im,'VICE',t,WHITE,55,135,260,outline=True);self.g.typography(im,'CITY',t,c,65,410,260)
    text(im,(78,722),'MY HOME',65,c2,'display');self.g.burst(im,e,c,c2,1.1)
   elif m=='anything':self.label(im,'ANYTHING','CAN HAPPEN IN THIS TOWN',t,c,xy=(60,210),big=185)
   elif m=='corner':self.label(im,'OUR SONG','EVERY STREET CORNER',t,c,xy=(60,200),big=175)
   elif m=='cityburst':self.g.burst(im,e,c,c2,1.2);self.label(im,'ALIVE','THE STREETS COME ALIVE',t,c,xy=(70,270),big=180)
   elif m=='drive':self.label(im,'OCEAN','DRIVE / SUNSET ARRIVAL',t,c,xy=(50,210),big=180)
   else:text(im,(70,100),'VICE CITY / MY HOME',43,WHITE,'display')
  elif m in ['road','traffic','keys','fastcar','free']:
   self.g.skyline(im,t*.8,c,c2);self.g.road(im,t,c,c2,1.8 if final else 1);self.g.palms(im,t,c2,.8)
   if m=='free':
    self.g.typography(im,'WILD & FREE',t,WHITE,-80+math.sin(t*.3)*80,170,235,outline=True)
    self.role(im,t,'lucia' if s['index']%2 else 'jason',c,c2,cx=1440,style='ink',alpha=.8)
   elif m=='keys':self.label(im,'THE KEYS','HEADLIGHTS / NO FINAL EDGE',t,c,xy=(70,150),big=180)
   elif m=='fastcar':self.label(im,'WINDOWS DOWN','FAST CARS / NIGHT DRIVE',t,c,xy=(75,135),big=155);self.g.burst(im,e,c,c2,.8)
  elif m in ['palms','hotel','heat','bay','radio','duet','reels','build']:
   if m in ['palms','heat']:self.g.palms(im,t,c);self.g.road(im,t,c2,c,.65,water=True)
   elif m=='bay':self.g.road(im,t,c,c2,.6,water=True);self.poster(im,t,'leonida-keys',c,c2,cx=1130)
   elif m=='radio':
    self.g.rings(im,t,c,kick);self.poster(im,t,'vice-city',c,c2,'portal',cx=1350,style='outline');self.label(im,'FM 99.1','THE RADIO / THROUGH THE NIGHT',t,c,xy=(60,230),big=190)
    for i in range(45):
     x=80+i*32;y=640+(i%5)*8;ImageDraw.Draw(im).line((x,y,x,y+32),fill=col(c2,.6),width=2)
   elif m=='duet':
    self.g.rings(im,t,c,kick);self.role(im,t,'jason',c,c2,cx=535,style='ink');self.role(im,t,'lucia',c2,c,cx=1430,style='ink');center(im,105,'SAME CITY. SAME SKY.',95,WHITE)
   elif m=='reels':self.filmstrip(im,t,e,c);self.g.typography(im,'VICE CITY',t,WHITE,80,580,180,outline=True)
   elif m=='build':self.g.road(im,t,c,c2,2);self.g.rings(im,t,c2,kick);self.poster(im,t,'vice-city',c,c2,cx=1310,style='outline')
   else:self.g.skyline(im,t,c,c2);self.g.palms(im,t,c);self.billboard(im,t,'PINK HOTELS','NEON NIGHTS / OCEAN DRIVE',c)
   if m=='heat':self.label(im,'SUMMER HEAT','LONG NIGHTS / OPEN ROADS',t,c,xy=(65,145),big=205)
   if m in ['bay','palms','duet']:self.g.ribbons(im,t,c,c2,kick)
  elif verse2:
   self.g.skyline(im,t,c,c2);self.g.shutters(im,t,c2,max(.2,snare));self.poster(im,t,'ambrosia',c,c2,cx=1480,style='outline')
   words={'smile':('PERFECT','SMILES / EVERY SCREEN'),'subscription':('SUNSHINE','YOUR PERFECT LIFE, BILLED MONTHLY'),'billboards':('BUY MORE','THE STREETS ARE STILL HUNGRY'),'blackout':('SOMEBODY WINS','WHEN THE LIGHTS GO OUT'),'gates':('GOLDEN GATES','GRAY STREETS'),'price':('TOMORROW','BELONGS TO WHOEVER PAYS'),'scandal':('SCANDAL','TODAY / TOMORROW: ADVERTISEMENT'),'fact':('SOLD AS FACT','THE WHOLE TOWN BUYS IT')}
   a,b=words.get(m,('PERFECT LIFE','VICE CITY'));self.billboard(im,t,a,b,c,price=m in ['subscription','price'])
   if m=='blackout':
    a=Image.new('RGBA',(W,H),(0,0,0,int(150*(.5+.5*math.sin(e*3)))));im.alpha_composite(a)
  elif m in ['shore','dreamers','names','sunrise','silence','ignition','launch']:
   self.g.road(im,t*.55,c,c2,.5,water=True)
   self.poster(im,t,'grassrivers',c,c2,cx=1370,style='outline')
   if m=='shore':self.label(im,'LIGHTS OUT','ALONG THE SHORE',t,c,xy=(80,240),big=190)
   elif m=='dreamers':self.role(im,t,'lucia',c,c2,cx=1250,style='outline');self.label(im,'DREAMERS','WANTING SOMETHING MORE',t,c,xy=(70,190),big=180)
   elif m=='names':self.label(im,'LET THE OCEAN','TAKE THE NAMES',t,c,xy=(65,185),big=165)
   elif m=='sunrise':self.g.skyline(im,t,GOLD,PINK);self.label(im,'MORNING','TURN THE SKYLINE INTO FLAMES',t,GOLD,xy=(70,180),big=220)
   elif m=='silence':
    black=Image.new('RGBA',(W,H),(0,0,0,165));im.alpha_composite(black);center(im,440,'MY HOME',100,CYAN);center(im,564,'当霓虹熄灭，仍有人渴望黎明。',33,WHITE,'zh')
   elif m=='ignition':
    self.g.rings(im,t,c,kick);self.poster(im,t,'vice-city',c,c2,cx=960,style='outline');center(im,420,'ONE MORE NIGHT',120,WHITE)
   else:
    self.g.road(im,t*1.4,PINK,GOLD,3);self.g.rings(im,t,PINK,kick);center(im,175,'VICE CITY',225,WHITE);self.g.burst(im,e,PINK,GOLD,1.5)
  else:
   self.poster(im,t,'vice-city',PINK,CYAN,'portal',cx=1380,style='outline');self.label(im,'VICE CITY','MY HOME',t,PINK,xy=(80,210),big=235)
   text(im,(93,615),'罪城，我的家乡',43,WHITE,'zh');text(im,(96,717),'歌曲与歌词：用户提供',26,WHITE,'zh');text(im,(96,762),'GTA VI 官方场景素材：Rockstar Games',26,WHITE,'zh');text(im,(96,807),'视觉：程序动画 · AI 辅助角色剪影',26,WHITE,'zh')
  self.g.shutters(im,t,c,snare if not quiet else 0)
  if final:self.g.burst(im,e,c,c2,1.3)
  # Soft optical blending at every planned cut; the incoming geometry continues moving.
  im=self.g.grade(im,t,kick,snare,True)
  if with_subtitles:self.subtitle(im,t)
  if t>266.8:
   a=np.asarray(im).copy();a[:,:,:3]=(a[:,:,:3]*(1-smooth((t-266.8)/3.04))).astype('u1');im=Image.fromarray(a)
  return im.convert('RGB')
