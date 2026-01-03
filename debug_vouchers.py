"""
Diagnostic script to debug voucher sync issues
Run this on your server with: bench --site <your-site> console < debug_vouchers.py
"""

import frappe
import json
from tally_erpnext.tally.client import TallyClient

frappe.connect()

print("\n" + "="*80)
print("TALLY VOUCHER SYNC DIAGNOSTIC")
print("="*80)

# Step 1: Check Tally Settings
print("\n1. Checking Tally Settings...")
try:
    settings = frappe.get_doc("Tally Settings", "Tally Settings")
    print(f"   ✓ Tally enabled: {settings.enabled}")
    print(f"   ✓ Host: {settings.host}:{settings.port}")
    print(f"   ✓ Default company: {settings.get('default_company')}")
except Exception as e:
    print(f"   ✗ Error getting settings: {e}")
    exit(1)

# Step 2: Test Tally Connection
print("\n2. Testing Tally connection...")
try:
    client = TallyClient()
    conn_test = client.test_connection()
    print(f"   {'✓' if conn_test else '✗'} Connection test: {conn_test}")
except Exception as e:
    print(f"   ✗ Connection failed: {e}")
    exit(1)

# Step 3: Get company name
print("\n3. Getting company info...")
try:
    company_info = client.get_current_company()
    company_name = company_info.get("name") if company_info else settings.get('default_company')
    print(f"   ✓ Company name: {company_name}")
except Exception as e:
    print(f"   ⚠ Warning: {e}")
    company_name = settings.get('default_company')
    print(f"   Using default: {company_name}")

# Step 4: Try to fetch vouchers with different parameters
print("\n4. Attempting to fetch vouchers...")
print(f"   Testing with voucher_type='Sales', last 30 days")

try:
    vouchers = client.get_vouchers(
        voucher_type="Sales",
        from_date=None,  # Will default to last 30 days
        to_date=None,
        company_name=company_name
    )

    print(f"   ✓ Fetched {len(vouchers)} vouchers")

    if len(vouchers) == 0:
        print("\n   ⚠ No vouchers returned. This could mean:")
        print("      - No Sales vouchers in Tally for the last 30 days")
        print("      - Incorrect company name")
        print("      - XML request issue")

        # Show XML request/response
        xml_request = client.get_last_xml_request()
        xml_response = client.get_last_xml_response()

        print("\n   Last XML Request:")
        print("   " + "-"*76)
        if xml_request:
            for line in xml_request.split('\n')[:20]:  # First 20 lines
                print(f"   {line}")
            if len(xml_request.split('\n')) > 20:
                print("   ... (truncated)")

        print("\n   Last XML Response (first 500 chars):")
        print("   " + "-"*76)
        if xml_response:
            print(f"   {xml_response[:500]}")
            if len(xml_response) > 500:
                print("   ... (truncated)")

    else:
        print(f"\n   ✓ SUCCESS! Found {len(vouchers)} voucher(s)")
        print("\n   First voucher details:")
        print("   " + "-"*76)
        first = vouchers[0]
        print(f"   Voucher Type: {first.get('voucher_type')}")
        print(f"   Voucher Number: {first.get('voucher_number')}")
        print(f"   Date: {first.get('date')}")
        print(f"   GUID: {first.get('guid')}")
        print(f"   Party Ledger: {first.get('party_ledger')}")
        print(f"   Narration: {first.get('narration', '')[:50]}")
        print(f"   Ledger Entries: {len(first.get('ledger_entries', []))}")

        if first.get('ledger_entries'):
            print("\n   Ledger Entries:")
            for i, entry in enumerate(first.get('ledger_entries', [])[:3], 1):
                print(f"     {i}. {entry.get('ledger_name')}: {entry.get('amount')} ({'Dr' if entry.get('is_debit') else 'Cr'})")
            if len(first.get('ledger_entries', [])) > 3:
                print(f"     ... and {len(first.get('ledger_entries', [])) - 3} more")

except Exception as e:
    print(f"   ✗ Error fetching vouchers: {e}")
    import traceback
    print("\n   Full traceback:")
    print("   " + "-"*76)
    traceback.print_exc()

# Step 5: Check existing Tally Vouchers in DB
print("\n5. Checking existing Tally Vouchers in database...")
try:
    existing_count = frappe.db.count("Tally Voucher")
    print(f"   Found {existing_count} existing Tally Vouchers in database")

    if existing_count > 0:
        recent = frappe.get_all("Tally Voucher",
            fields=["name", "voucher_type", "voucher_number", "sync_status", "modified"],
            order_by="modified desc",
            limit=3
        )
        print("\n   Most recent vouchers:")
        for v in recent:
            print(f"     - {v.name}: {v.voucher_type} {v.voucher_number} ({v.sync_status})")
except Exception as e:
    print(f"   ✗ Error checking database: {e}")

# Step 6: Check sync logs
print("\n6. Checking Tally Sync Logs for vouchers...")
try:
    logs = frappe.get_all("Tally Sync Log",
        filters={"entity_type": "Voucher"},
        fields=["name", "status", "operation", "sync_date", "error_message"],
        order_by="sync_date desc",
        limit=5
    )

    if len(logs) == 0:
        print("   No voucher sync logs found")
    else:
        print(f"   Found {len(logs)} recent voucher sync log(s):")
        for log in logs:
            status_icon = "✓" if log.status == "Success" else "✗"
            print(f"   {status_icon} {log.name}: {log.status} | {log.operation} | {log.sync_date}")
            if log.error_message:
                print(f"      Error: {log.error_message[:100]}")
except Exception as e:
    print(f"   ✗ Error checking logs: {e}")

print("\n" + "="*80)
print("DIAGNOSTIC COMPLETE")
print("="*80)
print("\nPlease share this entire output for analysis.\n")

frappe.db.rollback()
