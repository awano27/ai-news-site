(function(){
  function pageFooter(){
    var sec = document.querySelectorAll('.reveal .slides > section');
    var total = sec.length;
    sec.forEach(function(s, i){
      var f = s.querySelector('.footer');
      if(!f){ f = document.createElement('div'); f.className='footer'; s.appendChild(f); }
      f.textContent = 'Page ' + (i+1) + ' / ' + total + '  © AI Intelligence';
    });
  }
  function scoreChart(){
    var c = document.getElementById('scoreChart'); if(!c || !window.Chart) return;
    var k1 = Number(c.dataset.k1||0)||0, k2 = Number(c.dataset.k2||0)||0, k3 = Number(c.dataset.k3||0)||0;
    new Chart(c.getContext('2d'), { type:'bar', data:{ labels:['K1','K2','K3'], datasets:[{ label:'Score', data:[k1,k2,k3], backgroundColor:['#3b82f6','#10b981','#f59e0b'] }] }, options:{ responsive:true, scales:{ y:{ beginAtZero:true, max:100 } }, plugins:{ legend:{ display:false } } });
  }
  if (document.readyState==='loading') document.addEventListener('DOMContentLoaded', function(){ pageFooter(); scoreChart(); }, {once:true});
  else { pageFooter(); scoreChart(); }
})();
