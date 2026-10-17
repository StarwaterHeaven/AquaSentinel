"""AquaSentinel water-point score (v0.3). Five dimensions x 20 points; any point not working is flagged and listed first.
Run: python scoring/score.py   (needs the Kijana data pack CSVs in data/)
"""
import pandas as pd, numpy as np, re, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
D=str(ROOT/'data')+'/'
(ROOT/'out').mkdir(exist_ok=True); T=pd.Timestamp('2026-09-30')
reg=pd.read_csv(D+'kijana_water_point_register.csv')
jc=pd.read_csv(D+'kijana_repair_job_cards.csv',parse_dates=['date_reported','date_repaired','breakdown_date_est'])
ins=pd.read_csv(D+'kijana_inspection_visits.csv',parse_dates=['visit_date'])
sv=pd.read_csv(D+'kijana_verification_survey_2025.csv',parse_dates=['visit_date'])
wc=pd.read_csv(D+'kijana_water_committees.csv',parse_dates=['last_meeting'])
wq=pd.read_csv(D+'kijana_water_quality_results.csv',parse_dates=['sample_date'])
st=pd.read_csv(D+'kijana_settlements.csv')
msg=pd.read_csv(D+'kijana_community_messages.csv',parse_dates=['received_at'])
rain=pd.read_csv(D+'kijana_rainfall_by_subcounty_monthly.csv')
ids=set(reg.wp_id)
def norm(x):
    m=re.search(r'(\d{1,4})',str(x)); 
    return f'KJ-WP-{int(m.group(1)):04d}' if m else None
jc['wp']=jc.wp_id.where(jc.wp_id.isin(ids), jc.wp_id.map(norm))
wq['wp']=wq.water_point_ref.map(norm)
# ---- message -> wp resolution (ID in text, else village name -> single-wp settlement or first wp)
reg_set=reg.merge(st[['settlement_id','name']],on='settlement_id',how='left')
name2wp=reg_set.groupby(reg_set.name.str.lower())['wp_id'].apply(list).to_dict()
names=sorted([n for n in name2wp if isinstance(n,str) and len(n)>3],key=len,reverse=True)
pat=re.compile(r'\b('+'|'.join(map(re.escape,names))+r')\b')
def resolve(t):
    t=str(t); m=re.search(r'KJ-WP-\d{4}',t)
    if m: return m.group(0), 'id'
    m=pat.search(t.lower())
    if m:
        l=name2wp[m.group(1)]; return l[0], ('village' if len(l)==1 else 'village-ambiguous')
    return None,None
msg[['wp','res']]=msg.text.apply(lambda t: pd.Series(resolve(t)))
low=msg.text.str.lower()
def cat(t):
    t=t.lower()
    if re.search(r'chafu|dirty|smell|harufu|kutu|rangi|colou?r|taste|ladha|tumbo|diarr|kuhara',t): return 'quality'
    if re.search(r'kidogo|slow|many strokes|long to|takes long|polepole',t): return 'slow_flow'
    if re.search(r'\bdry\b|imekauka|kavu',t): return 'dry'
    if re.search(r'fixed|imetengenezwa|inafanya kazi|working now|repaired|imerekebishwa',t): return 'fixed'
    if re.search(r'still waiting|bado|when will|reported \d+ weeks',t): return 'follow_up'
    if re.search(r'not working|broke|imeharibika|imekufa|mbovu|hakuna maji|no water|haitoi|spoilt|loose|imevunjika',t): return 'breakdown'
    if re.search(r'flood|mafuriko',t): return 'flood'
    return 'other'
msg['cat']=msg.text.apply(cat)
# ---- status events
ev=[]
for r in reg.itertuples(): ev.append((r.wp_id,pd.Timestamp(r.status_date),r.status_recorded,'register'))
for r in ins.itertuples(): ev.append((r.wp_id,r.visit_date,r.status_observed,'inspection'))
for r in sv.itertuples(): ev.append((r.wp_id,r.visit_date,r.status_observed,'survey'))
b=jc[jc.repair_type!='preventive service']
for r in b.itertuples():
    if r.wp in ids:
        ev.append((r.wp,r.date_reported,'Non-functional','job opened'))
        if pd.notna(r.date_repaired): ev.append((r.wp,r.date_repaired,'Functional','job closed'))
for r in msg[msg.wp.notna()].itertuples():
    if r.cat in('breakdown','follow_up'): ev.append((r.wp,r.received_at,'Non-functional','committee SMS'))
    if r.cat=='fixed': ev.append((r.wp,r.received_at,'Functional','committee SMS'))
    if r.cat=='dry': ev.append((r.wp,r.received_at,'Seasonal (dry)','committee SMS'))
E=pd.DataFrame(ev,columns=['wp','date','status','src']).dropna(subset=['date']).sort_values('date')
last=E.groupby('wp').tail(1).set_index('wp')
# ---- components
out=reg[['wp_id','wp_name','sub_county','settlement_id','source_type_recorded','technology_recorded','design_population','rising_main_material','install_year','committee_id']].copy().set_index('wp_id')
out['status_now']=last.status; out['status_date']=last.date; out['status_src']=last.src
out['status_age_days']=(T-out.status_date).dt.days
# A. Service status (35)
def A(r):
    s,a=r.status_now,r.status_age_days
    if s=='Functional': base=35
    elif s=='Seasonal (dry)': base=15
    else: base=0
    if s=='Functional' and a>365: base=25
    if s=='Functional' and a>730: base=18
    return base
out['A_status']=out.apply(A,axis=1)
# B. Reliability (20): breakdowns per year since 2021 and median repair days
bb=b[b.wp.isin(ids)].copy(); bb['days']=(bb.date_repaired-bb.date_reported).dt.days
g=bb.groupby('wp').agg(breakdowns=('job_id','count'),med_repair_days=('days','median'),open_jobs=('date_repaired',lambda s: s.isna().sum()))
out=out.join(g); out[['breakdowns','open_jobs']]=out[['breakdowns','open_jobs']].fillna(0)
yrs=5.75
out['B_reliability']=(12-np.clip(out.breakdowns/yrs*4,0,12)) + (8-np.clip(out.med_repair_days.fillna(30)/15,0,8))
# C. Management & money (15)
w=wc.set_index('wp_id')
out=out.join(w[['tariff_model','avg_monthly_collection_usd_2025','savings_balance_usd','last_meeting','service_agreement']])
tm={'Monthly flat fee':5,'Pay per container':5,'Collect when broken':2,'No tariff':0}
def C(r):
    if pd.isna(r.tariff_model): return 10  # piped/solar: operator-run, neutral
    s=tm.get(r.tariff_model,0)
    s+=3 if (r.savings_balance_usd or 0)>=50 else (1 if (r.savings_balance_usd or 0)>0 else 0)
    s+=3 if pd.notna(r.last_meeting) and (T-r.last_meeting).days<=180 else 0
    s+=4 if r.service_agreement=='yes' else 0
    return s
out['C_management']=out.apply(C,axis=1)
# D. Water quality (15): latest result
q=wq[wq.wp.isin(ids)].sort_values('sample_date').groupby('wp').tail(1).set_index('wp')
out=out.join(q[['sample_date','ecoli_cfu_per_100ml','fluoride_mg_l','nitrate_mg_l']])
qc=msg[msg.cat=='quality'].groupby('wp').received_at.max()
out['last_quality_complaint']=qc
def Dq(r):
    if pd.isna(r.sample_date): s=8
    else:
        s=15
        if (r.ecoli_cfu_per_100ml or 0)>0: s-=10
        if (r.fluoride_mg_l or 0)>1.5: s-=5
        if (r.nitrate_mg_l or 0)>50: s-=5
        if (T-r.sample_date).days>730: s=min(s,10)
    if pd.notna(r.last_quality_complaint) and (T-r.last_quality_complaint).days<=365: s=min(s,5)
    return max(s,0)
out['D_quality']=out.apply(Dq,axis=1)
# E. Source & climate (15): sub-county rainfall anomaly last 6 months; shallow wells more exposed; recent dry reports
r6=rain[rain.month>='2026-04'].groupby('sub_county').anomaly_pct_vs_2014_2020.mean()
out['rain_anom_6m']=out.sub_county.map(r6)
shallow=out.source_type_recorded.str.contains('shallow|hand|hdw',case=False,na=False)
dry=msg[msg.cat=='dry'].groupby('wp').received_at.max()
out['last_dry_report']=dry
def Ec(r,sh):
    s=15+min(0,r.rain_anom_6m)/(4 if sh else 8)
    if pd.notna(r.last_dry_report) and (T-r.last_dry_report).days<=365: s-=6
    return float(np.clip(s,0,15))
out['E_source']=[Ec(r,sh) for r,sh in zip(out.itertuples(),shallow)]
# each dimension scaled to 20 points (equal weights)
out['A_status']=out.A_status*20/35
out['C_management']=out.C_management*20/15
out['D_quality']=out.D_quality*20/15
out['E_source']=out.E_source*20/15
for c in ['A_status','B_reliability','C_management','D_quality','E_source']: out[c]=out[c].round(1)
out['score']=(out.A_status+out.B_reliability+out.C_management+out.D_quality+out.E_source).round().astype(int)
# confidence (separate from score): how fresh/varied the evidence is
recent_msg=msg[(msg.received_at>=T-pd.Timedelta(days=365))].groupby('wp').size()
out['msgs_12m']=recent_msg; out['msgs_12m']=out.msgs_12m.fillna(0)
out=out.join(st.set_index('settlement_id')[['network_coverage','population_2026','nearest_active_mechanic_id','travel_min_to_mechanic_wet']],on='settlement_id')
def conf(r):
    if r.status_age_days<=180: return 'High'
    if r.status_age_days<=540 or r.msgs_12m>0: return 'Medium'
    return 'Low'
out['confidence']=out.apply(conf,axis=1)
# actions
def acts(r):
    a=[]
    if r.status_now!='Functional' and r.open_jobs==0: a.append(f'Dispatch mechanic {r.nearest_active_mechanic_id} (~{int(r.travel_min_to_mechanic_wet) if pd.notna(r.travel_min_to_mechanic_wet) else "?"} min wet season)')
    if r.open_jobs>0: a.append('Chase open job card')
    if r.D_quality<=6.7: a.append('Boil-water advice + retest E. coli')
    if r.confidence=='Low': a.append('Inspect: no fresh evidence (silent point)')
    if r.C_management<=5.3 and pd.notna(r.tariff_model): a.append('Committee support: tariff/savings')
    if r.E_source<=10.7: a.append('Seasonal-dry watch')
    if r.rising_main_material=='GI' and r.breakdowns>=4: a.append('Plan preventive rising-main swap')
    return '; '.join(a) or 'No action'
out['actions']=out.apply(acts,axis=1)
out['band']=pd.cut(out.score,[-1,39,59,79,100],labels=['Critical','At risk','Watch','Good']).astype(str)
# simple rule: any point not working is flagged and goes to the top of the list, whatever its score
out['flag']=np.where(out.status_now!='Functional','Not working','')
out['priority']=np.where(out.flag=='Not working',0,1)
out=out.sort_values(['priority','score'])
out.to_csv(str(ROOT/'out'/'water_point_scores.csv'))
print(out.band.value_counts().sort_index())
print(out.confidence.value_counts())
print(out.status_src.value_counts())
print('msgs resolved', msg.res.value_counts(dropna=False).to_dict(), msg.cat.value_counts().to_dict())
print(out.score.describe())
print(out.sort_values('score')[['wp_name','sub_county','score','status_now','status_src','confidence','actions']].head(8).to_string())
print(out[['A_status','B_reliability','C_management','D_quality','E_source']].mean().round(1))
