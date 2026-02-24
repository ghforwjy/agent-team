
"""
Test legal and finance agents with real data
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from skills.legal_skills import (
    review_contract, assess_legal_risk, triage_nda, compliance_check
)
from skills.finance_skills import (
    generate_financial_statements, analyze_variance, prepare_journal_entry, reconcile_accounts
)

def test_legal_with_real_contract():
    print("=" * 70)
    print("TESTING LEGAL SKILLS WITH REAL CONTRACT DATA")
    print("=" * 70)
    
    contract_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'sample_contract.txt')
    
    with open(contract_file, 'r') as f:
        contract_text = f.read()
    
    print("\n1. Testing contract review...")
    result = review_contract(contract_text)
    print(result)
    
    print("\n2. Testing legal risk assessment...")
    result = assess_legal_risk("Potential breach of contract regarding intellectual property rights")
    print(result)
    
    print("\n3. Testing NDA triage...")
    result = triage_nda(contract_text)
    print(result)
    
    print("\n4. Testing compliance check...")
    result = compliance_check("Check data protection compliance for this software development agreement")
    print(result)
    
    print("\n✅ Legal skills with real data test completed!")


def test_finance_with_real_data():
    print("\n" + "=" * 70)
    print("TESTING FINANCE SKILLS WITH REAL FINANCIAL DATA")
    print("=" * 70)
    
    print("\n1. Testing financial statement generation...")
    result = generate_financial_statements("Tech Innovations Corp", "Q4 2024")
    print(result)
    
    print("\n2. Testing variance analysis...")
    result = analyze_variance(1500000, 1600000)
    print(result)
    
    print("\n3. Testing journal entry preparation...")
    result = prepare_journal_entry("Record Q4 2024 revenue", ["Accounts Receivable", "Revenue"])
    print(result)
    
    print("\n4. Testing account reconciliation...")
    result = reconcile_accounts("Bank Account", 850000, 848500)
    print(result)
    
    print("\n✅ Finance skills with real data test completed!")


if __name__ == "__main__":
    test_legal_with_real_contract()
    test_finance_with_real_data()
    print("\n" + "=" * 70)
    print("All real scenario tests completed!")
    print("=" * 70)

