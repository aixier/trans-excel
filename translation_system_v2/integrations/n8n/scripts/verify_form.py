#!/usr/bin/env python3
"""
Form Workflow Verification Script
验证表单工作流配置是否正确
"""

import requests
import json
from config import get_api_headers

def main():
    headers = get_api_headers()
    workflow_id = "1xQAR3UTNGrk0X6B"

    print("=" * 60)
    print("Form Workflow Verification (表单工作流验证)")
    print("=" * 60)
    print()

    # 1. Get workflow info
    print("1️⃣  Fetching workflow...")
    response = requests.get(f'http://localhost:5678/api/v1/workflows/{workflow_id}', headers=headers)

    if response.status_code != 200:
        print(f"❌ Failed to fetch workflow: {response.status_code}")
        return

    workflow = response.json()
    print(f"✅ Workflow found: {workflow['name']}")
    print(f"   Active: {workflow.get('active', False)}")
    print()

    # 2. Check Form Trigger configuration
    print("2️⃣  Checking Form Trigger configuration...")
    form_nodes = [n for n in workflow['nodes'] if n['type'] == 'n8n-nodes-base.formTrigger']

    if not form_nodes:
        print("❌ No Form Trigger node found!")
        return

    form_node = form_nodes[0]
    webhook_id = form_node.get('webhookId', '')
    path = form_node['parameters'].get('path', '')
    response_mode = form_node['parameters'].get('responseMode', '')

    print(f"   Name: {form_node['name']}")
    print(f"   Path: {path}")
    print(f"   Response Mode: {response_mode}")
    print(f"   Webhook ID: {webhook_id if webhook_id else '(empty - need UI save)'}")
    print()

    # 3. Check Process Form Data node
    print("3️⃣  Checking Process Form Data node...")
    code_nodes = [n for n in workflow['nodes'] if n['name'] == 'Process Form Data']

    if code_nodes:
        code = code_nodes[0]['parameters']['jsCode']
        if 'binary: $input.item.binary' in code:
            print("   ✅ Binary pass-through: Correct")
        else:
            print("   ⚠️  Binary pass-through: Needs checking")
            print("      Should contain: binary: $input.item.binary")
    else:
        print("   ❌ Process Form Data node not found")
    print()

    # 4. Check HTTP Request node
    print("4️⃣  Checking Upload & Split Tasks node...")
    http_nodes = [n for n in workflow['nodes'] if n['name'] == 'Upload & Split Tasks']

    if http_nodes:
        params = http_nodes[0]['parameters']['bodyParameters']['parameters']
        file_param = [p for p in params if p['name'] == 'file']

        if file_param:
            file_value = file_param[0]['value']
            print(f"   File parameter: {file_value}")

            if "$binary['Excel 文件']" in file_value:
                print("   ✅ Binary reference: Correct (specific field name)")
            elif "Object.values($binary)[0]" in file_value:
                print("   ⚠️  Binary reference: Alternative method (works but less specific)")
            else:
                print("   ❌ Binary reference: Incorrect")
                print("      Should be: {{ $binary['Excel 文件'] }}")
    else:
        print("   ❌ Upload & Split Tasks node not found")
    print()

    # 5. Test webhook accessibility
    print("5️⃣  Testing webhook accessibility...")

    if webhook_id:
        form_url = f"http://localhost:5678/form/{webhook_id}"
        print(f"   Form URL: {form_url}")

        try:
            test_response = requests.get(form_url, timeout=5)

            if test_response.status_code == 200:
                if "Problem loading form" in test_response.text:
                    print("   ❌ Webhook NOT registered")
                    print("   📝 Action needed: Open workflow in n8n UI and click Save")
                    print(f"      URL: http://localhost:5678/workflow/{workflow_id}")
                else:
                    print("   ✅ Form is accessible!")
                    print(f"   🎉 You can test the form at: {form_url}")
            else:
                print(f"   ⚠️  Unexpected status code: {test_response.status_code}")
        except Exception as e:
            print(f"   ❌ Failed to access form: {e}")
    else:
        print("   ⚠️  No webhook ID - workflow needs to be saved in UI")
        print(f"   📝 Action: Open http://localhost:5678/workflow/{workflow_id} and click Save")
    print()

    # 6. Summary
    print("=" * 60)
    print("Summary (总结)")
    print("=" * 60)

    if webhook_id and form_nodes and code_nodes and http_nodes:
        print("✅ Configuration looks good!")
        print()
        print("Next steps:")
        print("1. If webhook is not registered:")
        print(f"   - Open: http://localhost:5678/workflow/{workflow_id}")
        print("   - Click the Save button (💾)")
        print("   - Run this script again to verify")
        print()
        print("2. Test the form:")
        if webhook_id:
            print(f"   - Access: http://localhost:5678/form/{webhook_id}")
        print("   - Upload an Excel file")
        print("   - Select target language (EN)")
        print("   - Submit and wait for result")
    else:
        print("⚠️  Some configuration issues detected")
        print("Please review the checks above")
    print()

if __name__ == '__main__':
    main()
