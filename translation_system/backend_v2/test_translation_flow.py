#!/usr/bin/env python3
"""
Complete translation workflow test script.
From file upload to result download.
"""

import requests
import json
import time
import sys
import os
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8013"
TEST_FILE = "/mnt/d/work/trans_excel/test2.xlsx"
PROVIDER = "qwen-plus"
MAX_WORKERS = 5
TARGET_LANGS = ["PT"]  # Use only PT to reduce API calls for testing

# Disable timeout for long-running operations
TIMEOUT = None


def print_step(step_num, message):
    """Print formatted step message."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n{'='*60}")
    print(f"[{timestamp}] Step {step_num}: {message}")
    print('='*60)


def print_info(message):
    """Print info message."""
    print(f"  ℹ️  {message}")


def print_success(message):
    """Print success message."""
    print(f"  ✅ {message}")


def print_error(message):
    """Print error message."""
    print(f"  ❌ {message}")


def upload_file(file_path):
    """Step 1: Upload Excel file for analysis."""
    print_step(1, "Uploading Excel file for analysis")

    if not os.path.exists(file_path):
        print_error(f"File not found: {file_path}")
        return None

    print_info(f"Uploading file: {file_path}")

    with open(file_path, 'rb') as f:
        files = {
            'file': (os.path.basename(file_path), f,
                    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        }
        game_info = {
            "game_type": "RPG",
            "world_view": "Fantasy world",
            "target_regions": TARGET_LANGS,
            "game_style": "Realistic"
        }
        data = {'game_info': json.dumps(game_info)}

        response = requests.post(
            f"{BASE_URL}/api/analyze/upload",
            files=files,
            data=data,
            timeout=TIMEOUT
        )

    if response.status_code == 200:
        result = response.json()
        session_id = result['session_id']
        print_success(f"Upload successful! Session ID: {session_id}")

        # Print analysis info
        analysis = result.get('analysis', {})
        lang_detection = analysis.get('language_detection', {})
        print_info(f"Source languages detected: {lang_detection.get('source_langs', [])}")
        print_info(f"Target languages available: {lang_detection.get('target_langs', [])}")

        stats = analysis.get('statistics', {})
        print_info(f"Estimated tasks: {stats.get('estimated_tasks', 0)}")

        return session_id
    else:
        print_error(f"Upload failed: {response.status_code}")
        print_error(f"Error: {response.text}")
        return None


def split_tasks(session_id):
    """Step 2: Split tasks for translation."""
    print_step(2, "Splitting tasks into batches")

    print_info(f"Session ID: {session_id}")
    print_info(f"Target languages: {TARGET_LANGS}")

    request_data = {
        "session_id": session_id,
        "source_lang": "CH",
        "target_langs": TARGET_LANGS
    }

    response = requests.post(
        f"{BASE_URL}/api/tasks/split",
        json=request_data,
        timeout=TIMEOUT
    )

    if response.status_code == 200:
        result = response.json()
        print_success(f"Task splitting successful!")
        print_info(f"Total tasks created: {result.get('task_count', 0)}")
        print_info(f"Total batches: {result.get('batch_count', 0)}")
        print_info(f"Total characters: {result.get('total_chars', 0)}")
        return True
    else:
        print_error(f"Task splitting failed: {response.status_code}")
        print_error(f"Error: {response.text}")
        return False


def start_translation(session_id):
    """Step 3: Start translation execution."""
    print_step(3, "Starting translation execution")

    print_info(f"Provider: {PROVIDER}")
    print_info(f"Max workers: {MAX_WORKERS}")

    request_data = {
        "session_id": session_id,
        "provider": PROVIDER,
        "max_workers": MAX_WORKERS
    }

    response = requests.post(
        f"{BASE_URL}/api/execute/start",
        json=request_data,
        timeout=TIMEOUT
    )

    if response.status_code == 200:
        result = response.json()
        print_success("Translation execution started!")
        print_info(f"Status: {result.get('status', 'unknown')}")
        return True
    else:
        print_error(f"Failed to start translation: {response.status_code}")
        print_error(f"Error: {response.text}")
        return False


def monitor_progress(session_id):
    """Step 4: Monitor translation progress."""
    print_step(4, "Monitoring translation progress")

    print_info("Checking progress every 10 seconds...")
    print_info("This may take a while depending on the file size...")

    completed = False
    last_progress = -1
    error_count = 0
    max_errors = 5

    while not completed:
        try:
            response = requests.get(
                f"{BASE_URL}/api/monitor/status/{session_id}",
                timeout=30  # Use shorter timeout for monitoring
            )

            if response.status_code == 200:
                status = response.json()
                progress = status.get('progress', {})

                total = progress.get('total', 0)
                completed_tasks = progress.get('completed', 0)
                processing = progress.get('processing', 0)
                pending = progress.get('pending', 0)
                failed = progress.get('failed', 0)

                if total > 0:
                    completion_rate = (completed_tasks / total) * 100
                else:
                    completion_rate = 0

                # Only print if progress changed
                if completion_rate != last_progress:
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    print(f"  [{timestamp}] Progress: {completion_rate:.1f}% " +
                          f"(Completed: {completed_tasks}/{total}, " +
                          f"Processing: {processing}, Pending: {pending}, Failed: {failed})")
                    last_progress = completion_rate

                # Check if completed
                if pending == 0 and processing == 0:
                    if completed_tasks > 0:
                        print_success(f"Translation completed! Total tasks: {completed_tasks}")
                        if failed > 0:
                            print_info(f"Warning: {failed} tasks failed")
                    completed = True
                    break

                error_count = 0  # Reset error count on success
            else:
                error_count += 1
                print_error(f"Failed to get status (attempt {error_count}/{max_errors})")

                if error_count >= max_errors:
                    print_error("Max errors reached. Translation might have stopped.")
                    break

        except requests.exceptions.RequestException as e:
            error_count += 1
            print_error(f"Connection error (attempt {error_count}/{max_errors}): {str(e)}")

            if error_count >= max_errors:
                print_error("Max connection errors reached.")
                break

        # Wait before next check
        time.sleep(10)

    return completed


def download_results(session_id):
    """Step 5: Download translation results."""
    print_step(5, "Downloading translation results")

    output_file = f"translated_{session_id[:8]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

    print_info(f"Downloading to: {output_file}")

    response = requests.get(
        f"{BASE_URL}/api/tasks/export/{session_id}",
        stream=True,
        timeout=TIMEOUT
    )

    if response.status_code == 200:
        with open(output_file, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        file_size = os.path.getsize(output_file)
        print_success(f"Download completed! File: {output_file}")
        print_info(f"File size: {file_size:,} bytes")
        return output_file
    else:
        print_error(f"Download failed: {response.status_code}")
        print_error(f"Error: {response.text}")
        return None


def get_summary(session_id):
    """Get final summary of translation."""
    print_step(6, "Getting translation summary")

    response = requests.get(
        f"{BASE_URL}/api/monitor/summary/{session_id}",
        timeout=30
    )

    if response.status_code == 200:
        summary = response.json()

        print_success("Translation Summary:")

        # Task statistics
        task_stats = summary.get('task_statistics', {})
        print_info(f"Total tasks: {task_stats.get('total', 0)}")

        by_status = task_stats.get('by_status', {})
        for status, count in by_status.items():
            print_info(f"  {status}: {count}")

        # Language distribution
        lang_dist = summary.get('language_distribution', {})
        if lang_dist:
            print_info("Language distribution:")
            for lang, count in lang_dist.items():
                print_info(f"  {lang}: {count} tasks")

        # Execution metrics
        exec_metrics = summary.get('execution_metrics', {})
        if exec_metrics:
            print_info("Execution metrics:")
            total_duration = exec_metrics.get('total_duration_ms', 0) / 1000
            print_info(f"  Total duration: {total_duration:.2f} seconds")
            print_info(f"  Total tokens: {exec_metrics.get('total_tokens', 0):,}")
            print_info(f"  Estimated cost: ${exec_metrics.get('estimated_cost', 0):.4f}")


def main():
    """Main execution flow."""
    print("\n" + "="*60)
    print(" Translation System - Complete Workflow Test")
    print("="*60)
    print(f"File: {TEST_FILE}")
    print(f"Provider: {PROVIDER}")
    print(f"Target Languages: {TARGET_LANGS}")
    print(f"Base URL: {BASE_URL}")

    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            print_error("Server is not healthy")
            return 1
    except:
        print_error("Server is not running. Please start the server first:")
        print("  cd /mnt/d/work/trans_excel/translation_system/backend_v2")
        print("  python3 main.py")
        return 1

    # Step 1: Upload file
    session_id = upload_file(TEST_FILE)
    if not session_id:
        print_error("Failed to upload file. Exiting.")
        return 1

    # Step 2: Split tasks
    if not split_tasks(session_id):
        print_error("Failed to split tasks. Exiting.")
        return 1

    # Step 3: Start translation
    if not start_translation(session_id):
        print_error("Failed to start translation. Exiting.")
        return 1

    # Step 4: Monitor progress
    monitor_progress(session_id)

    # Step 5: Download results
    output_file = download_results(session_id)
    if not output_file:
        print_error("Failed to download results.")
        return 1

    # Step 6: Get summary
    get_summary(session_id)

    # Final message
    print("\n" + "="*60)
    print(" Translation Workflow Completed!")
    print("="*60)
    print(f"Session ID: {session_id}")
    print(f"Output file: {output_file}")
    print("\nYou can now open the Excel file to review the translations.")

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nProcess interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)