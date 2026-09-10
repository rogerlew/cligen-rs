#!/usr/bin/env python3
import importlib.util,json,sys,unittest
from pathlib import Path
P=Path(__file__).with_name('analyze.py');S=importlib.util.spec_from_file_location('a11e12_tested',P);M=importlib.util.module_from_spec(S);sys.modules[S.name]=M;S.loader.exec_module(M)
class Tests(unittest.TestCase):
 def test_manifest(self):M.validate(json.loads(M.MANIFEST.read_text()))
 def test_common_requires_direction_and_threshold(self):
  c={'x':{'a':.6,'b':.7,'c':.8},'y':{'a':.6,'b':-.7,'c':.8},'z':{'a':.4,'b':.7,'c':.8}};self.assertEqual(M.common(c,['x','y','z'],.5),['x'])
 def test_classification(self):
  self.assertEqual(M.classify([],[],{'a':['x'],'b':['y']},[]),'STATION_SPECIFIC_NO_COMMON_LOADING_RULE');self.assertEqual(M.classify(['x'],[],{},[]),'COMMON_LOADING_MAGNITUDE_ASSOCIATION')
if __name__=='__main__':unittest.main()
