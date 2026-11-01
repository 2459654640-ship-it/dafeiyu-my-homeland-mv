const {chromium}=require('playwright');
const fs=require('fs');
const http=require('http'),path=require('path');
(async()=>{
 const root='/workspace/ocean-of-worlds/v2/output';
 const server=http.createServer((req,res)=>{
  const name=decodeURIComponent(new URL(req.url,'http://localhost').pathname);
  const file=path.resolve(root,'.'+name);
  if(!file.startsWith(root+'/')||!fs.existsSync(file)||!fs.statSync(file).isFile()){res.writeHead(404);res.end();return;}
  const size=fs.statSync(file).size,range=req.headers.range;
  const type={'.html':'text/html; charset=utf-8','.mp4':'video/mp4','.jpg':'image/jpeg','.png':'image/png','.vtt':'text/vtt'}[path.extname(file)]||'application/octet-stream';
  const match=range?.match(/bytes=(\d+)-(\d*)/);
  let start=0,end=size-1;
  if(match){start=Number(match[1]);end=match[2]?Math.min(size-1,Number(match[2])):size-1;res.statusCode=206;res.setHeader('Content-Range',`bytes ${start}-${end}/${size}`);}
  res.setHeader('Content-Type',type);res.setHeader('Accept-Ranges','bytes');res.setHeader('Content-Length',end-start+1);
  fs.createReadStream(file,{start,end}).pipe(res);
 });
 await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
 const url=`http://127.0.0.1:${server.address().port}/review.html`;
 const browser=await chromium.launch({executablePath:'/usr/bin/chromium',headless:true,args:['--no-sandbox','--disable-dev-shm-usage']});
 try{
 const page=await browser.newPage({viewport:{width:1440,height:1060}});
 const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto(url);
 await page.waitForFunction(()=>document.querySelector('video').readyState>=1);
 await page.screenshot({path:'/workspace/ocean-of-worlds/v2/output/review-desktop.png',fullPage:true});
 const mobile=await browser.newPage({viewport:{width:390,height:844}});
 await mobile.goto(url);
 const overflow=await mobile.evaluate(()=>document.documentElement.scrollWidth>innerWidth);
 await mobile.screenshot({path:'/workspace/ocean-of-worlds/v2/output/review-mobile.png',fullPage:true});
 const current=await page.evaluate(()=>{
  const v=document.querySelector('video');return {duration:v.duration,width:v.videoWidth,height:v.videoHeight,error:v.error?.message||null};
 });
 console.log(JSON.stringify({errors,mobileOverflow:overflow,video:current}));
 if(errors.length||overflow)throw new Error('Player layout or JS failure');
 if(current.duration!==195||current.width!==1920||current.height!==1080||current.error)throw new Error('Browser could not load the full MV');
 await page.click('button[data-time="139.78"]');
 await page.waitForFunction(()=>Math.abs(document.querySelector('video').currentTime-139.78)<2);
 console.log('CHAPTER_SEEK_PASSED');
 }finally{await browser.close();server.closeAllConnections();server.close();}
})().catch(e=>{console.error(e);process.exit(1);});
