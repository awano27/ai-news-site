const vm = require('node:vm');
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const source = fs.readFileSync(path.join(__dirname, '../assets/js/analytics.js'), 'utf8');
async function simulate({host='visionhub.jp', dnt='0', id='G-LOCAL123', pathname='/presentations/day_slides/day_slide_2026_10_03.html'}={}) {
  const handlers = {}, window = {addEventListener:(event,fn)=>handlers[event]=fn};
  const document = {head:{appendChild:()=>{}}, createElement:()=>({}),
    documentElement:{scrollHeight:100,clientHeight:100,scrollTop:0}, body:{scrollHeight:100},
    addEventListener:(event,fn)=>handlers[event]=fn};
  let requests=0;
  vm.runInNewContext(source, {window,document,navigator:{doNotTrack:dnt},
    location:{hostname:host,search:'',pathname,href:`https://${host}${pathname}`}, URL,
    fetch:async()=>{requests++;return {ok:true,json:async()=>({measurement_id:id})}}});
  await new Promise(resolve=>setImmediate(resolve));
  return {window,handlers,requests};
}
(async()=>{
  for (const options of [{host:'localhost'},{host:'127.0.0.1'},{dnt:'1'}]) {
    const state=await simulate(options);assert.equal(state.requests,0);assert.equal(state.window.dataLayer,undefined);
  }
  for (const id of ['G-REPLACE_ME','G-XXXXXX','invalid']) assert.equal((await simulate({id})).window.dataLayer,undefined);
  const state=await simulate();
  state.handlers.click({target:{closest:selector=>selector==='[data-cta]'?{getAttribute:key=>key==='data-cta'?'news':'/daily-news/'}:null}});
  state.handlers.click({target:{closest:selector=>selector==='a[href]'?{href:'https://example.org/source',getAttribute:()=> 'https://example.org/source'}:null}});
  const events=state.window.dataLayer.filter(args=>args[0]==='event').map(args=>args[1]);
  for (const event of ['slide_view','scroll_depth','cta_click','outbound_click']) assert.ok(events.includes(event),event);
  assert.equal(state.requests,1);
  console.log('PASS: analytics events and localhost/DNT/placeholder guards, all requests mocked');
})().catch(error=>{console.error(error);process.exitCode=1});
