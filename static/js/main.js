// mobile menu
const burger=document.getElementById('burger'),links=document.getElementById('links');
if(burger)burger.onclick=()=>links.classList.toggle('open');

// scroll reveal
const io=new IntersectionObserver(es=>es.forEach(e=>{if(e.isIntersecting){e.target.classList.add('in');io.unobserve(e.target)}}),{threshold:.15});
document.querySelectorAll('.reveal').forEach(el=>io.observe(el));

// count-up numbers
document.querySelectorAll('[data-count]').forEach(el=>{
  const end=parseFloat(el.dataset.count),dec=(el.dataset.count.split('.')[1]||'').length,suf=el.dataset.suffix||'';
  new IntersectionObserver((es,o)=>{if(es[0].isIntersecting){o.disconnect();const t0=performance.now();
    (function f(t){const p=Math.min((t-t0)/1400,1);el.textContent=(end*(1-Math.pow(1-p,3))).toFixed(dec)+suf;if(p<1)requestAnimationFrame(f)})(t0)}}).observe(el);
});

// hero slideshow: plays once, no looping
(function(){
  const hero=document.getElementById('hero');if(!hero)return;
  const slides=[...hero.querySelectorAll('.slide')],dots=[...hero.querySelectorAll('.dot')];
  const secs=parseFloat(hero.dataset.seconds||6);hero.style.setProperty('--dur',secs+'s');
  let i=0,timer=null;
  function show(n){
    i=Math.max(0,Math.min(n,slides.length-1));
    slides.forEach((s,k)=>s.classList.toggle('active',k===i));
    dots.forEach((d,k)=>{d.classList.remove('active','done','stopped');
      if(k<i)d.classList.add('done');
      if(k===i){void d.offsetWidth;d.classList.add('active');if(i===slides.length-1)d.classList.add('stopped')}});
    clearTimeout(timer);
    if(i<slides.length-1)timer=setTimeout(()=>show(i+1),secs*1000);
    const r=document.getElementById('restart');if(r)r.style.visibility=i===slides.length-1?'visible':'hidden';
  }
  document.getElementById('next').onclick=()=>show(i+1);
  document.getElementById('prev').onclick=()=>show(i-1);
  dots.forEach((d,k)=>d.onclick=()=>show(k));
  const r=document.getElementById('restart');if(r)r.onclick=()=>show(0);
  // preload then start
  Promise.all(slides.map(s=>new Promise(res=>{const u=s.dataset.img;if(!u||u.startsWith('PASTE'))return res();
    s.querySelector('.bg').style.backgroundImage=`url("${u}")`;const im=new Image();im.onload=im.onerror=res;im.src=u}))).then(()=>show(0));
  show(0);
})();

// password toggle
document.querySelectorAll('.pw button').forEach(b=>b.onclick=()=>{const i=b.previousElementSibling;i.type=i.type==='password'?'text':'password'});

// predict: scanning overlay + example chips
const pf=document.getElementById('predForm');
if(pf){pf.addEventListener('submit',()=>document.getElementById('scan').classList.add('show'));
  document.querySelectorAll('[data-fill]').forEach(b=>b.onclick=()=>{const i=document.getElementById('urlInput');i.value=b.dataset.fill;i.focus()})}

// dashboard filter + delete confirm
const q=document.getElementById('q');
if(q)q.oninput=()=>document.querySelectorAll('tbody tr').forEach(r=>r.style.display=r.textContent.toLowerCase().includes(q.value.toLowerCase())?'':'none');
document.querySelectorAll('form[data-confirm]').forEach(f=>f.addEventListener('submit',e=>{if(!confirm(f.dataset.confirm))e.preventDefault()}));

// result: gauge animation + filters
const ring=document.querySelector('.ring');
if(ring){const v=parseFloat(ring.dataset.v);let c=0;const num=ring.querySelector('.n');
  const t=setInterval(()=>{c=Math.min(c+v/45,v);ring.style.setProperty('--v',c);num.textContent=c.toFixed(0)+'%';if(c>=v){clearInterval(t);num.textContent=v.toFixed(1)+'%'}},18)}
document.querySelectorAll('.filters button').forEach(b=>b.onclick=()=>{
  document.querySelectorAll('.filters button').forEach(x=>x.classList.remove('on'));b.classList.add('on');
  const f=b.dataset.f;document.querySelectorAll('.fcard').forEach(c=>c.style.display=(f==='all'||c.dataset.s===f||c.dataset.g===f)?'':'none')});
