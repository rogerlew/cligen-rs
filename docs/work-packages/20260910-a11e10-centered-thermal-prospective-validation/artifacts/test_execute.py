#!/usr/bin/env python3
import importlib.util,json,sys,unittest
from pathlib import Path
P=Path(__file__).with_name('execute.py');S=importlib.util.spec_from_file_location('a11e10_tested',P);M=importlib.util.module_from_spec(S);sys.modules[S.name]=M;S.loader.exec_module(M)
class Tests(unittest.TestCase):
 def test_manifest_and_fresh_burns(self):M.validate(json.loads(M.MANIFEST.read_text()))
 def test_seed_vectors_are_deterministic_and_separated(self):
  a=M.seed('az026481','a11_centered_balanced_thermal_rank1_v1','0x59b34a8f107dc2e1',0);self.assertEqual(a,M.seed('az026481','a11_centered_balanced_thermal_rank1_v1','0x59b34a8f107dc2e1',0));self.assertNotEqual(a,M.seed('az026481','a11_centered_balanced_thermal_rank1_v1','0x59b34a8f107dc2e1',1))
 def test_summary_gate(self):
  rows=[{'faithful_metrics':{k:1.0 for k in M.METRICS},'candidate_metrics':{k:(.8 if k=='annual_temperature_dispersion_error' else 1.0) for k in M.METRICS}} for _ in range(3)];self.assertTrue(M.summarize(rows,{'annual_max':.9,'noninferiority_max':1.05,'improvement_fraction_min':1/3})['passes'])
if __name__=='__main__':unittest.main()
