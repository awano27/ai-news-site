const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const html = fs.readFileSync(require('node:path').join(__dirname, '../index.html'), 'utf8');
const scripts = [...html.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/g)].map(m => m[1]);
function element(attrs = {}) {
  const classes = new Set();
  return { attrs, textContent: '', innerHTML: '', inert: false, handlers: {}, style: {},
    classList: { toggle(k, on) { on ? classes.add(k) : classes.delete(k); }, remove(k) { classes.delete(k); }, contains(k) { return classes.has(k); } },
    getAttribute(k) { return this.attrs[k] || null; }, setAttribute(k,v) { this.attrs[k]=v; }, removeAttribute(k) { delete this.attrs[k]; },
    addEventListener(k,f) { this.handlers[k]=f; }, focus() { this.owner.activeElement=this; },
    querySelectorAll() { return []; }, contains(el) { return el===this; }
  };
}
function loadData({ latest = null, builtDate = '2026-10-09', slideDate = null } = {}) {
  const grid=element({'data-news-date':builtDate}); grid.innerHTML='<a class="cat-card">Verified static card</a>';
  const hero=slideDate ? element({href:'presentations/day_slides/day_slide_'+slideDate.replaceAll('-','_')+'.html'}) : null;
  const doc={ getElementById(id) { return id==='catGrid' ? grid : id==='heroSlideBtn' ? hero : null; }, querySelectorAll() { return []; } };
  const code=scripts.find(s=>s.includes('var LATEST_JSON')).replace(/\}\)\(\);\s*$/, 'globalThis.api={latestDate,latestForDate,renderCategories};})();');
  const c={document:doc, fetch:(url)=> latest ? Promise.resolve({ok:true,json:()=>Promise.resolve(url==='news/latest.json'?latest:[]),text:()=>Promise.resolve('')}) : Promise.reject(new Error('offline')), Date, console}; vm.createContext(c);vm.runInContext(code,c);return {api:c.api,grid};
}
test('news_date takes priority over slide/generated date',()=>{
 const {api}=loadData();assert.equal(api.latestDate({news_date:'2026-10-09',generated_at:'2026-10-08T09:00:00+09:00'}),'2026-10-09');
});
test('failed or rejected fetch retains verified static category cards',()=>{
 const {api,grid}=loadData();const before=grid.innerHTML;api.renderCategories(null);assert.equal(grid.innerHTML,before);
 api.renderCategories({sections:{}});assert.equal(grid.innerHTML,before);
});
test('category source attributes are escaped',()=>{
 const {api,grid}=loadData();api.renderCategories({sections:{tech:[{title:'ニュース',source:{url:'https://example.org/" onclick="alert(1)',name:'出典'}}]}});
 assert.ok(!grid.innerHTML.includes('href="https://example.org/" onclick="'));assert.ok(grid.innerHTML.includes('&quot;'));
});
function loadMenu(width=1180) {
 const btn=element({'aria-expanded':'false'}),nav=element(),main=element(),footer=element(),brand=element(),cta=element(),skip=element();
 const links=Array.from({length:5},(_,i)=>element({href:'link'+i}));
 nav.querySelectorAll=()=>links;nav.contains=e=>e===nav||links.includes(e);
 const doc={activeElement:btn,body:element(),handlers:{},querySelector(sel){return sel==='.nav-toggle'?btn:null;},getElementById(id){return id==='globalNav'?nav:null;},querySelectorAll(){return [main,footer,brand,cta,skip];},addEventListener(k,f){this.handlers[k]=f;}};
 for(const el of [btn,nav,main,footer,brand,cta,skip,...links])el.owner=doc;
 const win={innerWidth:width,handlers:{},matchMedia(){return {matches:win.innerWidth<=1180};},addEventListener(k,f){this.handlers[k]=f;}};
 const c={document:doc,window:win,console};vm.createContext(c);vm.runInContext(scripts.find(s=>s.includes("var btn = document.querySelector('.nav-toggle')")),c);
 const key=(key,shiftKey=false)=>{const e={key,shiftKey,preventDefault(){this.prevented=true;}};doc.handlers.keydown(e);return e;};
 return {btn,nav,main,footer,brand,cta,skip,links,doc,win,key};
}
test('menu opening focuses first link and makes covered page inert',()=>{
 const m=loadMenu();m.btn.handlers.click();assert.equal(m.doc.activeElement,m.links[0]);assert.equal(m.main.inert,true);assert.equal(m.footer.inert,true);
});
test('menu Tab and Shift+Tab cycle through links and close toggle',()=>{
 const m=loadMenu();m.btn.handlers.click();m.links[4].focus();assert.equal(m.key('Tab').prevented,true);assert.equal(m.doc.activeElement,m.btn);
 assert.equal(m.key('Tab').prevented,true);assert.equal(m.doc.activeElement,m.links[0]);
 assert.equal(m.key('Tab',true).prevented,true);assert.equal(m.doc.activeElement,m.btn);
});
test('Escape restores focus, releases inert, and supports reopening',()=>{
 const m=loadMenu();m.btn.handlers.click();m.key('Escape');assert.equal(m.doc.activeElement,m.btn);assert.equal(m.main.inert,false);assert.equal(m.btn.getAttribute('aria-expanded'),'false');
 m.btn.handlers.click();assert.equal(m.doc.activeElement,m.links[0]);m.key('Escape');assert.equal(m.footer.inert,false);
});
test('resize keeps menu at 1180 and closes above same CSS breakpoint',()=>{
 const m=loadMenu();m.btn.handlers.click();m.win.handlers.resize();assert.equal(m.btn.getAttribute('aria-expanded'),'true');
 m.win.innerWidth=1181;m.win.handlers.resize();assert.equal(m.btn.getAttribute('aria-expanded'),'false');assert.equal(m.main.inert,false);
});
test('menu close preserves pre-existing inert state',()=>{
 const m=loadMenu();m.main.inert=true;m.btn.handlers.click();m.key('Escape');assert.equal(m.main.inert,true);
});
test('all-slide CTA uses canonical list and search promises match destinations',()=>{
 assert.ok(!html.includes('href="presentations/day_slides_list.html">すべてのスライド'));
 assert.ok(!html.includes('キーワードや日付で、Daily News'));
 assert.ok(/href="presentations\/news_archive.html"[^>]*>日付/.test(html));
});

for (const newsDate of ['2026-99-99','2026-02-30','not-a-date',null]) {
 test('malformed explicit news date never overwrites static content: '+newsDate, async()=>{
  const {grid}=loadData({slideDate:'2026-10-09',latest:{news_date:newsDate,generated_at:'2026-10-10T09:00:00+09:00',sections:{tech:[{title:'Untrusted fetched content',source:{url:'https://example.test'}}]}}});
  await new Promise(setImmediate);assert.ok(grid.innerHTML.includes('Verified static card'));
 });
}
test('integrated rendering uses Oct9 news even with Oct8 generated timestamp and Oct10 slide', async()=>{
 const {grid}=loadData({slideDate:'2026-10-10',latest:{news_date:'2026-10-09',generated_at:'2026-10-08T09:00:00+09:00',sections:{tech:[{title:'Verified Oct9 news',source:{url:'https://example.test'}}]}}});
 await new Promise(setImmediate);assert.ok(grid.innerHTML.includes('Verified Oct9 news'));
});
test('stale fetched news retains more recent static cards', async()=>{
 const {grid}=loadData({slideDate:'2026-10-09',latest:{news_date:'2026-10-08',sections:{tech:[{title:'Older content',source:{url:'https://example.test'}}]}}});
 await new Promise(setImmediate);assert.ok(grid.innerHTML.includes('Verified static card'));
});
