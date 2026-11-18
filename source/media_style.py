"""A unified neon-print shader for every frame of official footage."""
import cv2,numpy as np
cv2.setNumThreads(1)
def neon_print(frame,final=False,frame_index=0):
 c=np.array((255,159,48) if final else (255,38,151),dtype='f4');top=np.array((255,65,177) if final else (44,230,255),dtype='f4')
 u=np.arange(256,dtype='f4')/255;low=np.array((2,4,13),dtype='f4');mid=np.array((43,8,53),dtype='f4')
 lut=np.zeros((256,3),dtype='u1')
 for i,v in enumerate(u):
  if v<.2:rgb=low+(mid-low)*(v/.2)
  elif v<.7:rgb=mid+(c-mid)*((v-.2)/.5)
  else:rgb=c+(top-c)*((v-.7)/.3)
  lut[i]=np.clip(rgb,0,255)
 gray=cv2.cvtColor(frame,cv2.COLOR_RGB2GRAY);printed=lut[gray]
 # Preserve a little local colour while replacing the tonal structure completely.
 out=cv2.addWeighted(frame,.19,printed,.81,0)
 edges=cv2.Canny(gray,65,155);edgecolor=(edges[:,:,None]/255*np.array(top,dtype='f4')*.48).astype('u1');out=cv2.add(out,edgecolor)
 out[::4]=(out[::4].astype('f4')*.80).astype('u1')
 # Traveling thin raster highlights; movement is intrinsic, even in a slow source shot.
 y=(frame_index*3)%out.shape[0];out[max(0,y-1):y+1]=cv2.addWeighted(out[max(0,y-1):y+1],.75,np.full_like(out[max(0,y-1):y+1],top),.25,0)
 return out
