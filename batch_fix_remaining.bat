@echo off
echo Applying link fixes to remaining slides...
cd "C:\Users\yoshitaka\ai-news-site"

echo.
echo Fixing 08/15...
python -c "import re; path='presentations/day_slides/day_slide_2025_08_15.html'; content=open(path,'r',encoding='utf-8').read(); content=re.sub(r'(fragments: false.*?)\n([ ]*)\}',r'\1,\n\2            mouseWheel: false,\n\2            hideInactiveCursor: false,\n\2            disableLayout: true\n\2}',content,1,re.DOTALL) if 'mouseWheel: false' not in content else content; open(path,'w',encoding='utf-8').write(content); print('Done')"

echo.
echo Fixing 08/16...
python -c "import re; path='presentations/day_slides/day_slide_2025_08_16.html'; content=open(path,'r',encoding='utf-8').read(); content=re.sub(r'(fragments: false.*?)\n([ ]*)\}',r'\1,\n\2            mouseWheel: false,\n\2            hideInactiveCursor: false,\n\2            disableLayout: true\n\2}',content,1,re.DOTALL) if 'mouseWheel: false' not in content else content; open(path,'w',encoding='utf-8').write(content); print('Done')"

echo.
echo Fixing 08/17...
python -c "import re; path='presentations/day_slides/day_slide_2025_08_17.html'; content=open(path,'r',encoding='utf-8').read(); content=re.sub(r'(fragments: false.*?)\n([ ]*)\}',r'\1,\n\2            mouseWheel: false,\n\2            hideInactiveCursor: false,\n\2            disableLayout: true\n\2}',content,1,re.DOTALL) if 'mouseWheel: false' not in content else content; open(path,'w',encoding='utf-8').write(content); print('Done')"

echo.
echo Fixing 08/18...
python -c "import re; path='presentations/day_slides/day_slide_2025_08_18.html'; content=open(path,'r',encoding='utf-8').read(); content=re.sub(r'(fragments: false.*?)\n([ ]*)\}',r'\1,\n\2            mouseWheel: false,\n\2            hideInactiveCursor: false,\n\2            disableLayout: true\n\2}',content,1,re.DOTALL) if 'mouseWheel: false' not in content else content; open(path,'w',encoding='utf-8').write(content); print('Done')"

echo.
echo All slides fixed!
pause