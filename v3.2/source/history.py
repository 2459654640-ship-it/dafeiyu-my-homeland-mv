import math
import numpy as np
from PIL import Image,ImageDraw
from ui import W,H,BG,BLUE,ICE,TEXT,font,text,panel,chip,color,smooth,ease,clamp
from fields import project,rotate

MILESTONES=[
(1943,'FORMAL NEURON','McCulloch / Pitts'),(1950,'CAN MACHINES THINK?','Alan Turing'),
(1956,'DARTMOUTH','Summer research project'),(1958,'PERCEPTRON','Frank Rosenblatt'),
(1986,'BACKPROPAGATION','Rumelhart / Hinton / Williams'),(1997,'DEEP BLUE','IBM'),
(2012,'ALEXNET','Krizhevsky / Sutskever / Hinton'),(2016,'ALPHAGO','Silver et al.'),
(2017,'ATTENTION','Attention Is All You Need'),(2020,'FEW-SHOT LEARNING','GPT-3 / Brown et al.'),
(2024,'DeepSeek-V2','MLA / MoE'),(2025,'DeepSeek-R1','MIT-licensed weights')]

class History:
    def road(self,im,t,at):
        d=ImageDraw.Draw(im);points=[]
        for i in range(len(MILESTONES)):
            delta=i-at;z=4.2+delta*.66
            if z<.35:continue
            x=960+math.sin(i*1.2)*660/z;y=540+delta*128/z+math.cos(i*.8)*80/z
            points.append((i,x,y,z))
        for a,b in zip(points,points[1:]):d.line((a[1],a[2],b[1],b[2]),fill=color(BLUE,.36),width=2)
        for i,x,y,z in points:
            r=max(3,22/z);d.ellipse((x-r,y-r,x+r,y+r),fill=ICE if abs(i-at)<.7 else color(BLUE,.65))
            if abs(i-at)>1.1:text(im,(x+12,y-9),str(MILESTONES[i][0]),max(12,int(40/z)),color(TEXT,.40))

    def label(self,im,index):
        year,title,credit=MILESTONES[index]
        text(im,(64,51),'~/history / idea.commit',17,color(ICE,.65))
        text(im,(61,98),str(year),96,ICE,'bold')
        text(im,(69,212),title,24,TEXT,'bold');text(im,(70,254),credit,16,color(TEXT,.65))
        text(im,(70,1016),'SELECTED IDEAS / primary sources in project notes',13,color(TEXT,.5))

    def neurons(self,im,t,hit):
        d=ImageDraw.Draw(im);points=[(l,k,-1.5+l*.6,(k-3)*.26,.3*math.sin(l*.8+k*.5+t*.3)) for l in range(6) for k in range(7)]
        p=rotate(np.array([a[2:] for a in points]),yaw=math.sin(t*.2)*.28,pitch=.15)
        q=project(p,(300,120,1880,940),cam=3.8)
        for i,(layer,k,*_) in enumerate(points):
            for j,(ll,kk,*_) in enumerate(points):
                if ll!=layer+1 or abs(k-kk)>2:continue
                v=.15+.35*math.exp(-((t*.7-layer*.13-k*.017)%1)*5)
                d.line((q[i,0],q[i,1],q[j,0],q[j,1]),fill=color(BLUE,v),width=1)
                if (k+kk)%3==0:
                    u=(t*1.35+layer*.1+kk*.09)%1;x=q[i,0]*(1-u)+q[j,0]*u;y=q[i,1]*(1-u)+q[j,1]*u
                    d.rectangle((x-2,y-2,x+2,y+2),fill=ICE)
        for i,(layer,k,*_) in enumerate(points):
            x,y=q[i,:2];v=math.exp(-((t*.9-layer*.23-k*.02)%1)*5);r=6+v*10+hit*2
            d.ellipse((x-r,y-r,x+r,y+r),outline=color(ICE,.45+.55*v),width=2)
            if v>.6:d.ellipse((x-3,y-3,x+3,y+3),fill=ICE)
        text(im,(750,927),'signal → connection → a new possibility',23,ICE,'bold')

    def tree(self,im,t,hit,reverse=False):
        d=ImageDraw.Draw(im);levels=7;nodes=[]
        for depth in range(levels):
            for k in range(2**depth):nodes.append((depth,k,(k+.5)/2**depth*2.8-1.4,.9-depth*.29,math.sin(k*.8+depth)*.2))
        q=project(rotate(np.array([n[2:] for n in nodes]),yaw=math.sin(t*.25)*.3),(320,90,1900,940),cam=3.5)
        mapping={(dep,k):i for i,(dep,k,*_) in enumerate(nodes)}
        for i,(dep,k,*_) in enumerate(nodes):
            if dep:
                j=mapping[(dep-1,k//2)];u=(t*1.2-dep*.08)%1
                if reverse:u=1-u
                a=q[j,:2];b=q[i,:2];hot=k==int(t*2)%2**dep
                d.line((*a,*b),fill=ICE if hot else color(BLUE,.32),width=2 if hot else 1)
                dot=a*(1-u)+b*u;d.rectangle((dot[0]-2,dot[1]-2,dot[0]+2,dot[1]+2),fill=color(ICE,.7))
            x,y=q[i,:2];r=3+(levels-dep)*.55;d.rectangle((x-r,y-r,x+r,y+r),fill=ICE if k==0 else color(BLUE,.65))
        text(im,(745,943),'error flows upstream' if reverse else 'search keeps the promising branch',25,ICE,'bold')

    def board(self,im,t,hit,go=True):
        d=ImageDraw.Draw(im);n=19 if go else 8
        coords=[[(i/(n-1)-.5)*2.9,0.,(j/(n-1)-.5)*2.9] for j in range(n) for i in range(n)]
        p=rotate(np.array(coords),yaw=math.sin(t*.18)*.28,pitch=.87);q=project(p,(370,120,1850,960),cam=4.)
        for j in range(n):d.line([tuple(v[:2]) for v in q[j*n:(j+1)*n]],fill=color(BLUE,.43),width=1)
        for i in range(n):d.line([tuple(q[j*n+i,:2]) for j in range(n)],fill=color(BLUE,.43),width=1)
        rng=np.random.default_rng(2016 if go else 1997);pick=rng.choice(len(q),45 if go else 20,replace=False)
        for k,idx in enumerate(pick):
            x,y,z=q[idx];phase=(t*.8+k*.13)%1;r=(15 if go else 18)*(4/z);yy=y-abs(math.sin(phase*math.pi))*hit*50
            d.ellipse((x-r,yy-r*.65,x+r,yy+r*.65),fill=ICE if k%2 else BG,outline=color(ICE,.8),width=2)
            if not go:d.line((x-r*.55,yy,x-r*.27,yy-r*1.8,x+r*.27,yy-r*1.8,x+r*.55,yy),fill=ICE,width=2)
        text(im,(727,949),'neural evaluation × tree search' if go else 'search at superhuman depth',24,ICE,'bold')

    def attention(self,im,t,hit):
        d=ImageDraw.Draw(im);words=['OUR','OCEAN','DREAMS','YOUR','HANDS','EVERY','VOICE','STARS','WORLDS','WE'];points=[]
        for i,w in enumerate(words):
            a=i/len(words)*math.tau+t*.12;z=math.sin(a)*.65
            points.append((1170+math.cos(a)*590/(1.2+z*.3),535+math.sin(a)*285/(1.2+z*.3),z))
        for i,a in enumerate(points):
            for j,b in enumerate(points):
                if j<=i or (i+j)%3==0:continue
                alpha=.14+.18*(math.sin(t*1.1+i*.5-j*.1)*.5+.5);d.line((a[0],a[1],b[0],b[1]),fill=color(BLUE,alpha),width=1)
                u=(t*.6+i*.07+j*.1)%1;x=a[0]*(1-u)+b[0]*u;y=a[1]*(1-u)+b[1]*u
                d.rectangle((x-2,y-2,x+2,y+2),fill=color(ICE,.65))
        for i,(x,y,z) in enumerate(points):
            size=int(23+(1-z)*11);w=font(size,'bold').getlength(words[i])+20
            d.rectangle((x-w/2-5,y-12,x+w/2+5,y+size+10),fill=BG,outline=color(BLUE,.55));text(im,(x-w/2+5,y),words[i],size,ICE,'bold')
        text(im,(744,949),'words learn to see one another',24,ICE,'bold')
