#!/usr/bin/env python3
"""Execute A11E13 AR(1) thermal successor feasibility."""
from __future__ import annotations
import argparse,hashlib,importlib.util,json,math,platform,subprocess,sys
from pathlib import Path
from typing import Any
import numpy as np
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent;MANIFEST=HERE/'execution-manifest-v1.json';A10=ROOT/'docs/work-packages/20260910-a11e10-centered-thermal-prospective-validation/artifacts';A12=ROOT/'docs/work-packages/20260910-a11e12-station-loading-signal-influence/artifacts';A9=ROOT/'docs/work-packages/20260910-a11e9-thermal-mean-regression-attribution/artifacts';A5=ROOT/'docs/work-packages/20260827-a11e5-interannual-family-stability/artifacts/execute.py'
DEPS={'a11e10_bundle':A10/'replay-input-bundle-v1.json','a11e10_evidence':A10/'development-evidence-v1.json','a11e10_loading':A10/'thermal-loading-bundle-v1.json','a11e12_manifest':A12/'execution-manifest-v1.json','a11e12_decision':A12/'attribution-decision-v1.json','a11e9_executor':A9/'execute.py'};METRICS=('monthly_temperature_dispersion_error','annual_temperature_dispersion_error','temperature_cross_month_correlation_rmse','annual_temperature_lag1_error','annual_temperature_low_frequency_error','monthly_temperature_mean_absolute_error_c');NONANNUAL=tuple(x for x in METRICS if x!='annual_temperature_dispersion_error')
class Error(RuntimeError):pass
def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def canon(v:Any)->str:return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def write(p:Path,v:Any)->None:q=p.with_suffix(p.suffix+'.part');q.write_text(json.dumps(v,indent=2,sort_keys=True,allow_nan=False)+'\n');q.replace(p)
def load(n:str,p:Path)->Any:s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);sys.modules[n]=m;s.loader.exec_module(m);return m
def validate(m:dict[str,Any])->None:
 if m['confirmation_target_access'] is not False or len(m['retired_model_ids'])!=2 or m['conditioned_iid_status']!='REJECTED_HORIZON_SELECTOR_SEMANTICS':raise Error('manifest invalid')
 for k,p in DEPS.items():
  if sha(p)!=m['dependencies'][k]:raise Error(f'dependency drift: {k}')
def source(commit:str)->dict[str,str]:
 head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();remote=subprocess.check_output(['git','rev-parse','origin/main'],cwd=ROOT,text=True).strip()
 if commit!=head or commit!=remote or len(commit)!=40:raise Error('source not exact published main')
 for p in (Path(__file__),HERE/'test_analyze.py',MANIFEST,HERE.parent/'package.md',ROOT/'docs/specifications/SPEC-A11-THERMAL-SUCCESSOR-LAW-FREEZE.md',ROOT/'docs/exec-plans/20260910-a11e13-thermal-successor-law-freeze.md'):
  rel=p.relative_to(ROOT).as_posix()
  if subprocess.check_output(['git','show',f'{commit}:{rel}'],cwd=ROOT)!=p.read_bytes():raise Error(f'working source differs: {rel}')
 return {'source_commit':commit,'source_tree':subprocess.check_output(['git','rev-parse',f'{commit}^{{tree}}'],cwd=ROOT,text=True).strip()}
def ar1(innovations:list[float],phi:float)->list[float]:
 e=np.asarray(innovations,dtype=np.float64);z=np.empty(16);z[0]=e[0];scale=math.sqrt(1-phi*phi)
 for i in range(1,16):z[i]=phi*z[i-1]+scale*e[i]
 z-=np.mean(z);sd=float(np.std(z,ddof=1))
 if not math.isfinite(sd) or sd<=0:raise Error('degenerate AR1 state')
 return (z/sd).tolist()
def summary(rows:list[dict[str,Any]],gate:dict[str,Any])->dict[str,Any]:
 ratios={k:float(np.median([r['candidate_metrics'][k] for r in rows]))/max(float(np.median([r['faithful_metrics'][k] for r in rows])),1e-12) for k in METRICS};improved=sum(r['candidate_metrics']['annual_temperature_dispersion_error']<r['faithful_metrics']['annual_temperature_dispersion_error'] for r in rows);passed=ratios['annual_temperature_dispersion_error']<=gate['annual_max'] and all(ratios[k]<=gate['noninferiority_max'] for k in NONANNUAL) and improved/len(rows)>=gate['improvement_fraction_min'];return {'passes':passed,'metric_median_ratios_candidate_over_faithful':ratios,'annual_improved':improved,'annual_improvement_fraction':improved/len(rows)}
def analyze(m:dict[str,Any])->tuple[dict[str,Any],dict[str,Any],dict[str,Any]]:
 bundle=json.loads((A10/'replay-input-bundle-v1.json').read_text());a9=load('a11e13_a9',A9/'execute.py');a5=load('a11e13_a5',A5);weights=np.asarray([31,28,31,30,31,30,31,31,30,31,30,31],dtype=np.float64);weights/=weights.sum();phi_by={};rows=[]
 for r in bundle['rows']:
  sid=r['station_id'];obs={'tmean':np.asarray(r['observed_tmean']),'precipitation':np.asarray(r['observed_precipitation'])};annual=obs['tmean']@weights
  if sid not in phi_by:phi_by[sid]=float(np.clip(a5.safe_corr(annual[:-1],annual[1:]),m['phi_clip'][0],m['phi_clip'][1]))
  states=ar1(r['states'],phi_by[sid]);loading=np.asarray(r['loading_c']);q=a9.balanced_tenths(loading,states);f=np.asarray(r['faithful_tmean']);p=np.asarray(r['faithful_precipitation']);c=f+q/10.0
  rows.append({'station_id':sid,'cohort_id':r['cohort_id'],'candidate_index':r['candidate_index'],'burn':r['burn'],'phi':phi_by[sid],'states_sha256':canon(states),'delta_tenths_sha256':canon(q.tolist()),'balanced_delta_sum_tenths':[int(x) for x in q.sum(axis=0)],'faithful_metrics':a9.metrics(p,f,obs,weights,a5),'candidate_metrics':a9.metrics(p,c,obs,weights,a5)})
 if len(rows)!=640 or any(any(r['balanced_delta_sum_tenths']) for r in rows):raise Error('grid invalid')
 overall=summary(rows,m['gate']);station={}
 for s in sorted(phi_by):station[s]=float(np.median([r['candidate_metrics']['annual_temperature_dispersion_error'] for r in rows if r['station_id']==s]))/max(float(np.median([r['faithful_metrics']['annual_temperature_dispersion_error'] for r in rows if r['station_id']==s])),1e-12)
 overall['station_annual_error_ratios']=station;overall['passes']=overall['passes'] and max(station.values())<=m['gate']['station_annual_max'];cohorts={str(c):summary([r for r in rows if r['cohort_id']==c],m['gate']) for c in range(4)};stable=all(v['passes'] for v in cohorts.values());feasible=overall['passes'] and stable;disp='AR1_FEASIBLE_TRANSFER_REQUIRED' if feasible else 'AR1_NOT_FEASIBLE_RETIRE_THERMAL_CAMPAIGN';decision={'schema_version':'a11e13-decision-1','terminal':'EXECUTED-COMPLETE','disposition':disp,'overall':overall,'cohorts':cohorts,'cohort_stability_passes':stable,'retired_model_ids':m['retired_model_ids'],'conditioned_iid_status':m['conditioned_iid_status'],'parameter_transfer_authorized':feasible,'confirmation_authorized':False,'production_authorized':False};evidence={'schema_version':'a11e13-evidence-1','record_count':len(rows),'station_phi':phi_by,'phi_clip':m['phi_clip'],'rows':rows,'decision':decision,'confirmation_target_series_accessed':False};evidence['evidence_sha256']=canon(evidence);retirement={'schema_version':'a11e13-retirement-1','retired_model_ids':m['retired_model_ids'],'reason':'fresh cohort temporal instability with no common loading correction','replacement_selected':feasible,'replacement_id':m['candidate_model_id'] if feasible else None,'confirmation_target_series_accessed':False};return evidence,decision,retirement
def main()->None:
 p=argparse.ArgumentParser();p.add_argument('--source-commit');p.add_argument('--execute',action='store_true');p.add_argument('--replay',action='store_true');p.add_argument('--validate-manifest',action='store_true');a=p.parse_args();m=json.loads(MANIFEST.read_text());validate(m)
 if a.validate_manifest:print(canon(m));return
 if not a.source_commit or a.execute==a.replay:p.error('choose execute or replay with source commit')
 src=source(a.source_commit);runtime={'python':platform.python_version(),'numpy':np.__version__,'system':platform.system(),'machine':platform.machine()}
 if runtime!=m['runtime']:raise Error(f'runtime drift {runtime}')
 evidence,decision,retirement=analyze(m)
 for n,v in [('feasibility-evidence-v1.json',evidence),('feasibility-decision-v1.json',decision),('thermal-law-retirement-v1.json',retirement)]:write(HERE/n,v)
 write(HERE/'execution-receipt-v1.json',{'schema_version':'a11e13-execution-receipt-1','mode':'replay' if a.replay else 'execute',**src,'runtime':runtime,'inputs':{k:sha(v) for k,v in DEPS.items()},'outputs':{n:sha(HERE/n) for n in ('feasibility-evidence-v1.json','feasibility-decision-v1.json','thermal-law-retirement-v1.json')},'confirmation_target_series_accessed':False})
if __name__=='__main__':main()
