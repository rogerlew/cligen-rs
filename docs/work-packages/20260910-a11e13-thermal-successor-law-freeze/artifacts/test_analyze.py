#!/usr/bin/env python3
import importlib.util,json,sys,unittest
from pathlib import Path
import numpy as np
P=Path(__file__).with_name('analyze.py');S=importlib.util.spec_from_file_location('a11e13_tested',P);M=importlib.util.module_from_spec(S);sys.modules[S.name]=M;S.loader.exec_module(M)
class Tests(unittest.TestCase):
 def test_manifest(self):M.validate(json.loads(M.MANIFEST.read_text()))
 def test_ar1_is_centered_normalized_and_deterministic(self):
  a=M.ar1([float(i+1) for i in range(16)],.4);b=M.ar1([float(i+1) for i in range(16)],.4);self.assertEqual(a,b);self.assertAlmostEqual(sum(a),0);self.assertAlmostEqual(float(np.std(a,ddof=1)),1)
 def test_summary(self):
  rows=[{'faithful_metrics':{k:1.0 for k in M.METRICS},'candidate_metrics':{k:(.8 if k=='annual_temperature_dispersion_error' else 1.0) for k in M.METRICS}} for _ in range(3)];self.assertTrue(M.summary(rows,{'annual_max':.9,'noninferiority_max':1.05,'improvement_fraction_min':1/3})['passes'])
if __name__=='__main__':unittest.main()
