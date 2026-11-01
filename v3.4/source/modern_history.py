"""Five animated, bilingual historical scenes continuing directly from GPT-3."""
import math,json
import numpy as np
from PIL import Image,ImageDraw
from director import FilmV3
from ui import *
from fields import rotate,project
NODES=[
(110.5,'2022','ChatGPT','从模型到对话','ChatGPT：让更多人通过自然语言与 AI 对话。','https://openai.com/index/chatgpt/'),
(114.31,'2023','DeepSeek','早期模型亮相 · DeepSeek-Coder','DeepSeek：公开早期代码模型，让想法走向实现。','https://huggingface.co/deepseek-ai/deepseek-coder-6.7b-base'),
(118.12,'2025.01','DeepSeek-R1','推理能力探索 · 开放代码与权重','DeepSeek-R1：探索推理能力，让更多人参与创造。','https://github.com/deepseek-ai/DeepSeek-R1'),
(121.93,'2026','DeepSeek Harness','一切皆插件 · 智能体框架 · 开发者预览','Harness：把工具、插件与工作流连接成创作空间。','https://github.com/deepseek-ai/deepseek-harness'),
(125.74,'2026.10','DeepSeek-V4.1','Flash · 1017 最新公开更新','V4.1-Flash-1017：推理、编程与智能体能力继续推进。','https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash-1017')]
class ModernHistory(FilmV3):
 def render(self,t,glow=True):
  if t<110.5 or t>=129.55:return super().render(t,glow)
  self.context(t);idx=max(i for i,n in enumerate(NODES) if n[0]<=t);start,year,title,sub,zh,url=NODES[idx];e=t-start
  im=Image.new('RGBA',(W,H),(*BG,255));self.stars(im,t,.8);self.spectacle.corridor(im,t,self.hit['kick'],'gate');d=ImageDraw.Draw(im)
  if idx==0:
   self.history.attention(im,t,self.pulse)
   for i,s in enumerate(['HUMAN > What can we create?','MODEL > Let us begin.','HUMAN > A world for everyone.']):
    x=470+i*65+math.sin(t*.5+i)*30;y=310+i*145
    d.rounded_rectangle((x,y,x+1000,y+98),radius=9,fill=(5,12,27,245),outline=color(BLUE,.8),width=2)
    text(im,(x+28,y+30),typed(s,e-i*.45,26),29,ICE,'mono')
  elif idx==1:
   self.cloud(im,'char-launch',t,(650,160,1780,945),scale=1.25,style='code',opacity=.85)
   code=['def create_world(dream):','    ocean = compile(dream)','    return share(ocean)','>>> world.ready = True']
   for i,s in enumerate(code):text(im,(100,390+i*84),typed(s,e-i*.4,29),32,ICE if i==3 else BLUE,'mono')
   self.explosion(im,t,max(0,e-1.3),(1200,490),.8)
  elif idx==2:
   self.history.tree(im,t,self.pulse,reverse=False)
   self.type3d.giant(im,'R1',(810,300),260,ICE,alpha=.85)
   self.actor(im,'present',t,1565,530,590,740)
   for i,label in enumerate(['explore()','check()','revise()','share()']):
    x=100+i*230;y=770-math.sin(t*.7+i)*40;chip(im,(x,y),label,True,BLUE,23)
  elif idx==3:
   # Plug-in hub and travelling tool calls, an authored illustration of the public architecture.
   tools=['FILES','TERMINAL','BROWSER','EDITOR','RENDER','MEMORY']
   for i,label in enumerate(tools):
    a=i/6*math.tau+t*.16;x=1160+math.cos(a)*500;y=510+math.sin(a)*280
    hot=i==self.beat_index%6;d.line((1160,510,x,y),fill=ICE if hot else color(BLUE,.35),width=4 if hot else 2)
    u=(t*1.4+i*.14)%1;xx=1160*(1-u)+x*u;yy=510*(1-u)+y*u
    d.rectangle((xx-5,yy-5,xx+5,yy+5),fill=ICE)
    panel(im,(x-120,y-50,x+120,y+55),label,ICE if hot else BLUE,level=.8)
    text(im,(x-95,y-13),typed('plugin.ready()',e,24),18,ICE)
   chip(im,(1010,475),'dsh / HARNESS',True,ICE,30)
   text(im,(80,753),'Everything is a Plugin.',30,ICE,'bold')
   text(im,(80,805),'开发者预览 · 从对话走向工具协作',28,TEXT,'cjk')
  else:
   self.world_planes(im,t,21,words=True);self.spectacle.orbits(im,t,self.pulse,True)
   self.type3d.sculpture(im,'V4.1',t,(300,195,1740,880),mode='orbit',gain=1.6,alpha=.85)
   for i,label in enumerate(['REASONING','CODING','AGENTIC TASKS','VISION']):
    text(im,(90,410+i*85),label,28,color(ICE,.9),'bold')
   self.actor(im,'launch',t,1535,490,580,760)
  # Readable dates and bilingual titles are composited after the moving geometry.
  panel(im,(48,70,780,319),'~/history / continued',ICE,level=.55)
  text(im,(70,92),year,65,ICE,'bold');text(im,(73,177),title,38,TEXT,'bold');text(im,(75,246),sub,30,ICE,'cjk')
  for i,n in enumerate(NODES):
   x=75+i*345;d.line((x,886,x+320,886),fill=ICE if i==idx else color(BLUE,.35),width=3 if i==idx else 1)
   text(im,(x,899),n[1]+' / '+(['ChatGPT','DeepSeek','R1','Harness','V4.1 Flash'][i]),16,ICE if i==idx else color(TEXT,.65))
  d.rectangle((0,945,W,H),fill=(3,7,18,255))
  for s,size,y,kind,c in [(title,30,959,'bold',ICE),(zh,46,1013,'cjk',TEXT)]:
   x=(W-font(size,kind).getlength(s))/2;text(im,(x,y),s,size,c,kind)
  return post(im,t,glow)
if __name__=='__main__':
 import render,sys
 render.FilmV3=ModernHistory
 render.main()
