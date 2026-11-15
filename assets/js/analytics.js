/* VisionHub: GA4 with persistent opt-out. No country lookup or popup. */
(function () {
  'use strict';
  if (window.__AIHUB_ANALYTICS_LOADED) return;
  window.__AIHUB_ANALYTICS_LOADED = true;
  var KEY = 'visionhub.analytics.optout.v1', LEGACY_KEY = 'visionhub.analytics.v1';
  var id = '', started = false, choice = null;
  var blocked = navigator.doNotTrack === '1' || navigator.globalPrivacyControl === true;
  var host = location.hostname;
  if (host !== 'visionhub.jp' && host !== 'www.visionhub.jp') return;
  function saved() {
    try {
      if (window.localStorage.getItem(KEY) === 'denied') return 'denied';
      var legacy = JSON.parse(window.localStorage.getItem(LEGACY_KEY));
      if (legacy && legacy.value === 'denied' && legacy.expires > Date.now()) return 'denied';
      return 'enabled';
    } catch (_) { return 'denied'; }
  }
  choice = saved();
  function permitted() { return !blocked && choice !== 'denied' && saved() !== 'denied'; }
  function remember(value) {
    try {
      window.localStorage.setItem(KEY, value);
      window.localStorage.removeItem(LEGACY_KEY);
      choice = value; return true;
    } catch (_) { choice = 'denied'; return false; }
  }
  // Only public static content routes; never query strings, fragments or arbitrary user paths.
  function safePath() {
    var p = location.pathname;
    if (p === '/' || /^\/(?:index|about|contact|privacy-policy)\.html$/.test(p)) return p;
    if (/^\/presentations\/day_slides\/day_slide_\d{4}_\d{2}_\d{2}\.html$/.test(p)) return p;
    if (/^\/daily-news\/archive\/\d{4}-\d{2}-\d{2}\.html$/.test(p)) return p;
    if (/^\/presentations\/(?:index|news_archive|day_slides_list)\.html$/.test(p)) return p;
    return '/other-public-page';
  }
  function send(name, params) {
    if (!permitted() || !started || saved() === 'denied') return;
    window.gtag('event', name, params);
  }
  function clearCookies() {
    document.cookie.split(';').forEach(function (item) {
      var name = item.split('=')[0].trim();
      if (!/^_ga(?:_|$)/.test(name)) return;
      ['', '; domain=' + host, '; domain=.visionhub.jp', '; domain=visionhub.jp'].forEach(function (domain) {
        document.cookie = name + '=; Max-Age=0; path=/' + domain + '; SameSite=Lax';
      });
    });
  }
  function node(tag, text, parent) {
    var n = document.createElement(tag); n.textContent = text || ''; if (parent) parent.appendChild(n); return n;
  }
  function ui() {
    var footer=node('div','',document.body);
    footer.setAttribute('role','contentinfo');
    footer.style.cssText='position:fixed;bottom:4px;right:8px;z-index:10000;max-width:calc(100vw - 16px);padding:3px 8px;background:#f8fafc;color:#334155;font:11px/1.5 sans-serif;border-radius:4px';
    node('span','Google アナリティクスによるアクセス解析について： ',footer);
    var link=node('a','プライバシー・計測の停止',footer);
    link.href='/privacy-policy.html#analytics';link.style.color='#174ea6';
    if(location.pathname !== '/privacy-policy.html')return;
    var controls=node('div','',document.getElementById('analytics-controls') || footer);
    var status=node('p',blocked?'このブラウザの追跡拒否設定により計測は停止中です。':choice==='denied'?'このブラウザでは計測を停止しています。':'このブラウザでは計測が有効です。',controls);
    function action(label,value) {
      var button=node('button',label,controls);button.type='button';button.style.cssText='margin:6px;padding:10px 16px;cursor:pointer';
      button.addEventListener('click',function(){
        var persisted = remember(value);
        if(value==='denied'){if(id)window['ga-disable-'+id]=true;clearCookies();}
        if(persisted) location.reload();
        else { if(id)window['ga-disable-'+id]=true;clearCookies();status.textContent='このページの計測を停止しましたが、設定を保存できませんでした。以降のページも停止するにはブラウザの追跡拒否設定またはGoogleのオプトアウトアドオンをご利用ください。'; }
      });
    }
    action('このブラウザで計測を停止する','denied');
    if(!blocked)action('計測を再開する','enabled');
  }
  function start() {
    if (started || !id || !permitted()) return;
    started = true; window['ga-disable-'+id] = false;
    window.dataLayer = window.dataLayer || [];
    window.gtag = function(){window.dataLayer.push(arguments);};
    window.gtag('consent','default',{ad_storage:'denied',ad_user_data:'denied',ad_personalization:'denied'});
    // Apply before initialization: newer Google tags can initialize destinations
    // before processing per-destination config. Do not rely on config alone.
    window.gtag('set',{send_page_view:false,allow_google_signals:false,allow_ad_personalization_signals:false,
      allow_enhanced_conversions:false,page_location:'https://visionhub.jp'+safePath(),
      page_referrer:'',page_title:'VisionHub',cookie_expires:15552000,cookie_update:false});
    window.gtag('js',new Date());
    window.gtag('config',id,{send_page_view:false,allow_google_signals:false,allow_ad_personalization_signals:false,
      page_location:'https://visionhub.jp'+safePath(),page_referrer:'',page_title:'VisionHub',cookie_expires:15552000,cookie_update:false});
    var s=node('script');s.async=true;s.src='https://www.googletagmanager.com/gtag/js?id='+encodeURIComponent(id);document.head.appendChild(s);
    send('page_view',{page_location:'https://visionhub.jp'+safePath(),page_referrer:'',page_title:'VisionHub'});
    var m=/day_slide_(\d{4})_(\d{2})_(\d{2})\.html$/.exec(safePath());
    if(m)send('slide_view',{slide_date:m[1]+'-'+m[2]+'-'+m[3]});
    var depths={};
    function depth(){var d=document.documentElement,b=document.body;var height=Math.max(d.scrollHeight,b.scrollHeight||0)-(window.innerHeight||d.clientHeight);var pct=height<=0?100:Math.min(100,Math.round(((window.pageYOffset||d.scrollTop||0)/height)*100));[25,50,75,100].forEach(function(n){if(pct>=n&&!depths[n]){depths[n]=true;send('scroll_depth',{percent:n,percent_scrolled:n});}});}
    window.addEventListener('scroll',depth,{passive:true});depth();
    document.addEventListener('click',function(e){var t=e.target;if(!t||!t.closest)return;var a=t.closest('a[href]');if(!a)return;try{var u=new URL(a.href,location.href);if(!/^https?:$/.test(u.protocol))return;if(t.closest('[data-cta]'))send('cta_click',{link_type:u.hostname===host?'internal':'external'});else if(u.hostname!==host)send('outbound_click',{link_type:'external'});}catch(_){} });
  }
  window.addEventListener('storage',function(e){if((e.key===KEY || e.key===LEGACY_KEY || e.key===null) && saved()==='denied'){choice='denied';if(id)window['ga-disable-'+id]=true;clearCookies();if(started)location.reload();}});
  function init(){ui();if(!permitted())return;fetch('/assets/analytics-config.json',{cache:'no-store'}).then(function(r){return r.ok?r.json():null;}).then(function(c){if(!c||!/^G-[A-Z0-9]{6,}$/.test(c.optout_measurement_id)||/REPLACE|XXXX/.test(c.optout_measurement_id))return;id=c.optout_measurement_id;start();}).catch(function(){});}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
})();
