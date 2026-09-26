import requests
import json
import time

COMPANIES = ["Tata Steel"]
URL = "http://127.0.0.1:8000/generate-pitch"

def main():
    for company in COMPANIES:
        print(f"\n==============================================")
        print(f"Testing pipeline for: {company}")
        print(f"==============================================")
        
        payload = {"company_name": company}
        headers = {"Content-Type": "application/json"}
        
        try:
            start_time = time.time()
            response = requests.post(URL, json=payload, headers=headers, timeout=600)
            response.raise_for_status()
            
            data = response.json()
            audit = data.get("audit_report", {})
            
            print(f"Time taken: {time.time() - start_time:.2f}s")
            print(f"PPTX Deck: {data.get('deck_filename')}")
            
            # Print audit metrics
            overall_confidence = audit.get("overall_confidence", 0)
            overall_pass = audit.get("overall_pass", False)
            print(f"Overall Confidence: {overall_confidence:.2%}")
            print(f"Overall Pass: {overall_pass}")
            
            # Count claims
            supported = 0
            partially_supported = 0
            unsupported = 0
            unverifiable = 0
            
            total_claims = 0
            
            slides_audit = audit.get("slide_audits", [])
            for slide in slides_audit:
                for claim in slide.get("claims", []):
                    total_claims += 1
                    verdict = claim.get("verdict", "")
                    if verdict == "supported": supported += 1
                    elif verdict == "partially_supported": partially_supported += 1
                    elif verdict == "unsupported": unsupported += 1
                    elif verdict == "unverifiable": unverifiable += 1
                    
            print(f"Total Claims: {total_claims}")
            print(f" - Supported: {supported}")
            print(f" - Partially Supported: {partially_supported}")
            print(f" - Unsupported: {unsupported}")
            print(f" - Unverifiable: {unverifiable}")
            
            # Save 3 spot-check claims for the first company
            if company == "Infosys":
                print("\n--- SPOT CHECK (3 Claims) ---")
                count = 0
                for slide in slides_audit:
                    for claim in slide.get("claims", []):
                        if count >= 3:
                            break
                        c_text = claim.get('claim_text', '').encode('ascii', 'ignore').decode()
                        c_source = claim.get('source_clause', '').encode('ascii', 'ignore').decode()
                        print(f"\nClaim {count+1}: {c_text}")
                        print(f"Verdict: {claim.get('verdict')} (Score: {claim.get('confidence_score')})")
                        print(f"Source Text: {c_source}")
                        count += 1
                    if count >= 3:
                        break
            
        except requests.exceptions.RequestException as e:
            print(f"Failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(e.response.text)

if __name__ == "__main__":
    main()
