"""Build data/indicators.csv and data/trend.csv from the CIHI extracts.

Reads the rows under data/source/ and writes the two derived datasets the
dashboard reads. Run from the repository root:

    python3 scripts/build_cihi.py            # uses ./data
    python3 scripts/build_cihi.py /some/dir  # uses /some/dir/data
"""

import csv, os, sys, collections

ROOT = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'data')
RAW = os.path.join(DATA, 'source')

SHORT = {
 '30-Day Acute Myocardial Infarction In-Hospital Mortality': '30-day AMI in-hospital mortality',
 '30-Day Stroke In-Hospital Mortality': '30-day stroke in-hospital mortality',
 'All Patients Readmitted to Hospital': 'Readmission, all patients',
 'Medical Patients Readmitted to Hospital': 'Readmission, medical',
 'Surgical Patients Readmitted to Hospital': 'Readmission, surgical',
 'Obstetric Patients Readmitted to Hospital': 'Readmission, obstetric',
 'Pediatric Patients Readmitted to Hospital': 'Readmission, pediatric',
 'Hip Fracture Surgery Within 48 Hours': 'Hip fracture surgery within 48 hours',
 'Hospital Deaths (HSMR)': 'Hospital deaths (HSMR)',
 'Hospital Deaths Following Major Surgery': 'Deaths after major surgery',
 'In-Hospital Sepsis': 'In-hospital sepsis',
 'Low-Risk Caesarean Section Rate': 'Low-risk C-section rate',
 'Obstetric Trauma (With Instrument)': 'Obstetric trauma, with instrument',
 'Obstetric Trauma (Without Instrument)': 'Obstetric trauma, no instrument',
 'Emergency Department Wait Time for Physician Initial Assessment': 'ED wait to physician, 90th percentile',
 'Total Time Spent in Emergency Department for Admitted Patients': 'ED time for admitted patients, 90th percentile',
 'Cost of a Standard Hospital Stay': 'Cost of a standard hospital stay',
 'Patient Days in Alternate Level of Care (Percentage)': 'Patient days in alternate level of care',
 'Average Acute Occupancy Rate': 'Acute occupancy rate',
 'Average Length of a Hospital Stay (Days)': 'Average length of stay',
 'Patients Admitted Through the Emergency Department': 'Admitted through the emergency department',
 'Hospitalized Seniors at Risk of Frailty': 'Hospitalized seniors at risk of frailty',
 'Number of Emergency Department Visits': 'Emergency department visits',
 'Number of Acute Care Hospital Stays': 'Acute care hospital stays',
 'Number of Acute Care Beds': 'Acute care beds',
}
CONTEXT = {'Patient Days in Alternate Level of Care (Percentage)', 'Average Acute Occupancy Rate',
           'Average Length of a Hospital Stay (Days)', 'Patients Admitted Through the Emergency Department',
           'Hospitalized Seniors at Risk of Frailty', 'Number of Emergency Department Visits',
           'Number of Acute Care Hospital Stays', 'Number of Acute Care Beds'}
CAT = {
 'Health system outputs: Safe': 'Safe',
 'Health system outputs: Appropriate and effective': 'Appropriate and effective',
 'Health system outputs: Access to comprehensive, high-quality health services': 'Access to high-quality services',
 'Health system outputs: Efficiently delivered': 'Efficiently delivered',
}
UNIT_BY_INDICATOR = {
 'Average Length of a Hospital Stay (Days)': 'days',
 'Number of Acute Care Beds': 'beds',
 'Number of Acute Care Hospital Stays': 'stays',
 'Hospitalized Seniors at Risk of Frailty': '%',
 'Hospital Deaths (HSMR)': 'ratio, Canada = 100',
}
UNIT = {'Per 100': 'per 100', 'Per 1,000': 'per 1,000', 'Percent': '%', 'Hours': 'hours',
        'Hour': 'hours', 'Dollars': 'dollars', 'NaN': '', 'Hospitalizations': 'hospitalizations',
        'Visits': 'visits', 'People': 'people', 'Days': 'days', 'Beds': 'beds'}

def ident(name):
    out = ''.join(ch if ch.isalnum() else '_' for ch in name.lower())
    while '__' in out: out = out.replace('__', '_')
    return out.strip('_')[:60]

def num(v):
    if v in ('', 'NaN', 'Suppressed', 'Not available', None): return None
    try: return float(v.replace(',', ''))
    except ValueError: return None

meta = {r['indicator']: r for r in csv.DictReader(open(os.path.join(RAW, 'indicator-meta.csv'), encoding='utf-8'))}

_all = [r for r in csv.DictReader(open(os.path.join(RAW, 'cihi-cmh-rows.csv'), encoding='utf-8-sig'))
        if r['Main metric'] == 'Yes' and r['Breakdowns'] == 'Not applicable']
_corp = {r['Indicator'] for r in _all if r['Reporting level'] == 'Corporation'}
# CIHI reports a few measures only against the physical site, not the corporation
cmh = [r for r in _all if r['Reporting level'] == 'Corporation'
       or (r['Reporting level'] == 'Facility' and r['Indicator'] not in _corp)]

bench = collections.defaultdict(dict)
for r in csv.DictReader(open(os.path.join(RAW, 'cihi-benchmark-rows.csv'), encoding='utf-8-sig')):
    if r['Main metric'] == 'Yes' and r['Breakdowns'] == 'Not applicable':
        bench[(r['Indicator'], r['Place or organization'])][r['Time frame']] = r['Metric value']

groups = collections.defaultdict(list)
for r in cmh: groups[r['Indicator']].append(r)

ind_rows, trend_rows = [], []
for name, rs in groups.items():
    if name not in SHORT: continue
    rs.sort(key=lambda r: r['Time frame'])
    latest = rs[-1]
    m = meta.get(name, {})
    dim = m.get('dimension', '')
    cat = 'Context' if name in CONTEXT else CAT.get(dim, 'Context')
    interp = m.get('interpretation', '')
    direction = 'higher' if 'Higher rates are desirable' in interp else 'lower'
    if cat == 'Context': direction = 'none'
    iid = ident(name)
    ca = bench.get((name, 'Canada'), {})
    on = bench.get((name, 'Ontario'), {})
    prior = rs[-2] if len(rs) > 1 else None
    ind_rows.append({
      'id': iid, 'category': cat, 'short': SHORT[name], 'indicator': name,
      'dimension': dim, 'metric': latest['Metric'],
      'unit': UNIT_BY_INDICATOR.get(name) or ('%' if latest['Metric'] == 'Percent' else UNIT.get(latest['Unit of measure'], '')),
      'direction': direction, 'measure_type': latest['Measure type'],
      'year': latest['Time frame'].replace('–', '-'),
      'value': latest['Metric value'].replace(',', '') if num(latest['Metric value']) is not None else '',
      'suppressed': 'yes' if latest['Metric value'] == 'Suppressed' else '',
      'ci_low': latest['Confidence interval lower limit'] if num(latest['Confidence interval lower limit']) is not None else '',
      'ci_high': latest['Confidence interval upper limit'] if num(latest['Confidence interval upper limit']) is not None else '',
      'cihi_comparison': '' if latest['Performance comparison'] in ('NaN', '') else latest['Performance comparison'],
      'cihi_trend': '' if latest['Performance trend'] in ('NaN', '') else latest['Performance trend'],
      'top_result': '' if latest['Top results'] in ('NaN', '') else latest['Top results'],
      'stat_diff': '' if latest['Statistically different'] in ('NaN', '') else latest['Statistically different'],
      'canada': (ca.get(latest['Time frame'], '') or '').replace(',', ''),
      'ontario': (on.get(latest['Time frame'], '') or '').replace(',', ''),
      'prior_year': prior['Time frame'].replace('–', '-') if prior else '',
      'prior_value': prior['Metric value'].replace(',', '') if prior and num(prior['Metric value']) is not None else '',
      'first_year': rs[0]['Time frame'].replace('–', '-'),
      'years_of_data': str(len(rs)),
      'peer_group': latest['Hospital peer group'],
      'interpretation': interp, 'description': m.get('description', ''), 'slug': m.get('slug', ''),
    })
    for r in rs:
        tf = r['Time frame']
        if num(r['Metric value']) is None: continue
        trend_rows.append({'id': iid, 'short': SHORT[name], 'category': cat,
          'year': tf.replace('–', '-'), 'value': r['Metric value'].replace(',', ''),
          'canada': (ca.get(tf, '') or '').replace(',', '') if num(ca.get(tf, '')) is not None else '',
          'ontario': (on.get(tf, '') or '').replace(',', '') if num(on.get(tf, '')) is not None else '',
          'cihi_comparison': '' if r['Performance comparison'] in ('NaN', '') else r['Performance comparison']})

order = {'Safe': 0, 'Appropriate and effective': 1, 'Access to high-quality services': 2,
         'Efficiently delivered': 3, 'Context': 4}
ind_rows.sort(key=lambda r: (order[r['category']], r['short']))
trend_rows.sort(key=lambda r: (order[r['category']], r['short'], r['year']))

for fn, data in (('indicators.csv', ind_rows), ('trend.csv', trend_rows)):
    p = os.path.join(DATA, fn)
    w = csv.DictWriter(open(p, 'w', newline='', encoding='utf-8'), fieldnames=list(data[0].keys()))
    w.writeheader(); w.writerows(data)
    print(f"{fn}: {len(data)} rows, {os.path.getsize(p)} bytes")

print()
for r in ind_rows:
    print(f"{r['category'][:26]:<28}{r['short'][:44]:<46}{r['year']}  {r['value'] or 'SUPPRESSED':>9} {r['unit'][:10]:<10} ON={r['ontario'] or '-':>7} CA={r['canada'] or '-':>7}  {r['cihi_comparison'][:28]:<30}{r['cihi_trend']}")
