#!/usr/bin/env python3
"""Execute the source-bound A11E9 thermal mean-regression attribution."""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, math, os, platform, shutil, subprocess, sys, time
from pathlib import Path
from typing import Any
os.environ.update(OPENBLAS_NUM_THREADS="1",OMP_NUM_THREADS="1",MKL_NUM_THREADS="1",VECLIB_MAXIMUM_THREADS="1")
import numpy as np

ROOT=Path(__file__).resolve().parents[4]; HERE=Path(__file__).resolve().parent
MANIFEST=HERE/'execution-manifest-v1.json'; RUNTIME=ROOT/'target/a11e9-runtime'
A8=ROOT/'docs/work-packages/20260904-a11e8-deterministic-cohort-joint-foundation/artifacts'
PANEL=ROOT/'docs/work-packages/20260715-a8a-dry-regime-applicability/artifacts/panel-v1.json'
FILES={'a11e8_manifest':A8/'execution-manifest-v1.json','a11e8_contract':A8/'contract.py','a11e8_evidence':A8/'development-evidence-v1.json','a11e8_decision':A8/'development-decision-v1.json','a11e8_loading':A8/'thermal-loading-bundle-v1.json','a11e8_executor':A8/'execute.py','panel':PANEL}
METRICS=('monthly_temperature_dispersion_error','annual_temperature_dispersion_error','temperature_cross_month_correlation_rmse','annual_temperature_lag1_error','annual_temperature_low_frequency_error','monthly_temperature_mean_absolute_error_c')
NONANNUAL=tuple(x for x in METRICS if x!='annual_temperature_dispersion_error')
class Error(RuntimeError): pass
def sha(p:Path)->str: return hashlib.sha256(p.read_bytes()).hexdigest()
def canon(v:Any)->str: return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def write(p:Path,v:Any)->None:
 q=p.with_suffix(p.suffix+'.part'); q.write_text(json.dumps(v,indent=2,sort_keys=True,allow_nan=False)+'\n'); q.replace(p)
def load(name:str,p:Path)->Any:
 s=importlib.util.spec_from_file_location(name,p); m=importlib.util.module_from_spec(s); sys.modules[name]=m; s.loader.exec_module(m); return m
def centered(states:list[float])->list[float]:
 if len(states)!=16 or not all(math.isfinite(x) for x in states): raise Error('invalid states')
 mean=sum(states)/16.0
 return [x-mean for x in states]
def balanced_tenths(loading:np.ndarray,states:list[float])->np.ndarray:
 raw=np.outer(np.asarray(states,dtype=np.float64),loading)*10.0
 q=np.rint(raw).astype(np.int64)
 for month in range(12):
  while int(q[:,month].sum())!=0:
   direction=-1 if q[:,month].sum()>0 else 1
   choices=sorted(range(16),key=lambda y:(abs((q[y,month]+direction)-raw[y,month])-abs(q[y,month]-raw[y,month]),y))
   q[choices[0],month]+=direction
 return q
def metrics(precip:np.ndarray,temp:np.ndarray,obs:dict[str,Any],weights:np.ndarray,m:Any)->dict[str,float]:
 out=m.interannual_metrics(precip,temp,obs['precipitation'],obs['tmean'],weights)
 out['monthly_temperature_mean_absolute_error_c']=float(np.mean(np.abs(np.mean(temp,axis=0)-np.mean(obs['tmean'],axis=0))))
 out={k:float(out[k]) for k in METRICS}
 if not all(math.isfinite(x) and x>=0 for x in out.values()): raise Error('nonfinite metric')
 return out
def decide(rows:list[dict[str,Any]],manifest:dict[str,Any])->dict[str,Any]:
 gate=manifest['gate']; results={}
 for arm in manifest['arms'][1:]:
  ratios={k:float(np.median([r['metrics'][arm][k] for r in rows]))/max(float(np.median([r['metrics']['faithful'][k] for r in rows])),1e-12) for k in METRICS}
  improved=sum(r['metrics'][arm]['annual_temperature_dispersion_error']<r['metrics']['faithful']['annual_temperature_dispersion_error'] for r in rows)
  station={s:float(np.median([r['metrics'][arm]['annual_temperature_dispersion_error'] for r in rows if r['station_id']==s]))/max(float(np.median([r['metrics']['faithful']['annual_temperature_dispersion_error'] for r in rows if r['station_id']==s])),1e-12) for s in sorted({r['station_id'] for r in rows})}
  passed=ratios['annual_temperature_dispersion_error']<=gate['annual_max'] and all(ratios[k]<=gate['noninferiority_max'] for k in NONANNUAL) and improved/640>=gate['improvement_fraction_min'] and max(station.values())<=gate['station_annual_max']
  results[arm]={'passes':passed,'metric_median_ratios_over_faithful':ratios,'annual_improved':improved,'annual_improvement_fraction':improved/640,'station_annual_error_ratios':station}
 if results['centered_balanced_rendered']['passes']: disposition='CENTERING_REMEDY_SUPPORTED'
 elif results['centered_unquantized']['passes']: disposition='QUANTIZATION_BLOCKS_CENTERING_REMEDY'
 else: disposition='RANK_ONE_THERMAL_FORMULATION_REJECTED'
 return {'disposition':disposition,'arms':results}
def validate(manifest:dict[str,Any])->None:
 if manifest['confirmation_target_access'] is not False or len(manifest['burns'])!=32 or len(set(manifest['burns']))!=32 or len(manifest['arms'])!=5: raise Error('manifest invalid')
 for k,p in FILES.items():
  if sha(p)!=manifest['dependencies'][k]: raise Error(f'dependency drift: {k}')
def source(commit:str)->dict[str,str]:
 head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(); remote=subprocess.check_output(['git','rev-parse','origin/main'],cwd=ROOT,text=True).strip()
 if commit!=head or commit!=remote or len(commit)!=40: raise Error('source not exact origin/main')
 for p in (Path(__file__),HERE/'test_execute.py',MANIFEST,HERE.parent/'package.md',ROOT/'docs/specifications/SPEC-A11-THERMAL-MEAN-REGRESSION-ATTRIBUTION.md',ROOT/'docs/exec-plans/20260910-a11e9-thermal-mean-regression-attribution.md'):
  rel=p.relative_to(ROOT).as_posix(); blob=subprocess.check_output(['git','show',f'{commit}:{rel}'],cwd=ROOT)
  if blob!=p.read_bytes(): raise Error(f'working source differs: {rel}')
 return {'source_commit':commit,'source_tree':subprocess.check_output(['git','rev-parse',f'{commit}^{{tree}}'],cwd=ROOT,text=True).strip()}
def analyze(bundle:dict[str,Any],manifest:dict[str,Any],a8:Any,m:Any)->tuple[dict[str,Any],dict[str,Any]]:
 weights=np.asarray([31,28,31,30,31,30,31,31,30,31,30,31],dtype=np.float64); weights/=weights.sum(); rows=[]
 for rec in bundle['rows']:
  faithful=np.asarray(rec['faithful_tmean'],dtype=np.float64); precip=np.asarray(rec['faithful_precipitation'],dtype=np.float64); observed={'tmean':np.asarray(rec['observed_tmean'],dtype=np.float64),'precipitation':np.asarray(rec['observed_precipitation'],dtype=np.float64)}; loading=np.asarray(rec['loading_c']); states=rec['states']; c=centered(states)
  raw_q=np.rint(np.outer(np.asarray(states),loading)*10).astype(np.int64); cent_q=np.rint(np.outer(np.asarray(c),loading)*10).astype(np.int64); bal_q=balanced_tenths(loading,c)
  temps={'faithful':faithful,'raw_rendered':faithful+raw_q/10.0,'centered_rendered':faithful+cent_q/10.0,'centered_balanced_rendered':faithful+bal_q/10.0,'centered_unquantized':faithful+np.outer(np.asarray(c),loading)}
  rows.append({'station_id':rec['station_id'],'burn':rec['burn'],'cohort_id':rec['cohort_id'],'candidate_index':rec['candidate_index'],'state_mean':sum(states)/16.0,'raw_delta_sum_tenths':[int(x) for x in raw_q.sum(axis=0)],'centered_delta_sum_tenths':[int(x) for x in cent_q.sum(axis=0)],'balanced_delta_sum_tenths':[int(x) for x in bal_q.sum(axis=0)], 'metrics':{k:metrics(precip,v,observed,weights,m) for k,v in temps.items()}})
 if len(rows)!=640 or any(any(x!=0 for x in r['balanced_delta_sum_tenths']) for r in rows): raise Error('grid/balance failure')
 evidence={'schema_version':'a11e9-evidence-1','rows':rows}; evidence['decision']=decide(rows,manifest); evidence['confirmation_target_series_accessed']=False; evidence['evidence_sha256']=canon(evidence)
 decision={'schema_version':'a11e9-decision-1','terminal':'EXECUTED-COMPLETE',**evidence['decision'],'confirmation_authorized':False,'production_authorized':False}
 return evidence,decision
def execute(commit:str,replay:bool)->None:
 manifest=json.loads(MANIFEST.read_text()); validate(manifest)
 runtime={'python':platform.python_version(),'numpy':np.__version__,'system':platform.system(),'machine':platform.machine(),'rustc':subprocess.check_output(['rustc','--version'],text=True).strip(),'cargo':subprocess.check_output(['cargo','--version'],text=True).strip()}
 if runtime!=manifest['runtime']: raise Error(f'runtime drift {runtime}')
 src=source(commit); a8=load('a11e9_a8',A8/'execute.py'); metricmod=load('a11e9_metrics',a8.A11E5)
 bundle_path=HERE/'replay-input-bundle-v1.json'
 if replay:
  bundle=json.loads(bundle_path.read_text())
 else:
  if RUNTIME.exists(): raise Error('runtime exists')
  try:
   pred=load('a11e9_pred',a8.A11E2); pm=pred.validate_manifest(json.loads(a8.A11E2_MANIFEST.read_text())); inherited,devrows,_=pred.verify_inputs(pm); base=pred.ensure_base_loaded(); development,preflight=base.load_development(devrows); obs={x['point_id']:x for x in development}
   panel=json.loads(PANEL.read_text())['stations']; roots=manifest['cohort_roots']; RUNTIME.mkdir(parents=True)
   build=RUNTIME/'build'; subprocess.run(['cargo','build','--release','--locked','--bin','cligen','--target-dir',str(build)],cwd=ROOT,check=True); binary=build/'release/cligen'; bundle_rows=[]
   loading_by={x['station_id']:x['loading_c'] for x in json.loads((A8/'thermal-loading-bundle-v1.json').read_text())['stations']}
   station_root=Path(os.environ.get('CLIGEN_DATA_DIR',str(Path.home()/'.cache/cligen')))/'stations/us-2015/2026.07'
   for station in panel:
    sid=station['station_id']; par=station_root/f'{sid}.par'
    if sha(par)!=station['parameter_sha256']: raise Error('par drift')
    for i,burn in enumerate(manifest['burns']):
     d=RUNTIME/'runs'/sid/str(i); d.mkdir(parents=True); shutil.copyfile(par,d/'source.par'); a8.write_runspec(d/'run.yaml',burn); subprocess.run([str(binary),'run','run.yaml'],cwd=d,check=True,capture_output=True,text=True); vals=a8.parse_cli(d/'faithful.cli'); cohort=i//8; index=i%8; seed=a8.contract.derive_thermal_seed(sid,a8.contract.MODEL_ORDER[1],roots[cohort],index); states=a8.contract.annual_states(seed,16)
     bundle_rows.append({'station_id':sid,'burn':burn,'cohort_id':cohort,'candidate_index':index,'faithful_precipitation':vals[0].tolist(),'faithful_tmean':vals[1].tolist(),'observed_precipitation':obs[sid]['precipitation'].tolist(),'observed_tmean':obs[sid]['tmean'].tolist(),'loading_c':loading_by[sid],'states':states,'faithful_cli_sha256':sha(d/'faithful.cli')})
   bundle={'schema_version':'a11e9-replay-input-1','source':src,'binary_sha256':sha(binary),'inherited':inherited,'preflight':preflight,'rows':bundle_rows,'confirmation_target_series_accessed':False}; bundle['bundle_sha256']=canon(bundle); write(bundle_path,bundle)
  finally:
   if RUNTIME.exists(): shutil.rmtree(RUNTIME)
 evidence,decision=analyze(bundle,manifest,a8,metricmod); write(HERE/'development-evidence-v1.json',evidence); write(HERE/'development-decision-v1.json',decision)
 pre={'schema_version':'a11e9-preflight-1','observed':bundle['preflight'],'station_count':20,'record_count':640,'confirmation_target_series_accessed':False}; write(HERE/'calendar-missingness-preflight-v1.json',pre)
 receipt={'schema_version':'a11e9-execution-receipt-1','mode':'replay' if replay else 'execute',**src,'runtime':runtime,'bundle_sha256':sha(bundle_path),'evidence_sha256':sha(HERE/'development-evidence-v1.json'),'decision_sha256':sha(HERE/'development-decision-v1.json'),'preflight_sha256':sha(HERE/'calendar-missingness-preflight-v1.json'),'confirmation_target_series_accessed':False}; write(HERE/'execution-receipt-v1.json',receipt)
def main()->None:
 p=argparse.ArgumentParser(); p.add_argument('--source-commit'); p.add_argument('--execute',action='store_true'); p.add_argument('--replay',action='store_true'); p.add_argument('--validate-manifest',action='store_true'); a=p.parse_args(); m=json.loads(MANIFEST.read_text()); validate(m)
 if a.validate_manifest: print(canon(m)); return
 if not a.source_commit or a.execute==a.replay: p.error('choose exactly one of --execute/--replay with --source-commit')
 execute(a.source_commit,a.replay)
if __name__=='__main__': main()
