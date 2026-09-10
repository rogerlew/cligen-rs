#!/usr/bin/env python3
"""Analyze station loading and signal influence for A11E12."""
from __future__ import annotations
import argparse,hashlib,json,math,platform,subprocess
from pathlib import Path
from typing import Any
import numpy as np
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent;MANIFEST=HERE/'execution-manifest-v1.json';A10=ROOT/'docs/work-packages/20260910-a11e10-centered-thermal-prospective-validation/artifacts';A11=ROOT/'docs/work-packages/20260910-a11e11-cohort-temporal-instability-attribution/artifacts'
DEPS={'a11e10_bundle':A10/'replay-input-bundle-v1.json','a11e10_loading':A10/'thermal-loading-bundle-v1.json','a11e10_evidence':A10/'development-evidence-v1.json','a11e11_manifest':A11/'execution-manifest-v1.json','a11e11_analyzer':A11/'analyze.py','a11e11_evidence':A11/'attribution-evidence-v1.json','a11e11_decision':A11/'attribution-decision-v1.json'}
class Error(RuntimeError):pass
def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def canon(v:Any)->str:return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def write(p:Path,v:Any)->None:q=p.with_suffix(p.suffix+'.part');q.write_text(json.dumps(v,indent=2,sort_keys=True,allow_nan=False)+'\n');q.replace(p)
def validate(m:dict[str,Any])->None:
 if m['confirmation_target_access'] is not False or m['association_threshold']!=.5:raise Error('manifest invalid')
 for k,p in DEPS.items():
  if sha(p)!=m['dependencies'][k]:raise Error(f'dependency drift: {k}')
def source(commit:str)->dict[str,str]:
 head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();remote=subprocess.check_output(['git','rev-parse','origin/main'],cwd=ROOT,text=True).strip()
 if commit!=head or commit!=remote or len(commit)!=40:raise Error('source not exact published main')
 for p in (Path(__file__),HERE/'test_analyze.py',MANIFEST,HERE.parent/'package.md',ROOT/'docs/specifications/SPEC-A11-STATION-LOADING-SIGNAL-INFLUENCE.md',ROOT/'docs/exec-plans/20260910-a11e12-station-loading-signal-influence.md'):
  rel=p.relative_to(ROOT).as_posix()
  if subprocess.check_output(['git','show',f'{commit}:{rel}'],cwd=ROOT)!=p.read_bytes():raise Error(f'working source differs: {rel}')
 return {'source_commit':commit,'source_tree':subprocess.check_output(['git','rev-parse',f'{commit}^{{tree}}'],cwd=ROOT,text=True).strip()}
def common(correlations:dict[str,dict[str,float]],names:list[str],threshold:float)->list[str]:
 out=[]
 for name in names:
  values=list(correlations[name].values())
  if all(abs(v)>=threshold for v in values) and (all(v>0 for v in values) or all(v<0 for v in values)):out.append(name)
 return out
def classify(magnitude:list[str],shape:list[str],clearing:dict[str,list[str]],common_exclusions:list[str])->str:
 if magnitude:return 'COMMON_LOADING_MAGNITUDE_ASSOCIATION'
 if shape:return 'COMMON_LOADING_SHAPE_ASSOCIATION'
 if not common_exclusions and any(clearing.values()):return 'STATION_SPECIFIC_NO_COMMON_LOADING_RULE'
 return 'NO_SIMPLE_LOADING_ATTRIBUTION'
def analyze(m:dict[str,Any])->tuple[dict[str,Any],dict[str,Any]]:
 bundle=json.loads((A10/'replay-input-bundle-v1.json').read_text());loading=json.loads((A10/'thermal-loading-bundle-v1.json').read_text());e10=json.loads((A10/'development-evidence-v1.json').read_text());e11=json.loads((A11/'attribution-evidence-v1.json').read_text());weights=np.asarray([31,28,31,30,31,30,31,31,30,31,30,31],dtype=np.float64);weights/=weights.sum();load_by={r['station_id']:r for r in loading['stations']};bundle_by={s:[r for r in bundle['rows'] if r['station_id']==s] for s in sorted(load_by)};station_rows=[]
 for station in sorted(load_by):
  l=np.asarray(load_by[station]['loading_c']);norm=float(np.linalg.norm(l));annual=abs(float(l@weights));rough=float(np.linalg.norm(np.roll(l,-1)-l))/max(norm,1e-12);signals=[];obs=np.asarray(bundle_by[station][0]['observed_tmean'])@weights
  for r in bundle_by[station]:
   states=np.asarray(r['states']);states-=np.mean(states);raw=np.outer(states,l)*10;q=np.rint(raw)
   for month in range(12):
    while int(q[:,month].sum())!=0:
     direction=-1 if q[:,month].sum()>0 else 1;choices=sorted(range(16),key=lambda y:(abs((q[y,month]+direction)-raw[y,month])-abs(q[y,month]-raw[y,month]),y));q[choices[0],month]+=direction
   signals.append(float(np.std((q/10)@weights,ddof=1)))
  station_rows.append({'station_id':station,'loading_l2':norm,'loading_max_abs':float(np.max(np.abs(l))),'annual_weighted_loading_abs':annual,'selected_eigenvalue':float(load_by[station]['selected_eigenvalue']),'signal_sd_over_observed_sd':float(np.median(signals))/max(float(np.std(obs,ddof=1)),1e-12),'loading_max_over_l2':float(np.max(np.abs(l)))/max(norm,1e-12),'cyclic_roughness_over_l2':rough})
 surfaces={f"c{s['cohort_id']}_{s['metric']}":s for s in e11['surfaces']};correlations={name:{} for name in m['magnitude_predictors']+m['shape_predictors']}
 for predictor in correlations:
  x=np.asarray([r[predictor] for r in station_rows])
  for key,surface in surfaces.items():
   y=np.asarray([surface['station_median_error_changes'][r['station_id']] for r in station_rows]);correlations[predictor][key]=float(np.corrcoef(x,y)[0,1]) if np.std(x)>0 and np.std(y)>0 else 0.0
 magnitude=common(correlations,m['magnitude_predictors'],m['association_threshold']);shape=common(correlations,m['shape_predictors'],m['association_threshold']);clearing={}
 for key,surface in surfaces.items():
  metric=surface['metric'];cohort=surface['cohort_id'];cr=[r for r in e10['rows'] if r['cohort_id']==cohort];fkey='faithful_metrics';ckey='candidate_metrics';clearing[key]=[]
  for station in sorted(load_by):
   subset=[r for r in cr if r['station_id']!=station];ratio=float(np.median([r[ckey][metric] for r in subset]))/max(float(np.median([r[fkey][metric] for r in subset])),1e-12)
   if ratio<=m['ratio_limit']:clearing[key].append(station)
 common_exclusions=sorted(set.intersection(*(set(v) for v in clearing.values()))) if all(clearing.values()) else []
 disposition=classify(magnitude,shape,clearing,common_exclusions);decision={'schema_version':'a11e12-decision-1','terminal':'EXECUTED-COMPLETE','disposition':disposition,'common_magnitude_predictors':magnitude,'common_shape_predictors':shape,'common_single_station_exclusions':common_exclusions,'a11e10_disposition_unchanged':'CENTERED_THERMAL_COMPONENT_REJECTED','normalization_hypothesis_authorized':bool(magnitude or shape),'confirmation_authorized':False,'production_authorized':False};evidence={'schema_version':'a11e12-evidence-1','station_count':len(station_rows),'station_predictors':station_rows,'surface_correlations':correlations,'clearing_single_station_exclusions':clearing,'decision':decision,'confirmation_target_series_accessed':False};evidence['evidence_sha256']=canon(evidence);return evidence,decision
def main()->None:
 p=argparse.ArgumentParser();p.add_argument('--source-commit');p.add_argument('--execute',action='store_true');p.add_argument('--replay',action='store_true');p.add_argument('--validate-manifest',action='store_true');a=p.parse_args();m=json.loads(MANIFEST.read_text());validate(m)
 if a.validate_manifest:print(canon(m));return
 if not a.source_commit or a.execute==a.replay:p.error('choose execute or replay with source commit')
 src=source(a.source_commit);runtime={'python':platform.python_version(),'numpy':np.__version__,'system':platform.system(),'machine':platform.machine()}
 if runtime!=m['runtime']:raise Error(f'runtime drift {runtime}')
 evidence,decision=analyze(m);write(HERE/'attribution-evidence-v1.json',evidence);write(HERE/'attribution-decision-v1.json',decision);write(HERE/'execution-receipt-v1.json',{'schema_version':'a11e12-execution-receipt-1','mode':'replay' if a.replay else 'execute',**src,'runtime':runtime,'inputs':{k:sha(v) for k,v in DEPS.items()},'evidence_sha256':sha(HERE/'attribution-evidence-v1.json'),'decision_sha256':sha(HERE/'attribution-decision-v1.json'),'confirmation_target_series_accessed':False})
if __name__=='__main__':main()
