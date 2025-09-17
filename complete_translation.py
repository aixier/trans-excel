#!/usr/bin/env python3
"""
Complete translation of 123.xlsx with smaller batches to avoid timeout
"""

import requests
import json
import time
import os

BASE_URL = "http://localhost:8703"
EXCEL_FILE = "/mnt/d/work/trans_excel/123.xlsx"
OUTPUT_FILE = "/mnt/d/work/trans_excel/complete_translation_result.xlsx"

def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}")

def translate_with_smaller_batches():
    """Translate with smaller batches to avoid timeout"""

    log("Starting complete translation with optimized settings")

    # Step 1: Analyze file
    with open(EXCEL_FILE, 'rb') as f:
        files = {'file': (os.path.basename(EXCEL_FILE), f,
                         'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
        response = requests.post(f"{BASE_URL}/api/v1/analyze/sheets", files=files)

        if response.status_code != 200:
            log(f"Analysis failed: {response.text}")
            return None

        analysis = response.json()
        log(f"File has {len(analysis['sheets'])} sheets: {analysis['sheets']}")
        for sheet_name, info in analysis['sheet_info'].items():
            log(f"  - {sheet_name}: {info['rows']} rows × {info['columns']} columns")

    # Step 2: Upload and translate with smaller batches
    all_sheets = analysis['sheets']

    with open(EXCEL_FILE, 'rb') as f:
        files = {'file': (os.path.basename(EXCEL_FILE), f,
                         'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}

        # Use smaller batch size and lower concurrency to avoid timeout
        data = {
            'selected_sheets': json.dumps(all_sheets),
            'urgency': 'urgent',
            'user_preference': 'speed',
            'strategy': 'realtime_concurrent',
            'batch_size': '20',  # Smaller batch size
            'concurrent_limit': '10'  # Lower concurrency
        }

        log("Translation settings:")
        for key, value in data.items():
            log(f"  {key}: {value}")

        response = requests.post(f"{BASE_URL}/api/v1/translate/upload",
                                files=files, data=data)

        if response.status_code != 200:
            log(f"Upload failed: {response.text}")
            return None

        result = response.json()
        task_id = result['task_id']
        log(f"Task created: {task_id}")

    # Step 3: Monitor progress
    log("\nMonitoring progress...")
    completed = False
    last_progress = -1
    no_progress_count = 0
    max_wait_time = 1200  # 20 minutes maximum
    start_time = time.time()

    while not completed:
        if time.time() - start_time > max_wait_time:
            log(f"Maximum wait time ({max_wait_time}s) exceeded")
            break

        response = requests.get(f"{BASE_URL}/api/v1/task/{task_id}/status")

        if response.status_code != 200:
            log(f"Status check failed: {response.status_code}")
            time.sleep(5)
            continue

        status = response.json()

        task_status = status.get('status', 'unknown')
        progress = status.get('progress', 0)
        current_step = status.get('current_step', '')
        processed_rows = status.get('processed_rows', 0)
        total_rows = status.get('total_rows', 0)

        # Check for progress
        if progress == last_progress:
            no_progress_count += 1
            if no_progress_count > 60:  # No progress for 2 minutes
                log("No progress for 2 minutes, checking if partial results available")
                break
        else:
            no_progress_count = 0
            last_progress = progress

        # Display progress
        if processed_rows and total_rows:
            log(f"[{task_status}] {processed_rows}/{total_rows} rows - {current_step}")
        else:
            log(f"[{task_status}] {progress:.1f}% - {current_step}")

        if task_status == 'completed':
            log("✅ Translation completed!")
            completed = True

        elif task_status == 'failed':
            error_msg = status.get('error', 'Unknown error')
            log(f"❌ Translation failed: {error_msg}")
            return None

        time.sleep(2)

    # Step 4: Download result
    log("\nDownloading result...")
    download_url = f"{BASE_URL}/api/v1/download/{task_id}"
    response = requests.get(download_url)

    if response.status_code != 200:
        log(f"Download failed: {response.status_code}")
        return None

    with open(OUTPUT_FILE, 'wb') as f:
        f.write(response.content)

    log(f"Result saved to: {OUTPUT_FILE}")

    # Verify result
    import pandas as pd
    try:
        excel = pd.ExcelFile(OUTPUT_FILE)
        log(f"\nResult file contains {len(excel.sheet_names)} sheets:")

        total_translated = 0
        for sheet_name in excel.sheet_names:
            df = pd.read_excel(OUTPUT_FILE, sheet_name=sheet_name)
            non_empty = df.notna().sum().sum()
            total_translated += len(df)
            log(f"  - {sheet_name}: {len(df)} rows, {non_empty} non-empty cells")

        log(f"\nTotal rows in result: {total_translated}")

    except Exception as e:
        log(f"Error verifying result: {e}")

    return OUTPUT_FILE

if __name__ == "__main__":
    result = translate_with_smaller_batches()
    if result:
        log(f"\n✅ Complete translation saved to: {result}")
    else:
        log("\n❌ Translation failed or incomplete")