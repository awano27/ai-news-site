import importlib.util,json,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class DiscoveryTest(unittest.TestCase):
 def test_refresh_from_retained_daily(self):
  path=ROOT/'scripts/refresh_machine_discovery.py'
  self.assertTrue(path.exists(),'machine endpoints have no publication refresh')
  spec=importlib.util.spec_from_file_location('refresh',path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
  with tempfile.TemporaryDirectory() as td:
   r=Path(td)
   for d in ['public-pages/news/daily','news','presentations/day_slides','config','assets']: (r/d).mkdir(parents=True)
   (r/'public-pages/news/daily/2026-11-14.json').write_text(json.dumps({'date':'2026-11-14','items':[{'title':'actual title','summary':'actual summary','url':'https://example.com','category':'Research','integrity_status':'corrected'}]}))
   (r/'presentations/day_slides/day_slide_2026_11_14.html').write_text('<title>Today</title>')
   (r/'llms.txt').write_text("# Docs\n- [Today's day slide](old): stale\n")
   (r/'config/analytics.json').write_text('{"measurement_id":"G-REPLACE-ME"}')
   (r/'news/2026-11-13.json').write_text('{"highlight":{"title":"curated"},"sections":{}}')
   (r/'public-pages/news/daily/2026-11-13.json').write_text(json.dumps({'date':'2026-11-13','items':[]}))
   m.refresh(r)
   self.assertEqual(json.loads((r/'news/2026-11-13.json').read_text())['highlight']['title'],'curated')
   j=json.loads((r/'news/2026-11-14.json').read_text());self.assertEqual(j['highlight']['title'],'actual title');self.assertEqual(j['sections']['Research'][0]['integrity_status'],'corrected')
   idx=json.loads((r/'public-pages/news/archive_index.json').read_text());self.assertEqual(idx[0]['file'],'daily/2026-11-14.json');self.assertEqual(idx[0]['count'],1)
   self.assertIn('day_slide_2026_11_14.html',(r/'llms.txt').read_text())
   self.assertIsNone(json.loads((r/'assets/analytics-config.json').read_text())['measurement_id'])
   before=(r/'news/2026-11-14.json').read_bytes();m.refresh(r);self.assertEqual(before,(r/'news/2026-11-14.json').read_bytes())
if __name__=='__main__':unittest.main()
