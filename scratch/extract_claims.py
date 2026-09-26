import json
import glob
import os

files = glob.glob('audit_reports/Audit_Report_Zomato_*.json')
files.sort(key=lambda x: x, reverse=True)
zomato_file = files[0]

with open(zomato_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

for slide in data['slide_audits']:
    for claim in slide['claims']:
        if claim['verdict'] == 'unsupported':
            print(f"CLAIM: {claim.get('claim_text').encode('ascii', 'ignore').decode()}")
            print(f"RATIONALE: {claim.get('notes').encode('ascii', 'ignore').decode()}")
            print('-'*40)
