#!/usr/bin/env python3
import importlib.util, sys, unittest
from pathlib import Path
import numpy as np
P=Path(__file__).with_name('execute.py'); S=importlib.util.spec_from_file_location('a11e9_tested',P); M=importlib.util.module_from_spec(S); sys.modules[S.name]=M; S.loader.exec_module(M)
class Tests(unittest.TestCase):
 def test_centering_is_chronological_binary64(self):
  x=[float(i) for i in range(16)]; y=M.centered(x); self.assertEqual(y[0],-7.5); self.assertEqual(sum(y),0.0)
 def test_balancing_is_zero_sum_and_deterministic(self):
  l=np.linspace(-2,3,12); s=M.centered([0.17*i for i in range(16)]); a=M.balanced_tenths(l,s); b=M.balanced_tenths(l,s); self.assertTrue(np.array_equal(a,b)); self.assertTrue(np.array_equal(a.sum(axis=0),np.zeros(12,dtype=np.int64)))
 def test_manifest_is_strictly_dependency_bound(self):
  import json
  M.validate(json.loads(M.MANIFEST.read_text()))
if __name__=='__main__': unittest.main()
