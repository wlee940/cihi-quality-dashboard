"""Build data/targets.csv from Cambridge Memorial Hospital's published QIP workplans.

The figures below are transcribed from the hospital's Quality Improvement Plan
workplans and are deliberately left exactly as published rather than recalculated
against CIHI's series. Extract the PDFs with scripts/pdftxt.py and inspect the
indicator blocks with scripts/parse_qip.py if you need to re-check them.

    2026/27 workplan, Org ID 661, report access date March 30, 2026
    2025/26 workplan, Org ID 661, report access date March 28, 2025

Usage: python3 scripts/build_targets.py data/targets.csv
"""

import csv
import sys

ROWS = [
    dict(
        id='offload', qip_num='1',
        short='Ambulance offload time, 90th percentile',
        indicator='90th percentile ambulance offload time',
        qip_type='Provincial priority', unit='minutes', direction='lower',
        source='CIHI NACRS', period='Dec 1, 2024 to Nov 30, 2025',
        current='36.00', target='30.00',
        target_justification=(
            'There has been great success achieved with this metric over the past year '
            'and periods where target of 30 minutes has been achieved. Fiscal 2026/27 '
            'will solidify processes and work on sustainability.'
        ),
        exec_comp='Yes', p4r='Yes',
        prior_current='100.00', prior_target='43.00',
        prior_period='Dec 1, 2023 to Nov 30, 2024',
        cihi_id='',
    ),
    dict(
        id='pia', qip_num='2',
        short='ED wait to physician, 90th percentile',
        indicator='90th percentile emergency department wait time to physician initial assessment',
        qip_type='Provincial priority', unit='hours', direction='lower',
        source='CIHI NACRS', period='Dec 1, 2024 to Nov 30, 2025',
        current='7.40', target='4.50',
        target_justification='Average performance of regional partners.',
        exec_comp='Yes', p4r='Yes',
        prior_current='7.40', prior_target='4.60',
        prior_period='Dec 1, 2023 to Nov 30, 2024',
        # the one commitment with a matching indicator in CIHI's library
        cihi_id='emergency_department_wait_time_for_physician_initial_assessm',
    ),
    dict(
        id='bedwait', qip_num='3',
        short='Patients waiting for an inpatient bed at 8 a.m.',
        indicator=(
            'Daily average number of patients waiting in the emergency department '
            'for an inpatient bed at 8 a.m.'
        ),
        qip_type='Provincial priority', unit='patients', direction='lower',
        source='CIHI NACRS', period='Apr 1, 2024 to Mar 31, 2025',
        current='11.56', target='9.15',
        target_justification=(
            '25% reduction from actual performance at the time target was set '
            '(January/February).'
        ),
        exec_comp='Yes', p4r='Yes',
        prior_current='', prior_target='', prior_period='',
        cihi_id='',
    ),
    dict(
        id='conservable', qip_num='4',
        short='Conservable bed days',
        indicator='Conservable bed days, acute medical inpatients',
        qip_type='Custom', unit='bed days per day', direction='lower',
        source='Hospital collected data', period='2025-26',
        current='34.20', target='27.00',
        target_justification=(
            'Target areas with the highest contribution towards conservable bed days '
            'to focus efforts.'
        ),
        exec_comp='Yes', p4r='No',
        prior_current='', prior_target='', prior_period='',
        cihi_id='',
    ),
    dict(
        id='ctas1', qip_num='5',
        short='CTAS-1 wait to physician, 90th percentile',
        indicator=(
            '90th percentile emergency department wait time to physician initial '
            'assessment for CTAS-1 patients'
        ),
        qip_type='Custom', unit='minutes', direction='lower',
        source='Hospital collected data', period='2025-26',
        current='31.00', target='30.00',
        target_justification=(
            'A substantial amount of work has occurred in fiscal 2025-26 to address the '
            'PIA time for the sickest patients (CTAS-1). Fiscal 2026-27 will solidify '
            'processes and sustainability, especially as the hospital transitions from a '
            'paper-based emergency department to a fully electronic health information '
            'system in Fall 2026.'
        ),
        exec_comp='Yes', p4r='No',
        prior_current='6.90', prior_target='4.00',
        prior_period='2025/26 cycle, CTAS 1 and 2 combined, hours',
        cihi_id='',
    ),
    dict(
        id='discharge_info', qip_num='6',
        short='Discharge information given to patients',
        indicator=(
            'Percentage of survey respondents who answered "completely" when asked '
            'whether they received enough information from hospital staff about what to '
            'do if they were worried about their condition or treatment after leaving '
            'the hospital'
        ),
        qip_type='Optional', unit='%', direction='higher',
        source='Local data collection', period='Most recent consecutive 12-month period',
        current='58.42', target='74.27',
        target_justification=(
            '25% improvement from baseline when the target was set (Jan/Feb 2026).'
        ),
        exec_comp='Yes', p4r='No',
        prior_current='', prior_target='', prior_period='',
        cihi_id='',
    ),
]

COLS = [
    'id', 'qip_num', 'short', 'indicator', 'qip_type', 'unit', 'direction',
    'source', 'period', 'current', 'target', 'target_justification',
    'exec_comp', 'p4r', 'prior_current', 'prior_target', 'prior_period', 'cihi_id',
]


def main(out_path):
    with open(out_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, COLS)
        writer.writeheader()
        for row in ROWS:
            writer.writerow({col: row.get(col, '') for col in COLS})
    print('wrote', out_path, len(ROWS), 'rows')


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'data/targets.csv')
