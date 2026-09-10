#!/usr/bin/env python3
"""Execute A11E10 fresh centered-thermal prospective validation."""
from __future__ import annotations
import argparse,hashlib,importlib.util,json,math,os,platform,shutil,subprocess,sys
from pathlib import Path
from typing import Any
os.environ.update(OPENBLAS_NUM_THREADS="1",OMP_NUM_THREADS="1",MKL_NUM_THREADS="1",VECLIB_MAXIMUM_THREADS="1")
import numpy as np
ROOT=Path(__file__).resolve().parents[4]; HERE=Path(__file__).resolve().parent; MANIFEST=HERE/'execution-manifest-v1.json'; RUN=ROOT/'target/a11e10-runtime'
A8=ROOT/'docs/work-packages/20260904-a11e8-deterministic-cohort-joint-foundation/artifacts'; A9=ROOT/'docs/work-packages/20260910-a11e9-thermal-mean-regression-attribution/artifacts'; PANEL=ROOT/'docs/work-packages/20260715-a8a-dry-regime-applicability/artifacts/panel-v1.json'
DEPS={'a11e8_executor':A8/'execute.py','a11e8_contract':A8/'contract.py','a11e9_manifest':A9/'execution-manifest-v1.json','a11e9_executor':A9/'execute.py','a11e9_decision':A9/'development-decision-v1.json','panel':PANEL}
METRICS=('monthly_temperature_dispersion_error','annual_temperature_dispersion_error','temperature_cross_month_correlation_rmse','annual_temperature_lag1_error','annual_temperature_low_frequency_error','monthly_temperature_mean_absolute_error_c'); NONANNUAL=tuple(x for x in METRICS if x!='annual_temperature_dispersion_error'); DOMAIN=b'cligen-rs/a11e10/centered-thermal-state-v1\0'
class Error(RuntimeError): pass
def sha(p:Path)->str: return hashlib.sha256(p.read_bytes()).hexdigest()
def canon(v:Any)->str:return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def write(p:Path,v:Any)->None:q=p.with_suffix(p.suffix+'.part');q.write_text(json.dumps(v,indent=2,sort_keys=True,allow_nan=False)+'\n');q.replace(p)
def load(n:str,p:Path)->Any:s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);sys.modules[n]=m;s.loader.exec_module(m);return m
def seed(station:str,model:str,root:str,index:int)->int:
 pre=DOMAIN+station.encode()+b'\0'+model.encode()+b'\0'+int(root,16).to_bytes(8,'big')+index.to_bytes(4,'big');return int.from_bytes(hashlib.sha256(pre).digest()[:8],'big')
def validate(m:dict[str,Any])->None:
 burns=[b for c in m['cohorts'] for b in c['burns']]; old=set(json.loads((A8/'execution-manifest-v1.json').read_text())['cohorts'][i]['burns'][j] for i in range(4) for j in range(8))
 if m['confirmation_target_access'] is not False or len(burns)!=32 or len(set(burns))!=32 or set(burns)&old or m['seed_domain']!=DOMAIN[:-1].decode()+'\\0':raise Error('manifest identity invalid')
 for k,p in DEPS.items():
  if sha(p)!=m['dependencies'][k]:raise Error(f'dependency drift: {k}')
def source(commit:str)->dict[str,str]:
 head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();remote=subprocess.check_output(['git','rev-parse','origin/main'],cwd=ROOT,text=True).strip()
 if commit!=head or commit!=remote or len(commit)!=40:raise Error('source not exact published main')
 for p in (Path(__file__),HERE/'test_execute.py',MANIFEST,HERE.parent/'package.md',ROOT/'docs/specifications/SPEC-A11-CENTERED-THERMAL-PROSPECTIVE-VALIDATION.md',ROOT/'docs/exec-plans/20260910-a11e10-centered-thermal-prospective-validation.md'):
  rel=p.relative_to(ROOT).as_posix()
  if subprocess.check_output(['git','show',f'{commit}:{rel}'],cwd=ROOT)!=p.read_bytes():raise Error(f'working source differs: {rel}')
 return {'source_commit':commit,'source_tree':subprocess.check_output(['git','rev-parse',f'{commit}^{{tree}}'],cwd=ROOT,text=True).strip()}
def summarize(rows:list[dict[str,Any]],gate:dict[str,Any])->dict[str,Any]:
 ratios={k:float(np.median([r['candidate_metrics'][k] for r in rows]))/max(float(np.median([r['faithful_metrics'][k] for r in rows])),1e-12) for k in METRICS}; improved=sum(r['candidate_metrics']['annual_temperature_dispersion_error']<r['faithful_metrics']['annual_temperature_dispersion_error'] for r in rows)
 passed=ratios['annual_temperature_dispersion_error']<=gate['annual_max'] and all(ratios[k]<=gate['noninferiority_max'] for k in NONANNUAL) and improved/len(rows)>=gate['improvement_fraction_min']
 return {'passes':passed,'metric_median_ratios_candidate_over_faithful':ratios,'annual_improved':improved,'annual_improvement_fraction':improved/len(rows)}
def analyze(bundle:dict[str,Any],manifest:dict[str,Any],a8:Any,a9:Any,metricmod:Any)->tuple[dict[str,Any],dict[str,Any],dict[str,Any]]:
 weights=np.asarray([31,28,31,30,31,30,31,31,30,31,30,31],dtype=np.float64);weights/=weights.sum();rows=[]
 for r in bundle['rows']:
  f=np.asarray(r['faithful_tmean']);p=np.asarray(r['faithful_precipitation']);obs={'tmean':np.asarray(r['observed_tmean']),'precipitation':np.asarray(r['observed_precipitation'])};loading=np.asarray(r['loading_c']);states=a9.centered(r['states']);q=a9.balanced_tenths(loading,states);candidate=f+q/10.0
  rows.append({'station_id':r['station_id'],'cohort_id':r['cohort_id'],'candidate_index':r['candidate_index'],'burn':r['burn'],'thermal_seed_u64':r['thermal_seed_u64'],'delta_tenths_sha256':canon(q.tolist()),'balanced_delta_sum_tenths':[int(x) for x in q.sum(axis=0)],'faithful_metrics':a9.metrics(p,f,obs,weights,metricmod),'candidate_metrics':a9.metrics(p,candidate,obs,weights,metricmod)})
 if len(rows)!=640 or any(any(x for x in r['balanced_delta_sum_tenths']) for r in rows):raise Error('incomplete or unbalanced grid')
 overall=summarize(rows,manifest['gate']);station={}
 for s in sorted({r['station_id'] for r in rows}):station[s]=float(np.median([r['candidate_metrics']['annual_temperature_dispersion_error'] for r in rows if r['station_id']==s]))/max(float(np.median([r['faithful_metrics']['annual_temperature_dispersion_error'] for r in rows if r['station_id']==s])),1e-12)
 overall['station_annual_error_ratios']=station;overall['passes']=overall['passes'] and max(station.values())<=manifest['gate']['station_annual_max']
 cohorts={str(c):summarize([r for r in rows if r['cohort_id']==c],manifest['gate']) for c in range(4)};stable=all(x['passes'] for x in cohorts.values());disposition='CENTERED_THERMAL_COMPONENT_RETAINED_FOR_TRANSFER' if overall['passes'] and stable else 'CENTERED_THERMAL_COMPONENT_REJECTED'
 decision={'schema_version':'a11e10-decision-1','terminal':'EXECUTED-COMPLETE','disposition':disposition,'overall':overall,'cohorts':cohorts,'cohort_stability_passes':stable,'confirmation_authorized':False,'production_authorized':False}
 evidence={'schema_version':'a11e10-evidence-1','rows':rows,'decision':decision,'confirmation_target_series_accessed':False};evidence['evidence_sha256']=canon(evidence)
 loading={'schema_version':'a11e10-loading-bundle-1','stations':bundle['loadings'],'confirmation_target_series_accessed':False}
 return evidence,decision,loading
def execute(commit:str,replay:bool)->None:
 manifest=json.loads(MANIFEST.read_text());validate(manifest);runtime={'python':platform.python_version(),'numpy':np.__version__,'system':platform.system(),'machine':platform.machine(),'rustc':subprocess.check_output(['rustc','--version'],text=True).strip(),'cargo':subprocess.check_output(['cargo','--version'],text=True).strip()}
 if runtime!=manifest['runtime']:raise Error(f'runtime drift {runtime}')
 src=source(commit);a8=load('a11e10_a8',A8/'execute.py');a9=load('a11e10_a9',A9/'execute.py');metricmod=load('a11e10_metrics',a8.A11E5);bundle_path=HERE/'replay-input-bundle-v1.json'
 if replay:bundle=json.loads(bundle_path.read_text())
 else:
  if RUN.exists():raise Error('runtime exists')
  try:
   pred=load('a11e10_pred',a8.A11E2);pm=pred.validate_manifest(json.loads(a8.A11E2_MANIFEST.read_text()));inherited,devrows,_=pred.verify_inputs(pm);base=pred.ensure_base_loaded();development,preflight=base.load_development(devrows);obs={x['point_id']:x for x in development};panel=json.loads(PANEL.read_text())['stations'];RUN.mkdir(parents=True);build=RUN/'build';subprocess.run(['cargo','build','--release','--locked','--bin','cligen','--target-dir',str(build)],cwd=ROOT,check=True);binary=build/'release/cligen';bundle_rows=[];loadings=[];station_root=Path(os.environ.get('CLIGEN_DATA_DIR',str(Path.home()/'.cache/cligen')))/'stations/us-2015/2026.07'
   for station in panel:
    sid=station['station_id'];par=station_root/f'{sid}.par'
    if sha(par)!=station['parameter_sha256']:raise Error('parameter drift')
    generated=[]
    for cohort in manifest['cohorts']:
     for index,burn in enumerate(cohort['burns']):
      d=RUN/'runs'/sid/str(cohort['cohort_id'])/str(index);d.mkdir(parents=True);shutil.copyfile(par,d/'source.par');a8.write_runspec(d/'run.yaml',burn);subprocess.run([str(binary),'run','run.yaml'],cwd=d,check=True,capture_output=True,text=True);vals=a8.parse_cli(d/'faithful.cli');generated.append((cohort,index,burn,vals,sha(d/'faithful.cli')))
    fit=a8.fit_thermal_loading(obs[sid]['tmean'],[g[3][1] for g in generated]);loadings.append({'station_id':sid,**fit})
    for cohort,index,burn,vals,cli_sha in generated:
     sd=seed(sid,manifest['candidate_model_id'],cohort['root_seed_hex'],index);states=a8.contract.annual_states(sd,16);bundle_rows.append({'station_id':sid,'cohort_id':cohort['cohort_id'],'candidate_index':index,'burn':burn,'thermal_seed_u64':sd,'states':states,'loading_c':fit['loading_c'],'faithful_precipitation':vals[0].tolist(),'faithful_tmean':vals[1].tolist(),'observed_precipitation':obs[sid]['precipitation'].tolist(),'observed_tmean':obs[sid]['tmean'].tolist(),'faithful_cli_sha256':cli_sha})
   bundle={'schema_version':'a11e10-replay-input-1','source':src,'binary_sha256':sha(binary),'inherited':inherited,'preflight':preflight,'loadings':loadings,'rows':bundle_rows,'confirmation_target_series_accessed':False};bundle['bundle_sha256']=canon(bundle);write(bundle_path,bundle)
  finally:
   if RUN.exists():shutil.rmtree(RUN)
 evidence,decision,loading=analyze(bundle,manifest,a8,a9,metricmod);pre={'schema_version':'a11e10-preflight-1','observed':bundle['preflight'],'station_count':20,'record_count':640,'confirmation_target_series_accessed':False}
 for name,value in [('calendar-missingness-preflight-v1.json',pre),('thermal-loading-bundle-v1.json',loading),('development-evidence-v1.json',evidence),('development-decision-v1.json',decision)]:write(HERE/name,value)
 receipt={'schema_version':'a11e10-execution-receipt-1','mode':'replay' if replay else 'execute',**src,'runtime':runtime,'bundle_sha256':sha(bundle_path),'outputs':{n:sha(HERE/n) for n in ('calendar-missingness-preflight-v1.json','thermal-loading-bundle-v1.json','development-evidence-v1.json','development-decision-v1.json')},'confirmation_target_series_accessed':False};write(HERE/'execution-receipt-v1.json',receipt)
def main()->None:
 p=argparse.ArgumentParser();p.add_argument('--source-commit');p.add_argument('--execute',action='store_true');p.add_argument('--replay',action='store_true');p.add_argument('--validate-manifest',action='store_true');a=p.parse_args();m=json.loads(MANIFEST.read_text());validate(m)
 if a.validate_manifest:print(canon(m));return
 if not a.source_commit or a.execute==a.replay:p.error('choose execute or replay with source commit')
 execute(a.source_commit,a.replay)
if __name__=='__main__':main()
