"""Geometry that grows out of terminal commands and continues beyond the viewport."""
import math,functools
import numpy as np
import cv2
from PIL import Image,ImageDraw,ImageFilter
from ui import W,H,BG,BLUE,ICE,TEXT,color,text,font,smooth,ease,clamp
from fields import rotate


class Spectacle:
    def __init__(self):
        self.seed=np.random.default_rng(120125).random((800,7))
        self.u=np.linspace(0,math.tau,340)

    def project(self,p,t=0,roll=0,yaw=0,pitch=0,focal=940):
        p=rotate(np.asarray(p,float),yaw,pitch,roll)
        z=4.6-p[:,2]
        return np.c_[960+p[:,0]*focal/np.maximum(.3,z),500-p[:,1]*focal/np.maximum(.3,z),z]

    def line(self,d,q,ink=BLUE,width=1):
        # Break polylines at the camera plane, avoiding screen-spanning near-plane artifacts.
        run=[]
        for x,y,z in q:
            if z>.38 and -3200<x<5120 and -2400<y<3400:run.append((x,y))
            else:
                if len(run)>1:d.line(run,fill=ink,width=width)
                run=[]
        if len(run)>1:d.line(run,fill=ink,width=width)

    def corridor(self,im,t,hit,kind='gate'):
        d=ImageDraw.Draw(im)
        spin=.12*math.sin(t*.31)+(t*.075 if kind=='launch' else 0)
        yaw=math.sin(t*.21)*.17;pitch=math.sin(t*.17)*.13
        for i in range(23):
            z=3.9-((i*.9+t*(2.4 if kind=='launch' else .85))%20)
            a=(i*.11+t*.055) if kind=='launch' else math.sin(i*.23+t*.3)*.10
            ww=3.4;hh=1.91
            p=np.array([[-ww,hh,z],[ww,hh,z],[ww,-hh,z],[-ww,-hh,z],[-ww,hh,z]])
            p=rotate(p,roll=a)
            q=self.project(p,t,roll=spin,yaw=yaw,pitch=pitch)
            power=np.clip((z+17)/20,0,1)**1.6
            self.line(d,q,color(BLUE,.08+power*.42),2 if z>1.9 else 1)
            if z>-.2 and i%3==0:
                self.line(d,q[:2],color(ICE,.25+hit*.5),3)
            if q[0,2]>.6 and i%2==0:
                x,y=q[0,:2];text(im,(x+9,y+7),f'world.branch[{i:02d}] / '+('launch()' if kind=='launch' else 'create()'),15,color(BLUE,.22+power*.5))
        # Light packets follow the terminal's four vanishing rails, rather than a music spectrum.
        for i,r in enumerate(self.seed[:115]):
            z=3.7-((r[0]*22+t*(1.5+r[3]))%22)
            side=i%4;x=(-1 if side<2 else 1)*3.4;y=(-1 if side%2 else 1)*1.91
            p=np.array([[x,y,z],[x,y,z-.20-r[2]*.6]])
            q=self.project(p,t,roll=spin,yaw=yaw,pitch=pitch)
            self.line(d,q,color(ICE,.16+r[4]*.5),2)

    def knot(self,im,t,hit,front=False):
        d=ImageDraw.Draw(im);u=self.u
        for j in range(9):
            v=j/9*math.tau
            r=2.1+.47*np.cos(3*u+v)
            p=np.c_[r*np.cos(2*u),r*np.sin(2*u)*.72,.7*np.sin(3*u+v)]
            p=rotate(p,yaw=t*.22,pitch=math.sin(t*.18)*.35,roll=t*.045)
            p*=1.2+hit*.07
            q=self.project(p,focal=1030)
            self.line(d,q,color(ICE if j==0 else BLUE,.33 if j==0 else .15),2 if j==0 else 1)
            for k in range(5):
                idx=int((t*.22+k*.2+j*.015)%1*(len(u)-1));x,y,z=q[idx]
                if z>.5:d.rectangle((x-3,y-3,x+3,y+3),fill=color(ICE,.66))
        text(im,(54,966),'string → curve → topology → world',15,color(TEXT,.5))

    def orbits(self,im,t,hit,final=False):
        d=ImageDraw.Draw(im);u=self.u
        for j in range(7 if final else 4):
            r=2.2+j*.30
            p=np.c_[np.cos(u)*r,np.sin(u)*r,np.zeros(len(u))]
            p=rotate(p,yaw=j*.49+t*.08,pitch=.32+j*.41,roll=t*.06)
            q=self.project(p,focal=1050)
            self.line(d,q,color(BLUE,.20+j*.025),2 if j%3==0 else 1)
            for k in range(3):
                ix=int(((t*.09+k/3+j*.055)%1)*(len(u)-1));x,y,z=q[ix]
                if z<.4:continue
                size=int(np.clip(65/z,9,35));ink=ICE if k==0 else BLUE
                d.rectangle((x-size,y-size,x+size,y+size),outline=color(ink,.8),width=2)
                d.line((x-size*1.7,y,x+size*1.7,y),fill=color(ink,.6),width=2)
                if j%2==0:text(im,(x+size+8,y-9),['DREAM','VOICE','WORLD'][k],17,color(ink,.65))

    def worldbirth(self,im,t,age,hit):
        d=ImageDraw.Draw(im);e=ease(age/2.5)
        count=int(180+e*520)
        p=self.seed[:count,:3]-.5
        norm=np.linalg.norm(p,axis=1);p=p/np.maximum(.001,norm[:,None])
        r=(.45+self.seed[:count,3]*1.3)*(1.4+e*2.3)
        p*=r[:,None];p=rotate(p,yaw=t*.13,pitch=t*.045)
        q=self.project(p,focal=900)
        # Nearby worlds form a living graph; the same deterministic graph is reproducible per frame.
        for i in range(0,count-12,3):
            for off in [3,11]:
                j=i+off
                if np.linalg.norm(p[i]-p[j])<1.5:
                    self.line(d,q[[i,j]],color(BLUE,.17),1)
        for i,(x,y,z) in enumerate(q):
            if z<.4 or not(-60<x<W+60 and -60<y<H+60):continue
            s=np.clip((9+12*self.seed[i,4])/z,2,20)
            hot=i%11==0
            d.rectangle((x-s,y-s,x+s,y+s),outline=color(ICE if hot else BLUE,.6 if hot else .32),width=2 if hot else 1)
            if hot:text(im,(x+s+3,y-s),f'{i:03X}',12,color(ICE,.65))

    def camera(self,im,t,hit,mode):
        # Subject and geometry share the same small camera impulse; captions are composited afterwards.
        scale=1+hit['kick']*.027+hit['snare']*.017
        if mode in ['portals','fugue']:scale+=.045*(math.sin(t*.81)*.5+.5)
        dx=math.sin(t*12.7)*hit['snare']*7;dy=hit['kick']*9
        angle=math.sin(t*.28)*.55 if mode in ['perform','portals','ignite','fugue'] else 0
        rad=math.radians(angle);c=math.cos(rad)/scale;s=math.sin(rad)/scale
        coeff=(c,-s,W/2-c*W/2+s*H/2+dx,s,c,H/2-s*W/2-c*H/2+dy)
        a=cv2.warpAffine(np.asarray(im),np.array(coeff,dtype='f4').reshape(2,3),(W,H),
                         flags=cv2.INTER_LINEAR|cv2.WARP_INVERSE_MAP,borderMode=cv2.BORDER_CONSTANT,borderValue=(*BG,255))
        return Image.fromarray(a)

    def background(self,im,t,hit,mode):
        if mode in ['perform','lights']:self.knot(im,t,hit['guitar'])
        if mode in ['sky','glass','portals','fugue','coauthor']:
            self.corridor(im,t,hit['kick'],'launch' if mode in ['portals','fugue'] else 'gate')
        if mode in ['satellite','voices','alight','home']:self.orbits(im,t,hit['snare'],mode in ['home','alight'])
        if mode=='ignite':self.worldbirth(im,t,t-150.74,hit['kick'])
