#!/usr/bin/env python3
import importlib.util,json,sys,unittest
from pathlib import Path
P=Path(__file__).with_name('analyze.py');S=importlib.util.spec_from_file_location('a11e11_tested',P);M=importlib.util.module_from_spec(S);sys.modules[S.name]=M;S.loader.exec_module(M)
class Tests(unittest.TestCase):
 def test_manifest_authenticates_failed_surfaces(self):M.validate(json.loads(M.MANIFEST.read_text()))
 def test_classification_priority(self):
  self.assertEqual(M.classify([{'denominator_sensitive':True,'broad':False,'station_concentrated':False}]),'RATIO_DENOMINATOR_INSTABILITY')
  self.assertEqual(M.classify([{'denominator_sensitive':False,'broad':True,'station_concentrated':False}]),'BROAD_IID_TEMPORAL_INSTABILITY')
  self.assertEqual(M.classify([{'denominator_sensitive':False,'broad':False,'station_concentrated':True}]),'STATION_CONCENTRATED_LOADING_INSTABILITY')
if __name__=='__main__':unittest.main()
