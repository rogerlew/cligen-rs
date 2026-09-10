#!/usr/bin/env python3
"""Execute A11E14 candidate-fit to development AR(1) parameter transfer."""
from __future__ import annotations
import argparse,hashlib,importlib.util,json,math,platform,subprocess,sys
from collections import defaultdict
from pathlib import Path
from typing import Any
import numpy as np
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent;MANIFEST=HERE/'execution-manifest-v1.json'
A1=ROOT/'docs/work-packages/20260825-a11e1-observed-strategy-comparison/artifacts/execute.py';A2=ROOT/'docs/work-packages/20260825-a11e2-nearest-candidate-forcing/artifacts';PANEL=ROOT/'docs/work-packages/20260715-a8a-dry-regime-applicability/artifacts/panel-v1.json';A10=ROOT/'docs/work-packages/20260910-a11e10-centered-thermal-prospective-validation/artifacts/replay-input-bundle-v1.json';A13=ROOT/'docs/work-packages/20260910-a11e13-thermal-successor-law-freeze/artifacts';A9=ROOT/'docs/work-packages/20260910-a11e9-thermal-mean-regression-attribution/artifacts/execute.py';A5=ROOT/'docs/work-packages/20260827-a11e5-interannual-family-stability/artifacts/execute.py'
DEPS={'a11e1_executor':A1,'a11e2_executor':A2/'execute.py','a11e2_manifest':A2/'execution-manifest-v1.json','panel':PANEL,'a11e10_bundle':A10,'a11e13_analyzer':A13/'analyze.py','a11e13_decision':A13/'feasibility-decision-v1.json','a11e9_executor':A9};METRICS=('monthly_temperature_dispersion_error','annual_temperature_dispersion_error','temperature_cross_month_correlation_rmse','annual_temperature_lag1_error','annual_temperature_low_frequency_error','monthly_temperature_mean_absolute_error_c');NONANNUAL=tuple(k for k in METRICS if k!='annual_temperature_dispersion_error')
class Error(RuntimeError):pass
def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def canon(v:Any)->str:return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def write(p:Path,v:Any)->None:q=p.with_suffix(p.suffix+'.part');q.write_text(json.dumps(v,indent=2,sort_keys=True,allow_nan=False)+'\n');q.replace(p)
def load(n:str,p:Path)->Any:s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);sys.modules[n]=m;s.loader.exec_module(m);return m
def phi(values:Any,weights:np.ndarray,clip:list[float])->float:
 annual=np.asarray(values,dtype=np.float64)@weights;x=annual[:-1];y=annual[1:]
 if len(x)<2 or float(np.std(x))==0 or float(np.std(y))==0:raise Error('degenerate annual series')
 return float(np.clip(np.corrcoef(x,y)[0,1],clip[0],clip[1]))
def half(point_id:str)->int:return hashlib.sha256(point_id.encode()).digest()[0]&1
def summary(rows:list[dict[str,Any]],gate:dict[str,Any],station_gate:bool=False)->dict[str,Any]:
 ratios={k:float(np.median([r['candidate_metrics'][k] for r in rows]))/max(float(np.median([r['faithful_metrics'][k] for r in rows])),1e-12) for k in METRICS};improved=sum(r['candidate_metrics']['annual_temperature_dispersion_error']<r['faithful_metrics']['annual_temperature_dispersion_error'] for r in rows);out={'metric_median_ratios_candidate_over_faithful':ratios,'annual_improved':improved,'annual_improvement_fraction':improved/len(rows)};passed=ratios['annual_temperature_dispersion_error']<=gate['annual_max'] and all(ratios[k]<=gate['noninferiority_max'] for k in NONANNUAL) and out['annual_improvement_fraction']>=gate['improvement_fraction_min']
 if station_gate:
  sr={s:float(np.median([r['candidate_metrics']['annual_temperature_dispersion_error'] for r in rows if r['station_id']==s]))/max(float(np.median([r['faithful_metrics']['annual_temperature_dispersion_error'] for r in rows if r['station_id']==s])),1e-12) for s in sorted({r['station_id'] for r in rows})};out['station_annual_error_ratios']=sr;passed=passed and max(sr.values())<=gate['station_annual_max']
 out['passes']=bool(passed);return out
def validate(m:dict[str,Any])->None:
 if m['confirmation_target_access'] is not False or m['estimators']!=['global_median_phi','regime_median_phi'] or m['expected']!={'fit_objects':1200,'development_objects':20,'downstream_rows_per_estimator':640}:raise Error('manifest invalid')
 for k,p in DEPS.items():
  if sha(p)!=m['dependencies'][k]:raise Error(f'dependency drift: {k}')
def source(commit:str)->dict[str,str]:
 head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();remote=subprocess.check_output(['git','rev-parse','origin/main'],cwd=ROOT,text=True).strip()
 if commit!=head or commit!=remote or len(commit)!=40:raise Error('source not exact published main')
 for p in (Path(__file__),HERE/'test_analyze.py',MANIFEST,HERE.parent/'package.md',ROOT/'docs/specifications/SPEC-A11-AR1-PARAMETER-TRANSFER.md',ROOT/'docs/exec-plans/20260910-a11e14-ar1-parameter-transfer.md'):
  rel=p.relative_to(ROOT).as_posix()
  if subprocess.check_output(['git','show',f'{commit}:{rel}'],cwd=ROOT)!=p.read_bytes():raise Error(f'working source differs: {rel}')
 return {'source_commit':commit,'source_tree':subprocess.check_output(['git','rev-parse',f'{commit}^{{tree}}'],cwd=ROOT,text=True).strip()}
def load_observed()->tuple[list[dict[str,Any]],list[dict[str,Any]],dict[str,Any]]:
 pred=load('a11e14_a2',A2/'execute.py');pm=pred.validate_manifest(json.loads((A2/'execution-manifest-v1.json').read_text()));_,devrows,_=pred.verify_inputs(pm);base=pred.ensure_base_loaded();all_fit,fit_pre=base.load_fit_corpus();development,dev_pre=base.load_development(devrows);fit=[r for r in all_fit if r['role']=='candidate_fit']
 return fit,development,{'fit':fit_pre,'development':dev_pre,'fitting_role':'candidate_fit','fitting_object_count':len(fit),'excluded_fit_validation_count':len(all_fit)-len(fit),'confirmation_target_series_accessed':False}
def fit_estimators(fit:list[dict[str,Any]],development:list[dict[str,Any]],weights:np.ndarray,m:dict[str,Any])->tuple[dict[str,Any],dict[str,float],dict[str,float]]:
 fit_rows=[{'point_id':r['point_id'],'regime':r['regime'],'phi':phi(r['tmean'],weights,m['phi_clip']),'half':half(r['point_id'])} for r in fit];dev_phi={r['point_id']:phi(r['tmean'],weights,m['phi_clip']) for r in development};dev_regime={r['point_id']:r['regime'] for r in development};groups=defaultdict(list)
 for r in fit_rows:groups[r['regime']].append(r)
 global_phi=float(np.median([r['phi'] for r in fit_rows]));regime_phi={g:float(np.median([r['phi'] for r in rows])) for g,rows in sorted(groups.items())};halves={g:{str(h):float(np.median([r['phi'] for r in rows if r['half']==h])) for h in (0,1)} for g,rows in sorted(groups.items())}
 for g,v in halves.items():
  if not all(any(r['half']==h for r in groups[g]) for h in (0,1)):raise Error(f'empty hash half: {g}')
 base_mae=float(np.mean(np.abs(list(dev_phi.values()))));global_mae=float(np.mean([abs(global_phi-v) for v in dev_phi.values()]));regime_mae=float(np.mean([abs(regime_phi[dev_regime[s]]-v) for s,v in dev_phi.items()]));leave={}
 for g in sorted(set(dev_regime.values())):
  trained=float(np.median([r['phi'] for r in fit_rows if r['regime']!=g]));targets=[v for s,v in dev_phi.items() if dev_regime[s]==g];mae=float(np.mean([abs(trained-v) for v in targets]));zero=float(np.mean(np.abs(targets)));leave[g]={'trained_phi':trained,'phi_mae':mae,'zero_phi_mae':zero,'passes':mae<zero}
 stable_global=all(x['passes'] for x in leave.values());stable_regime=all(abs(v['0']-v['1'])<=m['hash_half_median_difference_max'] for v in halves.values());bundle={'schema_version':'a11e14-phi-fit-1','candidate_fit_count':len(fit_rows),'candidate_fit_phi_sha256':canon(sorted(fit_rows,key=lambda r:r['point_id'])),'global_phi':global_phi,'regime_phi':regime_phi,'hash_half_medians':halves,'development_oracle_phi':dev_phi,'phi_mae':{'zero':base_mae,'global_median_phi':global_mae,'regime_median_phi':regime_mae},'global_leave_source_regime_out':leave,'stability_passes':{'global_median_phi':stable_global,'regime_median_phi':stable_regime},'confirmation_target_series_accessed':False};return bundle,dev_phi,dev_regime
def downstream(name:str,value:Any,bundle:dict[str,Any],station_regime:dict[str,str],m:dict[str,Any])->dict[str,Any]:
 a13=load('a11e14_a13',A13/'analyze.py');a9=load('a11e14_a9',A9);metric=load('a11e14_a5',A5);weights=np.asarray([31,28,31,30,31,30,31,31,30,31,30,31],dtype=np.float64);weights/=weights.sum();rows=[];digests=[]
 for r in bundle['rows']:
  p=value if name=='global_median_phi' else value[station_regime[r['station_id']]];states=a13.ar1(r['states'],p);q=a9.balanced_tenths(np.asarray(r['loading_c']),states);f=np.asarray(r['faithful_tmean']);pr=np.asarray(r['faithful_precipitation']);obs={'tmean':np.asarray(r['observed_tmean']),'precipitation':np.asarray(r['observed_precipitation'])};rows.append({'station_id':r['station_id'],'cohort_id':r['cohort_id'],'faithful_metrics':a9.metrics(pr,f,obs,weights,metric),'candidate_metrics':a9.metrics(pr,f+q/10.0,obs,weights,metric)});digests.append({'station_id':r['station_id'],'burn':r['burn'],'delta_tenths_sha256':canon(q.tolist())})
 if len(rows)!=m['expected']['downstream_rows_per_estimator']:raise Error('downstream grid invalid')
 overall=summary(rows,m['gate'],True);cohorts={str(c):summary([r for r in rows if r['cohort_id']==c],m['gate']) for c in range(4)};stable=all(x['passes'] for x in cohorts.values());return {'row_count':len(rows),'reconstruction_sha256':canon(digests),'overall':overall,'cohorts':cohorts,'cohort_stability_passes':stable,'passes':overall['passes'] and stable}
def analyze(m:dict[str,Any])->tuple[dict[str,Any],dict[str,Any],dict[str,Any],dict[str,Any]]:
 fit,development,preflight=load_observed();weights=np.asarray([31,28,31,30,31,30,31,31,30,31,30,31],dtype=np.float64);weights/=weights.sum();fit_bundle,_,dev_regime=fit_estimators(fit,development,weights,m);panel={r['station_id']:r['stratum'] for r in json.loads(PANEL.read_text())['stations']}
 if panel!=dev_regime:raise Error('development regime/panel mismatch')
 replay=json.loads(A10.read_text());down={name:downstream(name,fit_bundle['global_phi'] if name=='global_median_phi' else fit_bundle['regime_phi'],replay,panel,m) for name in m['estimators']};admission={name:{'phi_mae_improves_zero':fit_bundle['phi_mae'][name]<fit_bundle['phi_mae']['zero'],'downstream_passes':down[name]['passes'],'stability_passes':fit_bundle['stability_passes'][name]} for name in m['estimators']}
 for v in admission.values():v['passes']=all(v.values())
 disposition='GLOBAL_PHI_TRANSFER_SUPPORTED' if admission['global_median_phi']['passes'] else ('REGIME_PHI_TRANSFER_SUPPORTED' if admission['regime_median_phi']['passes'] else 'AR1_NONDEPLOYABLE_RETIRE_THERMAL_CAMPAIGN');decision={'schema_version':'a11e14-decision-1','terminal':'EXECUTED-COMPLETE','disposition':disposition,'admission':admission,'ordered_selection':m['estimators'],'fresh_burn_validation_authorized':disposition!='AR1_NONDEPLOYABLE_RETIRE_THERMAL_CAMPAIGN','confirmation_authorized':False,'production_authorized':False};evidence={'schema_version':'a11e14-evidence-1','phi_fit':fit_bundle,'downstream':down,'decision':decision,'confirmation_target_series_accessed':False};evidence['evidence_sha256']=canon(evidence);return preflight,fit_bundle,evidence,decision
def main()->None:
 p=argparse.ArgumentParser();p.add_argument('--source-commit');p.add_argument('--execute',action='store_true');p.add_argument('--replay',action='store_true');p.add_argument('--validate-manifest',action='store_true');a=p.parse_args();m=json.loads(MANIFEST.read_text());validate(m)
 if a.validate_manifest:print(canon(m));return
 if not a.source_commit or a.execute==a.replay:p.error('choose execute or replay with source commit')
 src=source(a.source_commit);runtime={'python':platform.python_version(),'numpy':np.__version__,'system':platform.system(),'machine':platform.machine()}
 if runtime!=m['runtime']:raise Error(f'runtime drift {runtime}')
 pre,fit,evidence,decision=analyze(m)
 for n,v in [('calendar-missingness-preflight-v1.json',pre),('phi-fit-v1.json',fit),('transfer-evidence-v1.json',evidence),('transfer-decision-v1.json',decision)]:write(HERE/n,v)
 write(HERE/'execution-receipt-v1.json',{'schema_version':'a11e14-execution-receipt-1','mode':'replay' if a.replay else 'execute',**src,'runtime':runtime,'inputs':{k:sha(v) for k,v in DEPS.items()},'outputs':{n:sha(HERE/n) for n in ('calendar-missingness-preflight-v1.json','phi-fit-v1.json','transfer-evidence-v1.json','transfer-decision-v1.json')},'confirmation_target_series_accessed':False})
if __name__=='__main__':main()
