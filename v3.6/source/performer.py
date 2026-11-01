import math,functools
import numpy as np
import cv2
cv2.setNumThreads(1)
from PIL import Image,ImageDraw,ImageFilter
from scipy.ndimage import distance_transform_edt
from ui import ROOT,BLUE,ICE,TEXT,BG,color,smooth,ease,clamp,font

class Performer:
    def __init__(self):
        data=np.load(ROOT/'assets/guitar-frames.npz')
        self.sdf=data['sdf'];self.rgba=data['rgba']
        self.forward=data['forward'].astype('f4');self.backward=data['backward'].astype('f4')
        self.yy,self.xx=np.indices(self.sdf.shape[1:],dtype='f4')
        self.targets={}
        for name in ['whale','FREE']:
            canvas=Image.new('L',(320,420))
            if name=='whale':
                a=Image.open(ROOT/'assets/whale.png').getchannel('A');a.thumbnail((315,295),Image.Resampling.LANCZOS)
                canvas.paste(a,((320-a.width)//2,(420-a.height)//2))
            else:
                a=Image.new('L',(560,240));f=font(185,'bold')
                ImageDraw.Draw(a).text((1,-f.getbbox('FREE')[1]),'FREE',font=f,fill=255)
                a=a.crop(a.getbbox());a.thumbnail((310,190),Image.Resampling.LANCZOS)
                canvas.paste(a,((320-a.width)//2,(420-a.height)//2))
            mask=np.asarray(canvas)>130
            self.targets[name]=distance_transform_edt(mask)-distance_transform_edt(~mask)
        self.sil_cache={};self.images={};self.grids={}
        self.opening=Image.open(ROOT/'assets/opening-greet.png').convert('RGBA')

    def guitar(self,phase,t,width=780,height=920,silhouette=False,ink=(239,245,255),drive=0.,transition=None):
        if not silhouette:
            # Eight beat-driven key poses with eased short dissolves; no optical flow or local stretching.
            q=phase*2;i=int(math.floor(q))%8
            u=smooth(clamp((q-math.floor(q))/.45))
            im=Image.blend(Image.fromarray(self.rgba[(i-1)%8]),Image.fromarray(self.rgba[i]),u)
            im.thumbnail((width,height),Image.Resampling.LANCZOS)
            if im.height<height and im.width<width:
                sc=min(width/im.width,height/im.height);im=im.resize((int(im.width*sc),int(im.height*sc)),Image.Resampling.LANCZOS)
            return im
        i=int(math.floor(phase))%8;j=(i+1)%8;u=phase-math.floor(phase)
        # Interpolate signed-distance shapes so each frame has a single moving contour rather than a double exposure.
        # Bidirectional optical flow transports both shape and texture into the intermediate pose.
        # This avoids eight held illustrations with simple dissolves between them.
        mx1=self.xx-self.forward[i,:,:,0]*u;my1=self.yy-self.forward[i,:,:,1]*u
        mx2=self.xx-self.backward[i,:,:,0]*(1-u);my2=self.yy-self.backward[i,:,:,1]*(1-u)
        sa=cv2.remap(self.sdf[i],mx1,my1,cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT,borderValue=-50)
        sb=cv2.remap(self.sdf[j],mx2,my2,cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT,borderValue=-50)
        sdf=sa*(1-u)+sb*u
        if transition:
            a,b,q=transition
            aa=sdf if a=='guitar' else self.targets[a]
            bb=sdf if b=='guitar' else self.targets[b]
            sdf=aa*(1-smooth(q))+bb*smooth(q)
        alpha=np.clip((sdf+.8)*170,0,255).astype('u1')
        rows,cols=alpha.shape;yy,xx=np.indices((rows,cols))
        edge=np.abs(xx-cols*.5)/(cols*.5)
        dx=np.sin(t*2.0+yy*.032)*edge*np.clip(.45-yy/rows,0,1)*3
        dy=np.sin(t*1.2+xx*.018)*np.clip(yy/rows-.8,0,1)*1.3
        arm=np.exp(-((xx-158)/36)**2-((yy-201)/28)**2)
        dy+=arm*math.sin(phase*math.tau*2)*5*(.4+drive)
        ix=np.clip(np.rint(xx-dx).astype(int),0,cols-1);iy=np.clip(np.rint(yy-dy).astype(int),0,rows-1)
        alpha=alpha[iy,ix]
        if silhouette:
            scale=min(width/cols,height/rows);ow=int(cols*scale);oh=int(rows*scale)
            warped=cv2.remap(sdf.astype('f4'),(xx-dx).astype('f4'),(yy-dy).astype('f4'),cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT,borderValue=-50)
            high=cv2.resize(warped,(ow,oh),interpolation=cv2.INTER_CUBIC)
            mask=np.clip((high*scale+.5)*255,0,255).astype('u1')
            image=Image.new('RGBA',(ow,oh),(*ink,255));image.putalpha(Image.fromarray(mask))
            return image
        else:
            ma=cv2.remap(self.rgba[i],mx1,my1,cv2.INTER_LINEAR)
            mb=cv2.remap(self.rgba[j],mx2,my2,cv2.INTER_LINEAR)
            mat=(ma.astype('f4')*(1-u)+mb.astype('f4')*u).astype('u1')[iy,ix].copy()
            lum=(mat[:,:,0]*.22+mat[:,:,1]*.58+mat[:,:,2]*.2)/255.
            # A generous lower bound keeps dark hair readable in glyph/pixel treatment.
            palette=np.array([(12,19,47),(24,38,84),(43,62,129),(67,91,177),(104,134,216),(156,184,241),(213,231,253),(245,249,255)])
            mat[:,:,:3]=palette[np.clip((np.sqrt(lum)*7).astype(int),0,7)]
            mat[:,:,3]=alpha;a=mat
        im=Image.fromarray(a)
        scale=min(width/im.width,height/im.height)
        return im.resize((int(im.width*scale),int(im.height*scale)),Image.Resampling.BICUBIC)

    def actor(self,name,t,width=650,height=930):
        key=(name,width,height)
        if key not in self.images:
            im=Image.open(ROOT/f'assets/char-{name}.png').convert('RGBA')
            # Match a common registration canvas, preserving motion space around the silhouette.
            im.thumbnail((width,height),Image.Resampling.LANCZOS);self.images[key]=im
        im=self.images[key];w,h=im.size
        if key not in self.grids:
            xx=np.arange(w,dtype='f4')[None,:];yy=np.arange(h,dtype='f4')[:,None]
            self.grids[key]=(xx,yy,np.abs(xx/w-.5)*2,np.asarray(im))
        xx,yy,edge,a=self.grids[key];lower=np.maximum(0,yy/h-.25)
        mx=xx-np.sin(t*1.4+yy/h*6)*edge*lower*w*.012
        my=np.broadcast_to(yy-np.sin(t+xx/w*5)*edge*h*.004,(h,w)).copy()
        return Image.fromarray(cv2.remap(a,mx.astype('f4'),my,cv2.INTER_CUBIC))

    def greeting(self,t,height=1000):
        # The large opening artwork is an actual foreground component with peripheral mesh motion.
        key=('opening',height)
        if key not in self.images:
            src=self.opening.copy();src.thumbnail((1600,height),Image.Resampling.LANCZOS);self.images[key]=src
        src=self.images[key];w,h=src.size
        if key not in self.grids:
            xx=np.arange(w,dtype='f4')[None,:];yy=np.arange(h,dtype='f4')[:,None]
            self.grids[key]=(xx,yy,np.abs(xx/w-.5)*2,np.asarray(src))
        xx,yy,side,a=self.grids[key]
        mx=xx-np.sin(t*1.5+yy/h*6)*side**2*w*.009
        my=np.broadcast_to(yy-np.sin(t*.9+xx/w*5)*side*h*.003,(h,w)).copy()
        return Image.fromarray(cv2.remap(a,mx.astype('f4'),my,cv2.INTER_CUBIC))
