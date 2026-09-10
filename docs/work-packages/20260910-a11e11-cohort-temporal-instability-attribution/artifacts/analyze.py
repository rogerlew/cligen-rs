#!/usr/bin/env python3
"""Analyze A11E10 cohort temporal instability without new generation."""
from __future__ import annotations
import argparse,hashlib,importlib.util,json,math,platform,subprocess,sys
from pathlib import Path
from typing import Any
import numpy as np
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent;MANIFEST=HERE/'execution-manifest-v1.json';A10=ROOT/'docs/work-packages/20260910-a11e10-centered-thermal-prospective-validation/artifacts';A9=ROOT/'docs/work-packages/20260910-a11e9-thermal-mean-regression-attribution/artifacts';A5=ROOT/'docs/work-packages/20260827-a11e5-interannual-family-stability/artifacts/execute.py'
DEPS={'a11e10_manifest':A10/'execution-manifest-v1.json','a11e10_executor':A10/'execute.py','a11e10_evidence':A10/'development-evidence-v1.json','a11e10_decision':A10/'development-decision-v1.json','a11e10_bundle':A10/'replay-input-bundle-v1.json','a11e10_loading':A10/'thermal-loading-bundle-v1.json'}
class Error(RuntimeError):pass
def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def canon(v:Any)->str:return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def write(p:Path,v:Any)->None:q=p.with_suffix(p.suffix+'.part');q.write_text(json.dumps(v,indent=2,sort_keys=True,allow_nan=False)+'\n');q.replace(p)
def load(n:str,p:Path)->Any:s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);sys.modules[n]=m;s.loader.exec_module(m);return m
def validate(m:dict[str,Any])->None:
 if m['confirmation_target_access'] is not False or len(m['failed_surfaces'])!=3:raise Error('manifest invalid')
 for k,p in DEPS.items():
  if sha(p)!=m['dependencies'][k]:raise Error(f'dependency drift: {k}')
 d=json.loads((A10/'development-decision-v1.json').read_text());found=[]
 for c,v in d['cohorts'].items():
  for metric,ratio in v['metric_median_ratios_candidate_over_faithful'].items():
   if ratio>m['ratio_limit']:found.append({'cohort_id':int(c),'metric':metric})
 if found!=m['failed_surfaces']:raise Error(f'failing surfaces drifted: {found}')
def source(commit:str)->dict[str,str]:
 head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();remote=subprocess.check_output(['git','rev-parse','origin/main'],cwd=ROOT,text=True).strip()
 if commit!=head or commit!=remote or len(commit)!=40:raise Error('source not exact published main')
 for p in (Path(__file__),HERE/'test_analyze.py',MANIFEST,HERE.parent/'package.md',ROOT/'docs/specifications/SPEC-A11-COHORT-TEMPORAL-INSTABILITY-ATTRIBUTION.md',ROOT/'docs/exec-plans/20260910-a11e11-cohort-temporal-instability-attribution.md'):
  rel=p.relative_to(ROOT).as_posix()
  if subprocess.check_output(['git','show',f'{commit}:{rel}'],cwd=ROOT)!=p.read_bytes():raise Error(f'working source differs: {rel}')
 return {'source_commit':commit,'source_tree':subprocess.check_output(['git','rev-parse',f'{commit}^{{tree}}'],cwd=ROOT,text=True).strip()}
def classify(surfaces:list[dict[str,Any]])->str:
 if all(x['denominator_sensitive'] for x in surfaces):return 'RATIO_DENOMINATOR_INSTABILITY'
 if all(x['broad'] for x in surfaces):return 'BROAD_IID_TEMPORAL_INSTABILITY'
 if all(x['station_concentrated'] for x in surfaces):return 'STATION_CONCENTRATED_LOADING_INSTABILITY'
 return 'MIXED_TEMPORAL_INSTABILITY'
def analyze(m:dict[str,Any])->tuple[dict[str,Any],dict[str,Any]]:
 bundle=json.loads((A10/'replay-input-bundle-v1.json').read_text());recorded=json.loads((A10/'development-evidence-v1.json').read_text());byid={(r['station_id'],r['cohort_id'],r['candidate_index']):r for r in recorded['rows']};a9=load('a11e11_a9',A9/'execute.py');a5=load('a11e11_a5',A5);weights=np.asarray([31,28,31,30,31,30,31,31,30,31,30,31],dtype=np.float64);weights/=weights.sum();rows=[]
 for r in bundle['rows']:
  key=(r['station_id'],r['cohort_id'],r['candidate_index']);metrics=byid[key];f=np.asarray(r['faithful_tmean'])@weights;o=np.asarray(r['observed_tmean'])@weights;loading=np.asarray(r['loading_c']);states=a9.centered(r['states']);q=a9.balanced_tenths(loading,states);signal=(q/10.0)@weights;c=f+signal
  fc=a5.safe_corr(f[:-1],f[1:]);cc=a5.safe_corr(c[:-1],c[1:]);oc=a5.safe_corr(o[:-1],o[1:]);fl=a5.low_frequency_fraction(f);cl=a5.low_frequency_fraction(c);ol=a5.low_frequency_fraction(o)
  rows.append({'station_id':r['station_id'],'cohort_id':r['cohort_id'],'candidate_index':r['candidate_index'],'lag1':{'faithful':fc,'candidate':cc,'observed':oc,'candidate_minus_observed':cc-oc,'faithful_minus_observed':fc-oc,'absolute_error_change':abs(cc-oc)-abs(fc-oc),'signal':a5.safe_corr(signal[:-1],signal[1:])},'low_frequency':{'faithful':fl,'candidate':cl,'observed':ol,'candidate_minus_observed':cl-ol,'faithful_minus_observed':fl-ol,'absolute_error_change':abs(cl-ol)-abs(fl-ol),'signal':a5.low_frequency_fraction(signal)},'recorded_metrics':{'faithful_lag1':metrics['faithful_metrics']['annual_temperature_lag1_error'],'candidate_lag1':metrics['candidate_metrics']['annual_temperature_lag1_error'],'faithful_low_frequency':metrics['faithful_metrics']['annual_temperature_low_frequency_error'],'candidate_low_frequency':metrics['candidate_metrics']['annual_temperature_low_frequency_error']}})
 surfaces=[]
 for spec in m['failed_surfaces']:
  cohort=spec['cohort_id'];kind='lag1' if 'lag1' in spec['metric'] else 'low_frequency';cr=[r for r in rows if r['cohort_id']==cohort];fm=np.median([r['recorded_metrics']['faithful_'+kind] for r in cr]);cm=np.median([r['recorded_metrics']['candidate_'+kind] for r in cr]);excess=float(cm-m['ratio_limit']*fm);station_d={s:float(np.median([r[kind]['absolute_error_change'] for r in cr if r['station_id']==s])) for s in sorted({r['station_id'] for r in cr})};worse=sum(v>0 for v in station_d.values());positive=sorted((v for v in station_d.values() if v>0),reverse=True);total=sum(positive);acc=0;needed=0
  for v in positive:
   acc+=v;needed+=1
   if acc>=total/2:break
  pair_worse=sum(r[kind]['absolute_error_change']>0 for r in cr);signal=[r[kind]['signal'] for r in cr];change=[r[kind]['absolute_error_change'] for r in cr];association=float(np.corrcoef(signal,change)[0,1]) if np.std(signal)>0 and np.std(change)>0 else 0.0
  surfaces.append({'cohort_id':cohort,'metric':spec['metric'],'faithful_median_error':float(fm),'candidate_median_error':float(cm),'ratio':float(cm/max(fm,1e-12)),'absolute_excess_above_1_05_bound':excess,'denominator_sensitive':excess<=m['absolute_excess_tolerance'],'stations_with_worse_median':worse,'pair_worsening_fraction':pair_worse/160,'broad':worse>=m['broad_station_minimum'] and pair_worse/160>=m['broad_worsening_fraction_minimum'],'stations_accounting_for_half_positive_deterioration':needed,'station_concentrated':needed<=m['concentrated_station_maximum'],'signal_error_change_correlation':association,'station_median_error_changes':station_d})
 disposition=classify(surfaces);decision={'schema_version':'a11e11-decision-1','terminal':'EXECUTED-COMPLETE','disposition':disposition,'a11e10_disposition_unchanged':'CENTERED_THERMAL_COMPONENT_REJECTED','confirmation_authorized':False,'production_authorized':False};evidence={'schema_version':'a11e11-evidence-1','record_count':len(rows),'surfaces':surfaces,'decision':decision,'confirmation_target_series_accessed':False};evidence['evidence_sha256']=canon(evidence);return evidence,decision
def main()->None:
 p=argparse.ArgumentParser();p.add_argument('--source-commit');p.add_argument('--execute',action='store_true');p.add_argument('--replay',action='store_true');p.add_argument('--validate-manifest',action='store_true');a=p.parse_args();m=json.loads(MANIFEST.read_text());validate(m)
 if a.validate_manifest:print(canon(m));return
 if not a.source_commit or a.execute==a.replay:p.error('choose execute or replay with source commit')
 src=source(a.source_commit);runtime={'python':platform.python_version(),'numpy':np.__version__,'system':platform.system(),'machine':platform.machine()}
 if runtime!=m['runtime']:raise Error(f'runtime drift: {runtime}')
 evidence,decision=analyze(m);write(HERE/'attribution-evidence-v1.json',evidence);write(HERE/'attribution-decision-v1.json',decision);write(HERE/'execution-receipt-v1.json',{'schema_version':'a11e11-execution-receipt-1','mode':'replay' if a.replay else 'execute',**src,'runtime':runtime,'inputs':{k:sha(v) for k,v in DEPS.items()},'evidence_sha256':sha(HERE/'attribution-evidence-v1.json'),'decision_sha256':sha(HERE/'attribution-decision-v1.json'),'confirmation_target_series_accessed':False})
if __name__=='__main__':main()
