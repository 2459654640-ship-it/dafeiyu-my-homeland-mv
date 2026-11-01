const {chromium}=require('playwright');
const fs=require('fs'),http=require('http'),path=require('path');

(async()=>{
 const root=path.resolve(__dirname,'../output');
 const name=process.argv[2]||'Dafeiyu-My-Homeland-v3.3-1080p60-Master.mp4';
 const proof=name.includes('motion-check');
 const seeks=proof?[1.5,6.5,10.5,15.5,21,27]:[2,7.7,35,64.5,105,112,120,123.1,153.7,190];
 const server=http.createServer((req,res)=>{
  const request=new URL(req.url,'http://localhost');
  if(request.pathname==='/'){
   res.setHeader('Content-Type','text/html; charset=utf-8');
   res.end(`<!doctype html><meta name="viewport" content="width=device-width, initial-scale=1"><title>大肥鱼我的家乡 · v3</title><style>body{background:#050810;color:#cbd9ed;font:16px sans-serif;margin:24px}main{max-width:1280px;margin:auto}video{width:100%;display:block;background:black}button{background:#111c39;color:#d4e4ff;border:1px solid #526cb1;padding:12px;margin:8px 6px 0 0;border-radius:4px}h1{font-size:24px}</style><main><h1>大肥鱼我的家乡 · v3</h1><video src="/${encodeURIComponent(name)}" controls muted preload="metadata" playsinline></video><nav>${seeks.map(t=>`<button data-time="${t}">${t}s</button>`).join('')}</nav></main><script>for(const b of document.querySelectorAll('button'))b.onclick=()=>document.querySelector('video').currentTime=Number(b.dataset.time)</script>`);
   return;
  }
  const file=path.resolve(root,'.'+decodeURIComponent(request.pathname));
  if(!file.startsWith(root+'/')||!fs.existsSync(file)||!fs.statSync(file).isFile()){res.writeHead(404);res.end();return;}
  const size=fs.statSync(file).size,match=req.headers.range?.match(/bytes=(\d+)-(\d*)/);
  let start=0,end=size-1;
  if(match){start=Number(match[1]);end=match[2]?Math.min(size-1,Number(match[2])):size-1;res.statusCode=206;res.setHeader('Content-Range',`bytes ${start}-${end}/${size}`);}
  if(start>=size){res.writeHead(416);res.end();return;}
  res.setHeader('Content-Type','video/mp4');res.setHeader('Accept-Ranges','bytes');res.setHeader('Content-Length',end-start+1);
  fs.createReadStream(file,{start,end}).pipe(res);
 });
 await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
 const browser=await chromium.launch({executablePath:'/usr/bin/chromium',headless:true,args:['--no-sandbox','--disable-dev-shm-usage']});
 const result={errors:[],seeks:[],file:name};
 try{
  const page=await browser.newPage({viewport:{width:1440,height:1000}});page.on('pageerror',e=>result.errors.push(e.message));
  await page.goto(`http://127.0.0.1:${server.address().port}/`);
  await page.waitForFunction(()=>document.querySelector('video').readyState>=1);
  result.video=await page.evaluate(()=>{const v=document.querySelector('video');return {duration:v.duration,width:v.videoWidth,height:v.videoHeight,error:v.error?.message||null};});
  if(result.video.width!==1920||result.video.height!==1080||result.video.error||(!proof&&Math.abs(result.video.duration-195)>.04))throw Error('Invalid browser video metadata');
  for(const t of seeks){
   await page.click(`button[data-time="${t}"]`);
   await page.waitForFunction(t=>{const v=document.querySelector('video');return !v.seeking&&v.readyState>=2&&Math.abs(v.currentTime-t)<.1;},t);
   const frame=await page.evaluate(()=>{const v=document.querySelector('video');const c=document.createElement('canvas');c.width=160;c.height=90;const x=c.getContext('2d');x.drawImage(v,0,0,160,90);const a=x.getImageData(0,0,160,90).data;let s=0,ss=0;for(let i=0;i<a.length;i+=4){const q=(a[i]+a[i+1]+a[i+2])/3;s+=q;ss+=q*q;}const n=a.length/4;return {at:v.currentTime,mean:s/n,std:Math.sqrt(ss/n-(s/n)**2)};});
   if(frame.std<3)throw Error('Browser decoded a blank frame at '+t);
   result.seeks.push(frame);
   if(!proof&&[7.7,120,153.7].includes(t))await page.screenshot({path:path.join(root,`browser-${t}.png`)});
  }
  await page.evaluate(async()=>{const v=document.querySelector('video');v.currentTime=2;await v.play();});
  await page.waitForTimeout(600);
  result.playback=await page.evaluate(()=>{const v=document.querySelector('video');v.pause();return {time:v.currentTime,decoded:v.getVideoPlaybackQuality().totalVideoFrames};});
  if(result.playback.time<=2.1||!result.playback.decoded)throw Error('Video did not play');
  await page.setViewportSize({width:390,height:844});
  result.mobileOverflow=await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth);
  if(result.mobileOverflow||result.errors.length)throw Error('Player layout or JavaScript error');
  result.status='passed';fs.writeFileSync(path.join(root,proof?'proof-browser-validation.json':'browser-validation.json'),JSON.stringify(result,null,2));
  console.log(JSON.stringify(result));
 }finally{await browser.close();server.closeAllConnections();server.close();}
})().catch(e=>{console.error(e);process.exit(1);});
