"""Rebuild editable, precomputed guitar keys after changing guitar-atlas.png."""
from pathlib import Path
import cv2,numpy as np
from PIL import Image
from scipy.ndimage import label,distance_transform_edt

ROOT=Path(__file__).resolve().parents[1]
atlas=Image.open(ROOT/'assets/guitar-atlas.png').convert('RGBA')
rgba=[];sdf=[]
for i in range(8):
    x=i%4;y=i//4;w=atlas.width//4;h=atlas.height//2
    tile=atlas.crop((x*w,y*h,(x+1)*w,(y+1)*h));tile.save(ROOT/f'assets/guitar-{i}.png')
    tile.thumbnail((300,400),Image.Resampling.LANCZOS)
    canvas=Image.new('RGBA',(320,420));canvas.alpha_composite(tile,((320-tile.width)//2,420-tile.height))
    a=np.asarray(canvas).copy();lab,_=label(a[:,:,3]>120);sizes=np.bincount(lab.ravel());sizes[0]=0
    mask=lab==np.argmax(sizes);a[:,:,3]=np.where(mask,a[:,:,3],0)
    rgba.append(a);sdf.append((distance_transform_edt(mask)-distance_transform_edt(~mask)).astype('f4'))
rgba=np.array(rgba);fwd=[];bwd=[];cv2.setNumThreads(1)
for i in range(8):
    a=cv2.cvtColor(rgba[i,:,:,:3],cv2.COLOR_RGB2GRAY);b=cv2.cvtColor(rgba[(i+1)%8,:,:,:3],cv2.COLOR_RGB2GRAY)
    for src,dst,out in [(a,b,fwd),(b,a,bwd)]:out.append(cv2.calcOpticalFlowFarneback(src,dst,None,.5,4,27,5,7,1.5,0).astype('f2'))
path=ROOT/'assets/guitar-frames.npz'
np.savez_compressed(path,rgba=rgba,sdf=np.array(sdf),forward=np.array(fwd),backward=np.array(bwd))
print(path,path.stat().st_size)
