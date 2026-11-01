from pathlib import Path
import subprocess,sys
R=Path(__file__).resolve().parents[1]
for p in ['output','analysis']:(R/p).mkdir(exist_ok=True)
subprocess.run([sys.executable,str(R/'source/subtitles.py')],check=True)
base=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else R.parent/'v3.2/output/Dafeiyu-My-Homeland-v3.2-Native.mp4'
assert base.exists(),'请先运行 v3.2/source/render_complete.py，或通过参数指定 v3.2 完整视频。'
subprocess.run(['ffmpeg','-y','-filter_threads','1','-threads','1','-i',str(base),'-filter_script:v','analysis/filter.txt','-c:v','libx264','-preset','veryfast','-crf','13','-maxrate','45M','-bufsize','90M','-threads','3','-pix_fmt','yuv420p','-c:a','copy','-movflags','+faststart','output/Dafeiyu-My-Homeland-v3.4-1080p60-Master.mp4'],cwd=R,check=True)
