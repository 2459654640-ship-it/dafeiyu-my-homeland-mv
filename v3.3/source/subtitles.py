from pathlib import Path
import json
R=Path(__file__).resolve().parents[1];P=R.parent
lines=json.loads((P/'analysis/lyrics.json').read_text());plan=json.loads((P/'v3.2/analysis/shot-plan.json').read_text())
notes=[(31.7,39.34,'COMPILE / PLAY','编译这首歌，让世界开始演奏。'),(39.34,46.18,'OCEAN / NO FINAL EDGE','越过海平线，世界没有最后的边界。'),(80.02,81.72,'1943 / FORMAL NEURON','形式神经元：把思考的可能，写成连接。'),(81.72,83.55,'1950 / CAN MACHINES THINK?','图灵发问：机器能够思考吗？'),(83.55,85.265,'1956 / DARTMOUTH','达特茅斯研究项目：探索人工智能的可能。'),(85.265,87.64,'1958 / PERCEPTRON','感知机：让机器从样本中学习。'),(87.64,91.45,'1986 / BACKPROPAGATION','反向传播：让误差信号逆流，修正连接。'),(91.45,95.26,'1997 / DEEP BLUE','深蓝：沿着搜索树，寻找下一步棋。'),(95.26,99.07,'2012 / ALEXNET','深度视觉：从层层特征中，学习看见。'),(99.07,102.88,'2016 / ALPHAGO','阿尔法围棋：让神经网络与树搜索携手落子。'),(102.88,106.69,'2017 / ATTENTION','注意力机制：让词语学会彼此关联。'),(106.69,110.5,'2020 / FEW-SHOT LEARNING','少样本学习：从少量示例中理解新的任务。'),(110.5,114.31,'OCEAN / PLAY','演奏吧，让这片海自由流动。'),(114.31,118.12,'SET FREE','挣脱边界，让歌声自由。'),(118.12,121.74,'NO FINAL EDGE','这片海，没有最后的边界。'),(121.74,125.74,'WE CREATE / FREE','我们一起，创造新的世界。'),(125.74,127.44,'2024 / DeepSeek-V2 / MLA / MoE','DeepSeek-V2：多头潜在注意力与混合专家架构。'),(127.44,129.55,'2025 / DeepSeek-R1 / OPEN BRANCHES','DeepSeek-R1：开放的代码与权重，让更多人参与。'),(129.55,133.36,'YOUR TURN / ENTER','现在，轮到你了——按下回车，一起创造。'),(133.36,139.78,'NO CLOSED WINDOW','窗口不再是边界；每个想法，都能打开一个世界。'),(154.8,158.61,'WORLDS / ACROSS THE FRAME','让新生的世界，继续向画面之外生长。'),(158.61,162.42,'CURRENT / LIVING NETWORKS','我们的声音，汇成彼此连接的生命之流。'),(162.42,166.23,'CODA / ONE MORE SKY','再演奏一次，再打开一片天空。'),(166.23,172.01,'HOME / A SHARED WORLD','家乡，是我们共同创造的世界。'),(172.01,179.04,'RETURN / WELCOME HOME','欢迎回家——这里有我们一起创造的一切。'),(179.04,187.42,'ARCHIVE / KEEP WORLDS OPEN','保存这一刻，让世界继续向每个人敞开。')]
events=[]
for l in lines:
 for s in plan:
  if s['mode'] in ['opening','boot','dock','return','archive','end']:continue
  a=max(l['start'],s['start']);b=min(l['end']+.32,s['end'])
  if b>a:events.append(dict(start=a,end=b,en=l['en'],zh=l['zh'],kind='lyric'))
for a,b,en,zh in notes:events.append(dict(start=a,end=b,en=en,zh=zh,kind='narration'))
events.sort(key=lambda e:e['start'])
def stamp(t):
 n=round(t*100);return f'{n//360000}:{n//6000%60:02d}:{n//100%60:02d}.{n%100:02d}'
ass='''[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 2
ScaledBorderAndShadow: yes
[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Chinese,Noto Sans CJK SC,48,&H00F6F3EC,&H00FFFFFF,&H000B0805,&H90000000,-1,0,0,0,100,100,0,0,1,2,1,2,72,72,22,1
Style: English,DejaVu Sans,30,&H00FFD2AD,&H00FFFFFF,&H000B0805,&H90000000,0,0,0,0,100,100,0,0,1,1.5,0,2,72,72,84,1
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
'''
for e in events:
 for style,key in [('Chinese','zh'),('English','en')]:ass+=f"Dialogue: 0,{stamp(e['start'])},{stamp(e['end'])},{style},,0,0,0,,{{\\fad(75,75)}}{e[key]}\n"
(R/'output/Dafeiyu-v3.3-Bilingual.ass').write_text(ass)
(R/'analysis/subtitle-events.json').write_text(json.dumps(events,ensure_ascii=False,indent=2))
expr='+'.join(f"between(t,{e['start']:.3f},{e['end']:.3f})" for e in events)
(R/'analysis/filter.txt').write_text("drawbox=x=0:y=932:w=iw:h=148:color=0x030712@0.92:t=fill:enable='"+expr+"',ass=output/Dafeiyu-v3.3-Bilingual.ass")
print('SUBTITLE_EVENTS',len(events))
