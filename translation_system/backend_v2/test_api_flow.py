"""Test full API flow with test2.xlsx file."""

import requests
import json
import time
import os
from pathlib import Path


def test_full_api_flow():
    """Test the complete API flow."""

    # Configuration
    BASE_URL = "http://localhost:8000"
    TEST_FILE = "/mnt/d/work/trans_excel/test2.xlsx"

    if not os.path.exists(TEST_FILE):
        print(f"❌ Test file not found: {TEST_FILE}")
        return

    print(f"\n{'='*60}")
    print("Testing Full API Flow")
    print(f"{'='*60}")
    print(f"File: {TEST_FILE}")
    print(f"API: {BASE_URL}")

    # Step 1: Upload and analyze Excel file
    print("\n1. Uploading and analyzing Excel file...")

    with open(TEST_FILE, 'rb') as f:
        files = {'file': ('test2.xlsx', f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}

        # Prepare game info
        game_info = {
            "game_type": "MMORPG",
            "world_view": "Fantasy martial arts world with cultivation system",
            "target_regions": ["TH", "PT", "VN"],
            "game_style": "Realistic",
            "additional_context": "Mobile MMORPG with turn-based combat, focus on PvP"
        }

        data = {
            'game_info': json.dumps(game_info)
        }

        try:
            response = requests.post(
                f"{BASE_URL}/api/analyze/upload",
                files=files,
                data=data
            )
            response.raise_for_status()
            analyze_result = response.json()

            print("✓ Upload successful!")
            print(f"  Session ID: {analyze_result['session_id']}")
            print(f"  Sheets: {analyze_result['analysis']['file_info']['sheets']}")
            print(f"  Total rows: {analyze_result['analysis']['file_info']['total_rows']}")
            print(f"  Source langs: {analyze_result['analysis']['language_detection']['source_langs']}")
            print(f"  Target langs: {analyze_result['analysis']['language_detection']['target_langs']}")
            print(f"  Estimated tasks: {analyze_result['analysis']['statistics']['estimated_tasks']}")

            session_id = analyze_result['session_id']

        except requests.exceptions.RequestException as e:
            print(f"❌ Upload failed: {e}")
            if hasattr(e.response, 'text'):
                print(f"   Response: {e.response.text}")
            return

    # Step 2: Split tasks
    print("\n2. Splitting tasks...")

    split_request = {
        "session_id": session_id,
        "source_lang": None,  # Auto-detect
        "target_langs": ["TH", "PT", "VN"]
    }

    try:
        response = requests.post(
            f"{BASE_URL}/api/tasks/split",
            json=split_request
        )
        response.raise_for_status()
        split_result = response.json()

        print("✓ Task splitting successful!")
        print(f"  Total tasks: {split_result['task_count']}")
        print(f"  Total batches: {split_result['batch_count']}")
        print(f"  Batch distribution: {split_result['batch_distribution']}")
        print(f"  Download URL: {split_result['download_url']}")

        # Show preview
        if split_result.get('preview'):
            print("\n  Task preview (first 3):")
            for i, task in enumerate(split_result['preview'][:3], 1):
                print(f"    {i}. [{task['task_id']}]")
                print(f"       Source: {task['source_text']}")
                print(f"       Target: {task['target_lang']}")
                print(f"       Batch: {task['batch_id']}")

    except requests.exceptions.RequestException as e:
        print(f"❌ Task splitting failed: {e}")
        if hasattr(e.response, 'text'):
            print(f"   Response: {e.response.text}")
        return

    # Step 3: Get task status
    print("\n3. Checking task status...")

    try:
        response = requests.get(f"{BASE_URL}/api/tasks/status/{session_id}")
        response.raise_for_status()
        status_result = response.json()

        print("✓ Status check successful!")
        print(f"  Statistics: {status_result['statistics']}")

    except requests.exceptions.RequestException as e:
        print(f"❌ Status check failed: {e}")

    # Step 4: Get DataFrame content (limited)
    print("\n4. Getting task DataFrame...")

    try:
        response = requests.get(
            f"{BASE_URL}/api/tasks/dataframe/{session_id}",
            params={"limit": 5}
        )
        response.raise_for_status()
        df_result = response.json()

        print("✓ DataFrame retrieval successful!")
        print(f"  Total tasks: {df_result['total_count']}")
        print(f"  Returned: {df_result['returned_count']}")

        if df_result['tasks']:
            print("\n  First task details:")
            task = df_result['tasks'][0]
            for key in ['task_id', 'source_text', 'target_lang', 'batch_id', 'group_id', 'char_count']:
                if key in task:
                    print(f"    {key}: {task[key]}")

    except requests.exceptions.RequestException as e:
        print(f"❌ DataFrame retrieval failed: {e}")

    # Step 5: Export tasks
    print("\n5. Exporting tasks to Excel...")

    try:
        response = requests.get(f"{BASE_URL}/api/tasks/export/{session_id}")
        response.raise_for_status()

        # Save the exported file
        output_file = f"tasks_export_{session_id[:8]}.xlsx"
        with open(output_file, 'wb') as f:
            f.write(response.content)

        print(f"✓ Tasks exported successfully!")
        print(f"  Saved to: {output_file}")
        print(f"  File size: {len(response.content):,} bytes")

    except requests.exceptions.RequestException as e:
        print(f"❌ Export failed: {e}")

    print(f"\n{'='*60}")
    print("Test completed!")
    print(f"{'='*60}")


def test_with_curl():
    """Generate curl commands for manual testing."""

    print(f"\n{'='*60}")
    print("CURL Commands for Manual Testing")
    print(f"{'='*60}")

    print("\n1. Upload and analyze:")
    print("""curl -X 'POST' \\
  'http://localhost:8000/api/analyze/upload' \\
  -H 'accept: application/json' \\
  -H 'Content-Type: multipart/form-data' \\
  -F 'file=@/mnt/d/work/trans_excel/test2.xlsx;type=application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' \\
  -F 'game_info={"game_type":"MMORPG","world_view":"Fantasy martial arts world","target_regions":["TH","PT","VN"],"game_style":"Realistic"}'
""")

    print("\n2. Split tasks (replace SESSION_ID):")
    print("""curl -X 'POST' \\
  'http://localhost:8000/api/tasks/split' \\
  -H 'accept: application/json' \\
  -H 'Content-Type: application/json' \\
  -d '{
    "session_id": "SESSION_ID",
    "source_lang": null,
    "target_langs": ["TH", "PT", "VN"]
  }'
""")

    print("\n3. Check status (replace SESSION_ID):")
    print("""curl -X 'GET' \\
  'http://localhost:8000/api/tasks/status/SESSION_ID' \\
  -H 'accept: application/json'
""")

    print("\n4. Get DataFrame (replace SESSION_ID):")
    print("""curl -X 'GET' \\
  'http://localhost:8000/api/tasks/dataframe/SESSION_ID?limit=10' \\
  -H 'accept: application/json'
""")

    print("\n5. Export tasks (replace SESSION_ID):")
    print("""curl -X 'GET' \\
  'http://localhost:8000/api/tasks/export/SESSION_ID' \\
  -H 'accept: application/json' \\
  -o tasks_export.xlsx
""")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "curl":
        test_with_curl()
    else:
        test_full_api_flow()