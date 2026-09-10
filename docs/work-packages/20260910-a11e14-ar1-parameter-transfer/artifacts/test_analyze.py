#!/usr/bin/env python3
import importlib.util,json,sys,unittest
from pathlib import Path
import numpy as np
P=Path(__file__).with_name('analyze.py');S=importlib.util.spec_from_file_location('a11e14_tested',P);M=importlib.util.module_from_spec(S);sys.modules[S.name]=M;S.loader.exec_module(M)
class Tests(unittest.TestCase):
 def test_manifest(self):M.validate(json.loads(M.MANIFEST.read_text()))
 def test_phi_and_clip(self):
  w=np.full(12,1/12);x=np.arange(16,dtype=float);self.assertAlmostEqual(M.phi(np.repeat(x[:,None],12,axis=1),w,[-.75,.75]),.75)
 def test_halves_are_deterministic(self):self.assertEqual(M.half('alpha'),M.half('alpha'));self.assertIn(M.half('beta'),(0,1))
 def test_summary(self):
  rows=[{'station_id':'s','faithful_metrics':{k:1.0 for k in M.METRICS},'candidate_metrics':{k:(.8 if k=='annual_temperature_dispersion_error' else 1.0) for k in M.METRICS}} for _ in range(3)];self.assertTrue(M.summary(rows,{'annual_max':.9,'noninferiority_max':1.05,'improvement_fraction_min':1/3,'station_annual_max':1.25},True)['passes'])
if __name__=='__main__':unittest.main()
