#!/usr/bin/env python3
"""Run the data preparation, analysis, and validation stages."""
from pathlib import Path
import subprocess
import sys

SCRIPTS = Path(__file__).resolve().parent
STAGES = [
    '01_analyze.py',
    '02_segment_preferences.py',
    '06_quality_audit.py',
    '07_export_low_sample.py',
    '13_recruiter_business_analysis.py',
    '14_export_operating_lists.py',
    '04_verify.py',
]

for name in STAGES:
    print(f'\nRunning {name}', flush=True)
    subprocess.run([sys.executable, str(SCRIPTS / name)], check=True)
