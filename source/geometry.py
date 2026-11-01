import numpy as np
from PIL import Image
from pathlib import Path

def line_segments(curve):
    p=np.asarray(curve,dtype='f4')
    return np.stack([p[:-1],p[1:]],axis=1).reshape(-1,3)

def geometries():
    rng=np.random.default_rng(617)
    result={}
    # A spherical, folded wave-function: the seed from which all later worlds grow.
    n=38000;t=rng.uniform(0,2*np.pi,n);v=rng.uniform(-1,1,n)
    r=4.4+np.cos(5*t+v*3)*.6
    seed=np.c_[r*np.sqrt(1-v*v)*np.cos(t),v*5.0,r*np.sqrt(1-v*v)*np.sin(t)]
    curves=[]
    for k in range(22):
        a=np.linspace(0,2*np.pi,480);b=k/22*np.pi
        p=np.c_[np.cos(a)*4.4,np.sin(a)*np.cos(b)*4.4,np.sin(a)*np.sin(b)*4.4]
        curves.append(line_segments(p))
    result['seed']=(seed,np.concatenate(curves),0)
    # A true perspective sea. The same vertex displacement is applied to points and isolines.
    u=np.linspace(-54,54,140);v=np.linspace(-70,50,180)
    x,z=np.meshgrid(u,v);sea=np.c_[x.ravel(),np.full(x.size,-3.),z.ravel()]
    curves=[line_segments(np.c_[np.full(len(v),a),np.full(len(v),-3.),v]) for a in u[::2]]
    curves += [line_segments(np.c_[u,np.full(len(u),-3.),np.full(len(u),b)]) for b in v[::3]]
    result['sea']=(sea,np.concatenate(curves),1)
    # Nested tilted toroidal filaments; no simulated footage, all analytic 3D geometry.
    n=48000;a=rng.uniform(0,2*np.pi,n);b=rng.uniform(0,2*np.pi,n)
    r=7.0+1.45*np.cos(b)
    torus=np.c_[r*np.cos(a),np.sin(b)*1.5,r*np.sin(a)]
    curves=[]
    for i in range(23):
        a=np.linspace(0,2*np.pi,600);b=i/23*2*np.pi
        r=7.+1.45*np.cos(b+a*3.)
        curves.append(line_segments(np.c_[r*np.cos(a),np.sin(b+a*3.)*1.5,r*np.sin(a)]))
    result['orbit']=(torus,np.concatenate(curves),2)
    # Recursive hexagonal gates, experienced by an actual moving camera.
    curves=[];cloud=[]
    for k,z in enumerate(np.linspace(-90,30,45)):
        a=np.linspace(0,np.pi*2,7)+k*.06
        r=5.8+.8*np.sin(k*.5)
        p=np.c_[np.cos(a)*r,np.sin(a)*r,np.full(len(a),z)]
        curves.append(line_segments(p));cloud.append(p)
        for j in range(6):curves.append(np.array([p[j],p[j]+[0,0,2.72]],dtype='f4'))
    n=30000;a=rng.uniform(0,2*np.pi,n);z=rng.uniform(-90,30,n);r=rng.uniform(5.4,8.,n)
    tunnel=np.c_[r*np.cos(a),r*np.sin(a),z]
    result['tunnel']=(tunnel,np.concatenate(curves),3)
    # A hundred small inhabited worlds, laid on a Fibonacci spiral across an infinite volume.
    cloud=[];curves=[]
    for i in range(144):
        a=i*2.399963;r=4.+np.sqrt(i)*1.55
        c=np.array([r*np.cos(a),np.sin(i*.7)*8.,r*np.sin(a)])
        rad=.15+(.5+.5*np.sin(i*11.7))*.6
        u=rng.uniform(-1,1,160);b=rng.uniform(0,2*np.pi,160)
        sphere=np.c_[np.sqrt(1-u*u)*np.cos(b),u,np.sqrt(1-u*u)*np.sin(b)]*rad+c
        cloud.append(sphere)
        q=np.linspace(0,2*np.pi,100)
        ring=np.c_[np.cos(q)*rad*1.7,np.sin(q)*rad*.65,np.sin(q)*rad]+c
        curves.append(line_segments(ring))
        if i>1:
            prev=np.array([(4.+np.sqrt(i-1)*1.55)*np.cos((i-1)*2.399963),np.sin((i-1)*.7)*8.,(4.+np.sqrt(i-1)*1.55)*np.sin((i-1)*2.399963)])
            if i%12==0:curves.append(np.array([prev,c]))
    result['worlds']=(np.concatenate(cloud),np.concatenate(curves),4)
    # Parametric star-whale, including pectoral fins and a bifurcated fluke.
    n=40000;u=rng.uniform(.01,.99,n);a=rng.uniform(0,2*np.pi,n)
    x=-9+u*18;r=np.sin(u*np.pi)**.72*2.1
    whale=np.c_[x,r*np.cos(a)*.85,r*np.sin(a)]
    fins=[]
    for side in [-1,1]:
        q=rng.uniform(0,1,6500);s=rng.uniform(-1,1,6500)
        fins.append(np.c_[2.5-q*5.+s*(1-q)*.75,-1.0-q*1.6,side*(1.3+q*4.5)])
        q=rng.uniform(0,1,6500);s=rng.uniform(-1,1,6500)
        fins.append(np.c_[-8.6-q*2.2+s*(1-q)*.45,np.sin(q*np.pi)*.35,side*q*4.2])
    whale=np.concatenate([whale]+fins)
    curves=[]
    for angle in np.linspace(0,2*np.pi,28):
        u=np.linspace(.01,.99,320);r=np.sin(u*np.pi)**.72*2.1
        curves.append(line_segments(np.c_[-9+u*18,r*np.cos(angle)*.85,r*np.sin(angle)]))
    for u in np.linspace(.02,.98,24):
        a=np.linspace(0,2*np.pi,160);r=np.sin(u*np.pi)**.72*2.1
        curves.append(line_segments(np.c_[np.full(len(a),-9+u*18),r*np.cos(a)*.85,r*np.sin(a)]))
    result['whale']=(whale,np.concatenate(curves),5)
    # Streamfunction ribbons: interlocking mathematical counterpoint.
    curves=[];cloud=[]
    for i in range(48):
        t=np.linspace(0,2*np.pi,600);phase=i/48*2*np.pi
        r=5.+2.*np.cos(t*3.+phase)
        p=np.c_[r*np.cos(t),2.8*np.sin(t*4.+phase),r*np.sin(t)]
        curves.append(line_segments(p));cloud.append(p)
    result['flow']=(np.concatenate(cloud),np.concatenate(curves),6)
    # Explicit recursive geometry: a third-order Menger construction.
    centers=[np.zeros(3)];size=12.
    for depth in range(3):
        step=size/3
        centers=[c+np.array([i,j,k])*step for c in centers
                 for i in [-1,0,1] for j in [-1,0,1] for k in [-1,0,1]
                 if (i==0)+(j==0)+(k==0)<=1]
        size=step
    corners=np.array([[i,j,k] for i in [-1,1] for j in [-1,1] for k in [-1,1]])*size*.5
    edges=[(a,b) for a in range(8) for b in range(a+1,8) if np.count_nonzero(corners[a]!=corners[b])==1]
    cloud=[];curves=[]
    for c in centers:
        p=corners+c;cloud.append(p)
        # Sparse internal edges retain the large recursive voids as readable negative space.
        if rng.random()<.23:curves.extend([p[[a,b]] for a,b in edges])
    result['fractal']=(np.concatenate(cloud),np.concatenate(curves),2)
    # The same opening portrait becomes an actual 3D glyph cloud in the instrumental bridge.
    portrait=Image.open(Path(__file__).resolve().parents[1]/'assets/greeting.png').convert('RGBA')
    portrait.thumbnail((210,180))
    pixels=np.array(portrait)
    yy,xx=np.where((pixels[:,:,3]>180)&(pixels[:,:,:3].mean(axis=2)>45))
    lum=pixels[yy,xx,:3].mean(axis=1)/255.
    avatar=np.c_[(xx/portrait.width-.5)*14.,(.5-yy/portrait.height)*12.,lum*1.5,lum]
    result['avatar']=(avatar,np.zeros((0,3)),7)
    # Constellation dust exists at multiple parallax distances.
    stars=rng.uniform(-1,1,(7000,3));stars/=np.linalg.norm(stars,axis=1)[:,None];stars*=rng.uniform(24,90,(len(stars),1))
    result['stars']=(stars,np.zeros((0,3)),0)
    return {k:(np.asarray(p,dtype='f4'),np.asarray(l,dtype='f4'),mode) for k,(p,l,mode) in result.items()}
