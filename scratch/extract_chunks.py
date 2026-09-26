import json
import glob

files = glob.glob('audit_reports/Audit_Report_Zomato_*.json')
files.sort(key=lambda x: x, reverse=True)
with open(files[0], 'r', encoding='utf-8') as f:
    data = json.load(f)

for slide in data['slide_audits']:
    for claim in slide['claims']:
        if claim['verdict'] == 'unsupported':
            c_text = claim.get('claim_text', '')
            print(f"CLAIM: {c_text.encode('ascii', 'ignore').decode()}")
            print(f"SOURCE: {claim.get('source_clause').encode('ascii', 'ignore').decode()}")
            print(f"RATIONALE: {claim.get('notes').encode('ascii', 'ignore').decode()}")
            print('-'*40)
