from pathlib import Path

p = Path('presentations/assets/presentations.js')
lines = p.read_text(encoding='utf-8', errors='ignore').splitlines()
for i, line in enumerate(lines):
    if 'ntt-slide-meta' in line:
        lines[i] = '            <div class="ntt-slide-meta">???????????????</div>'
    if 'day_slides_index.html' in line and 'ntt-card' in line:
        lines[i] = '      host.innerHTML = \'<div class="ntt-card">?????????????????<a class="ntt-inline" href="day_slides_index.html">?????</a></div>\';'
Path('presentations/assets/presentations.js').write_text('\n'.join(lines)+'\n', encoding='utf-8')
print('patched')
