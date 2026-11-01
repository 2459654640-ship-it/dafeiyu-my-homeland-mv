import math,functools
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.ndimage import distance_transform_edt,gaussian_filter
from ui import ROOT,clamp,smooth

RNG=np.random.default_rng(260611)

@functools.lru_cache(24)
def asset_points(name,size=300):
    path=ROOT/f'assets/{name}.png'
    im=Image.open(path).convert('RGBA');im.thumbnail((size,size))
    a=np.array(im);mask=a[:,:,3]>150
    lum=(a[:,:,0]*.22+a[:,:,1]*.58+a[:,:,2]*.20)/255.
    yy,xx=np.where(mask)
    if len(xx)>45000:
        ix=np.linspace(0,len(xx)-1,45000,dtype=int);yy,xx=yy[ix],xx[ix]
    depth=distance_transform_edt(mask);depth/=max(1,depth.max())
    scale=max(im.size)
    p=np.c_[(xx-im.width/2)/scale*2,(im.height/2-yy)/scale*2,depth[yy,xx]*.3]
    brightness=.15+.85*np.sqrt(lum[yy,xx])
    return p.astype('f4'),brightness.astype('f4')

@functools.lru_cache(1)
def basis():
    u,v=np.meshgrid(np.linspace(-2.3,2.3,230),np.linspace(-5.,2.,190))
    ocean=np.c_[u.ravel(),np.zeros(u.size),v.ravel()].astype('f4')
    rng=np.random.default_rng(37)
    star=rng.uniform(-1,1,(16000,3));star/=np.linalg.norm(star,axis=1)[:,None]
    star*=rng.uniform(.6,2.8,(len(star),1))
    # Numerically integrated Lorenz paths, retained as trajectories and moving packets.
    trails=[];p=np.array([.12,.25,2.1])
    for i in range(40000):
        def f(q):x,y,z=q;return np.array([10*(y-x),x*(28-z)-y,x*y-8/3*z])
        k1=f(p);k2=f(p+k1*.003);k3=f(p+k2*.003);k4=f(p+k3*.006)
        p=p+.006*(k1+2*k2+2*k3+k4)/6
        if i>4000:trails.append(p.copy())
    flow=np.array(trails);flow=(flow-[0,0,25])/[18,24,25]
    centers=np.zeros((1,3));s=1.7
    offsets=np.array([[i,j,k] for i in [-1,0,1] for j in [-1,0,1] for k in [-1,0,1] if (i==0)+(j==0)+(k==0)<=1])
    for depth in range(3):
        s/=3;centers=(centers[:,None,:]+offsets[None,:,:]*s*2).reshape(-1,3)
    corners=np.array([[i,j,k] for i in [-1,1] for j in [-1,1] for k in [-1,1]])*s
    fractal=(centers[:,None,:]+corners[None,:,:]).reshape(-1,3)
    return ocean,star.astype('f4'),flow.astype('f4'),fractal.astype('f4')

def rotate(p,yaw=0,pitch=0,roll=0):
    q=p.copy()
    c,s=math.cos(yaw),math.sin(yaw);q[:,[0,2]]=q[:,[0,2]]@np.array([[c,-s],[s,c]])
    c,s=math.cos(pitch),math.sin(pitch);q[:,[1,2]]=q[:,[1,2]]@np.array([[c,-s],[s,c]])
    c,s=math.cos(roll),math.sin(roll);q[:,[0,1]]=q[:,[0,1]]@np.array([[c,-s],[s,c]])
    return q

def field(name,t,bass=0.,phase=0.):
    sea,stars,flow,fractal=basis()
    if name in ['ocean','tide']:
        p=sea.copy();x,z=p[:,0],p[:,2]
        y=np.zeros(len(p));dx=np.zeros(len(p));dz=np.zeros(len(p))
        for k,(freq,angle,amp) in enumerate([(1.7,.2,.11),(3.4,1.0,.065),(6.3,2.,.037),(9.7,.7,.023),(14.,2.7,.016)]):
            a=math.cos(angle)*freq;b=math.sin(angle)*freq
            arg=x*a+z*b-t*(.55+k*.27)
            y+=np.sin(arg)*amp;dx+=np.cos(arg)*amp*a;dz+=np.cos(arg)*amp*b
        if name=='tide':
            crest=np.exp(-((z+.3-math.sin(t*.5)*.5)/.6)**2)
            y+=crest*(.18+bass*.30)*np.cos(x*2.-t)
        p[:,1]=y-.4
        p=rotate(p,pitch=.28)
        lum=np.clip(.35+(-dx*.3+dz*.4)+y*.2,.12,.95)
        return p,lum,3.6
    if name in ['whale','island','station','seed','planet','fluke','portal','citadel','moebius','jellyfish','orrery','origami','relay','loom','shattered']:
        p,b=asset_points(name)
        p=p.copy()
        if name=='whale':
            tail=np.clip((-p[:,0]-.15)*1.2,0,1)
            p[:,1]+=np.sin(t*2.1+p[:,0]*2.)*.10*tail
            p[:,2]+=np.sin(t*2.1+p[:,0]*2.)*.18*tail
            p[:,1]+=.025*math.sin(t*.8)
            p=rotate(p,yaw=math.sin(t*.25)*.24,pitch=math.sin(t*.3)*.04)
        elif name=='jellyfish':
            tail=np.clip(.3-p[:,1],0,1)
            p[:,0]+=np.sin(t*1.3+p[:,1]*9)*tail*.10
            p[:,2]+=np.cos(t*1.1+p[:,1]*8)*tail*.12
            p=rotate(p,yaw=math.sin(t*.25)*.3)
        elif name in ['station','planet','seed','island','citadel','portal','orrery','moebius','loom','relay','origami','shattered']:
            p=rotate(p,yaw=math.sin(t*.3)*.4,roll=math.sin(t*.22)*.08)
        return p,b,2.4
    if name.startswith('char-'):
        p,b=asset_points(name)
        p=p.copy();edge=np.abs(p[:,0]);lower=np.clip(.5-p[:,1],0,1)
        p[:,0]+=np.sin(p[:,1]*5+t*1.3)*edge*lower*.08
        p=rotate(p,yaw=math.sin(t*.35)*.28)
        return p,b,2.2
    if name=='sky':
        p=stars.copy();p=rotate(p,yaw=t*.025,pitch=.15)
        lum=.25+.65*(np.sin(np.arange(len(p))*.17+t*.6)*.5+.5)
        return p,lum,3.4
    if name in ['flow','flame']:
        shift=int(t*180)%len(flow);p=np.roll(flow,-shift,axis=0).copy()
        p=rotate(p,yaw=t*.065,pitch=.35,roll=.12)
        lum=np.clip(1-np.arange(len(p))/len(p)*.75,.2,1.)
        if name=='flame':
            p[:,1]*=1.25;p[:,0]*=.75
            lum*=.8+.2*np.sin(p[:,1]*10-t*4.)
        return p,lum,3.1
    if name=='fractal':
        p=rotate(fractal,yaw=t*.12,pitch=t*.055)
        lum=.35+.5*(p[:,2]+1.7)/3.4
        return p,lum,3.7
    if name=='tunnel':
        rings=[];bright=[]
        for i in range(34):
            z=-7+((i*.45+t*.85)%15.)
            a=np.linspace(0,2*np.pi,180)
            r=1.45+.12*math.sin(z*.6)
            p=np.c_[np.cos(a+z*.08)*r,np.sin(a+z*.08)*r,np.full(len(a),z)]
            rings.append(p);bright.append(np.full(len(a),.3+.5*(z+7)/15))
        return np.concatenate(rings),np.concatenate(bright),9.0
    return field('sky',t,bass)

def project(p,rect,cam=3.,yaw=0,pitch=0):
    p=rotate(p,yaw,pitch)
    x,y,x2,y2=rect;w=x2-x;h=y2-y
    den=np.maximum(.22,cam-p[:,2]);scale=min(w,h)*cam*.43
    return np.c_[x+w/2+p[:,0]*scale/den,y+h/2-p[:,1]*scale/den,den]

def raster(p,lum,rect,glyph,cam=3.,yaw=0,pitch=0,style='solid',phase=0,alpha=1.,letter=''):
    x,y,x2,y2=rect;cols=max(1,int((x2-x)/glyph.cw));rows=max(1,int((y2-y)/glyph.ch))
    q=project(p,(0,0,cols,rows),cam,yaw,pitch)
    # Correct for the non-square terminal cell aspect after the 3D projection.
    q[:,0]=(q[:,0]-cols/2)*glyph.ch/glyph.cw+cols/2
    ix=q[:,0].astype(int);iy=q[:,1].astype(int)
    valid=(ix>=0)&(ix<cols)&(iy>=0)&(iy<rows)&(cam-p[:,2]>.25)
    ids=iy[valid]*cols+ix[valid]
    values=np.zeros(rows*cols,dtype='f4')
    np.maximum.at(values,ids,np.asarray(lum)[valid])
    values=values.reshape(rows,cols)
    return glyph.field(values,style=style,phase=phase,alpha=alpha,letter=letter)

def scalar_field(t,cols=112,rows=42,kind='velocity',energy=0.):
    y,x=np.mgrid[-1:1:complex(rows),-1.6:1.6:complex(cols)]
    if kind=='velocity':
        r=np.hypot(x+.4*math.sin(t*.4),y+.3*math.cos(t*.3));a=np.arctan2(y,x)
        v=np.sin(r*14.-t*2.+np.sin(a*4.))*np.exp(-r*.7)
        return np.clip((v+.15)*(.7+energy*.4),0,1)
    if kind=='reaction':
        v=np.sin(x*8+t*.6)*np.cos(y*12-t*.5)+np.sin((x+y)*9-t*.4)*.4
        return np.clip((np.abs(v)-.4)*1.4,0,1)
    if kind=='spectrum':
        return np.clip(np.cos(x*4+t)*np.cos(y*6-t*.5),0,1)
    return np.clip(np.sin(np.hypot(x,y)*15-t*3),0,1)
