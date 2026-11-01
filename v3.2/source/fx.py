import math
import numpy as np
from PIL import Image,ImageDraw,ImageFilter
from ui import W,H,BG,TEXT,DIM,BLUE,ICE,BRAND,color,text,panel,chip,cursor,smooth,ease,clamp

MAIN=(594,112,1726,906)

def bezier(a,b,c,d,u):
    return (1-u)**3*a+3*(1-u)**2*u*b+3*(1-u)*u*u*c+u**3*d

class FX:
    """Independent time-addressable motion layers, not a random filter over still pictures."""
    def __init__(self,glyph):
        self.glyph=glyph
        self.rng=np.random.default_rng(1024)
        self.seeds=self.rng.random((160,6))
        self.cached={}

    def intensity(self,t):
        if t<15.96:return .10
        if t<31.7:return .20
        if t<46.18:return .45
        if t<63.7:return .34
        if t<80.02:return .95
        if t<95.26:return .60
        if t<139.78:return .78
        if t<172.01:return 1.
        if t<187.42:return .18
        return .08

    def filaments(self,layer,t,drive,bass,pulse,kind):
        if drive<.3:return
        d=ImageDraw.Draw(layer)
        count=6 if drive<.6 else 12
        # Interlocking streamline trajectories have distinct phase and pitch, creating depth and counterpoint.
        for k in range(count):
            u=np.linspace(-math.pi,math.pi,115)
            a=k/count*math.tau
            x=np.sin(u*1.12+a)*430
            y=np.sin(u*1.83+a*.65+t*.20)*155
            z=np.cos(u*1.12+a)*.65
            roll=math.sin(t*.23)*.24
            xr=x*math.cos(roll)-y*math.sin(roll);yr=x*math.sin(roll)+y*math.cos(roll)
            den=1.4-z*.28
            px=1160+xr/den;py=526+yr/den+math.sin(t*.6+k)*16
            points=list(zip(px,py))
            d.line(points,fill=(*color(BLUE,.20+.12*drive),95),width=1)
            # A packet runs along each path; these are actual moving traces, not a breathing outline.
            at=(t*(.14+k*.003)+k/count)%1
            j=int(at*(len(px)-10));trail=list(zip(px[j:j+10],py[j:j+10]))
            d.line(trail,fill=(*color(ICE,.65+.25*pulse),180),width=2)
            if len(trail):
                x0,y0=trail[-1];d.rectangle((x0-2,y0-2,x0+2,y0+2),fill=(*ICE,230))
        # Parallel timing rails make the two guitar lines visible as independent moving streams.
        for rail in range(2):
            yy=205+rail*600
            for k in range(22):
                x=620+((k*61+t*(125+rail*32))%1050)
                y=yy+math.sin(x*.008+t+rail)*16
                if k%3:d.line((x,y,x+11,y),fill=(*color(BLUE,.34),140))
                elif drive>.7:text(layer,(x,y-5),'01'[k%2],12,color(ICE,.65))

    def data_particles(self,layer,t,drive,pulse,kind):
        if drive<.24:return
        d=ImageDraw.Draw(layer);n=int(55+drive*90)
        for i,r in enumerate(self.seeds[:n]):
            u=(t*(.10+r[3]*.09)+r[0])%1
            x=611+u*1090
            y=137+r[1]*735+math.sin(t*.7+r[2]*math.tau+u*7.)*(14+drive*36)
            if kind in ['free','climax','whale']:
                a=r[0]*math.tau+t*.08;rad=50+u*580
                x=1160+math.cos(a)*rad;y=520+math.sin(a)*rad*.58
            opacity=math.sin(u*math.pi)**.5
            c=color(ICE if i%8==0 else BLUE,(.22+.45*opacity)*drive)
            if i%11==0:text(layer,(x,y),f'{int(r[4]*65535):04X}',11,c)
            else:
                length=3+int(r[5]*8)
                d.line((x,y,x-length,y),fill=(*c,160),width=1)
                if i%5==0:d.rectangle((x-1,y-1,x+1,y+1),fill=(*c,210))

    def sparks(self,layer,t,e,drive,pulse,kind,beat):
        if drive<.5:return
        d=ImageDraw.Draw(layer)
        # Beat-locked geometric shock fronts are short accents under authored action, not a standalone visualizer.
        radius=45+(1-pulse)*350
        if pulse>.10:
            col=(*color(ICE,pulse*.28*drive),int(150*pulse))
            d.ellipse((1160-radius,515-radius*.56,1160+radius,515+radius*.56),outline=col,width=1)
        if kind not in ['free','ignite','climax','queue','coauthor']:return
        tau=(t*.525)%1
        for i in range(28):
            a=i/28*math.tau+(beat%7)*.17
            r=40+tau*620
            x=1160+math.cos(a)*r;y=520+math.sin(a)*r*.58
            c=(*color(ICE,(1-tau)*.68),int((1-tau)*190))
            d.line((1160+math.cos(a)*(r-18),520+math.sin(a)*(r-18)*.58,x,y),fill=c,width=1)

    def moving_panels(self,layer,t,drive,pulse,kind):
        if drive<.6 or kind in ['satellites','worlds','samples','coauthor']:return
        # Small diagnostic panes fly on genuine projected quadrilaterals, with animated internal content.
        d=ImageDraw.Draw(layer)
        for i in range(3):
            ph=t*.28+i*math.tau/3
            z=math.sin(ph);scale=.65+(.5+.5*z)*.25
            cx=1160+math.cos(ph)*422;cy=520+math.sin(ph*1.3)*225
            w=154*scale;h=92*scale;skew=math.sin(ph)*15
            corners=[(cx-w/2+skew,cy-h/2),(cx+w/2+skew,cy-h/2-7*z),(cx+w/2-skew,cy+h/2),(cx-w/2-skew,cy+h/2+7*z)]
            d.polygon(corners,fill=(5,8,16,180),outline=(*color(BLUE,.50),180),width=1)
            text(layer,(cx-w/2+10,cy-h/2+12),['FIELD','SEED','WORLD'][i],12,color(ICE,.70))
            for k in range(5):
                v=(math.sin(t*1.6+k*.7+i)*.5+.5)
                d.line((cx-w/2+12,cy-10+k*9,cx-w/2+12+(w-30)*v,cy-10+k*9),fill=(*color(BLUE,.30+v*.4),200))
            d.line((cx,cy,1160,520),fill=(*color(BLUE,.16),65))

    def transition(self,im,old,e,index):
        if old is None or e>=.78:return
        progress=clamp(e/.78);u=ease(progress)
        source=old
        # Two families of geometrical transitions share the existing content as a physical carrier.
        cols,rows=(6,4) if index%2 else (10,2)
        sw,sh=source.size;d=ImageDraw.Draw(im)
        for iy in range(rows):
            for ix in range(cols):
                x0=int(ix*sw/cols);y0=int(iy*sh/rows);x1=int((ix+1)*sw/cols);y1=int((iy+1)*sh/rows)
                cx=(x0+x1)/2-sw/2;cy=(y0+y1)/2-sh/2
                delay=(ix+iy)%4*.025
                q=ease(max(0,progress-delay)/(1-delay))
                if q>.96:continue
                tile=source.crop((x0,y0,x1,y1))
                if index%2:
                    angle=math.atan2(cy,cx)+index*.37
                    dx=math.cos(angle)*q*360;dy=math.sin(angle)*q*240
                    tile=tile.rotate((ix-iy)*q*7,Image.Resampling.NEAREST,expand=True)
                    xx=MAIN[0]+x0+dx-(tile.width-(x1-x0))/2
                    yy=MAIN[1]+y0+dy-(tile.height-(y1-y0))/2
                else:
                    w=max(1,int(tile.width*(1-q*.95)))
                    tile=tile.resize((w,tile.height),Image.Resampling.NEAREST)
                    xx=MAIN[0]+x0+(x1-x0-w)/2+q*(ix-cols/2)*22
                    yy=MAIN[1]+y0+math.sin(ix*.6+index)*q*140
                tile.putalpha(int(255*(1-progress)**.48))
                im.alpha_composite(tile,(int(xx),int(yy)))
        # A small source packet persists into the incoming scene, giving the eye an intentional hand-off.
        x=594+566+math.sin(index)*u*330;y=112+397-u*160
        d.rectangle((x-4,y-4,x+4,y+4),fill=(*ICE,int(220*(1-progress))))

    def interference(self,im,t,drive,pulse,beat,kind):
        if drive<.5:return im
        # Brief, local terminal memory-row displacement, timed to selected percussion hits.
        if pulse<.80 or beat%4 not in [0,3]:return im
        q=im.copy();d=ImageDraw.Draw(q)
        for i in range(3 if drive>.8 else 1):
            y=138+int((math.sin(beat*1.79+i*2.7)*.5+.5)*725)
            block=im.crop((598,y,1722,y+4+i*2))
            offset=(i*7+4)*(1 if beat%2 else -1)
            q.alpha_composite(block,(598+offset,y))
            d.line((599,y-1,1722,y-1),fill=(*color(BLUE,.35),100))
        return q

    def camera(self,im,t,e,kind,drive):
        if kind not in ['tunnel','recurse','climax','whale'] or drive<.6:return im
        # The entire continuously animated terminal is a plane in world space in these bridge shots.
        # This is a camera transformation of a live scene, not a Ken Burns move over an illustration.
        yaw=math.sin(t*.47)*.16
        pitch=math.sin(t*.31)*.065
        if kind=='climax':yaw+=math.sin(e*3.2)*.055
        p=np.array([[-1,-H/W,0],[1,-H/W,0],[1,H/W,0],[-1,H/W,0]],dtype=float)
        cy,sy=math.cos(yaw),math.sin(yaw);cp,sp=math.cos(pitch),math.sin(pitch)
        p[:,[0,2]]=p[:,[0,2]]@np.array([[cy,-sy],[sy,cy]])
        p[:,[1,2]]=p[:,[1,2]]@np.array([[cp,-sp],[sp,cp]])
        focal=W*.49;cam=1.07
        den=cam-p[:,2]
        dst=np.c_[W/2+p[:,0]*focal/den,H/2+p[:,1]*focal/den]
        src=np.array([[0,0],[W,0],[W,H],[0,H]],dtype=float)
        A=[];b=[]
        for (x,y),(u,v) in zip(dst,src):
            A.extend([[x,y,1,0,0,0,-u*x,-u*y],[0,0,0,x,y,1,-v*x,-v*y]]);b.extend([u,v])
        coeff=np.linalg.solve(np.array(A),np.array(b))
        warped=im.transform((W,H),Image.Transform.PERSPECTIVE,coeff,Image.Resampling.BICUBIC)
        back=Image.new('RGBA',(W,H),(*BG,255));d=ImageDraw.Draw(back)
        for i in range(1,12):
            x=i*W/12;d.line((W/2,H/2,x,H),fill=(*color(BLUE,.13),255))
            y=H*(.65+i*.025);d.line((0,y,W,y),fill=(*color(BLUE,.11),255))
        back.alpha_composite(warped)
        return back

    def apply(self,im,t,s,e,energy,bass,air,pulse,beat,previous=None):
        drive=self.intensity(t);kind=s['kind']
        # All FX are alpha composited. Low opacity is not multiplied into a dark RGB color twice.
        layer=Image.new('RGBA',(W,H))
        self.filaments(layer,t,drive,bass,pulse,kind)
        self.data_particles(layer,t,drive,pulse,kind)
        self.sparks(layer,t,e,drive,pulse,kind,beat)
        self.moving_panels(layer,t,drive,pulse,kind)
        # Keep captions and chat readable; stage layers may cross its right edge only during an impact.
        mask=Image.new('L',(W,H));ImageDraw.Draw(mask).rectangle((584,89,1742,929),fill=255)
        alpha=np.asarray(layer.getchannel('A'),dtype=np.uint16)*np.asarray(mask,dtype=np.uint16)//255
        layer.putalpha(Image.fromarray(alpha.astype('u1')))
        im.alpha_composite(layer)
        self.transition(im,previous,e,s['index'])
        im=self.interference(im,t,drive,pulse,beat,kind)
        im=self.camera(im,t,e,kind,drive)
        return im
