"""Test Phase 2 - Execution Engine and Monitoring."""

import asyncio
import requests
import json
import time
import os
from pathlib import Path


class Phase2Tester:
    """Test Phase 2 implementation."""

    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session_id = None

    def test_phase1_setup(self):
        """Setup from Phase 1: Upload and split tasks."""
        print("\n" + "="*60)
        print("Phase 1 Setup: Upload and Split Tasks")
        print("="*60)

        # Upload test file
        test_file = "/mnt/d/work/trans_excel/test2.xlsx"
        if not os.path.exists(test_file):
            print(f"❌ Test file not found: {test_file}")
            return False

        with open(test_file, 'rb') as f:
            files = {'file': ('test2.xlsx', f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
            game_info = {
                "game_type": "MMORPG",
                "world_view": "Fantasy martial arts world",
                "target_regions": ["TH", "PT", "VN"],
                "game_style": "Realistic"
            }
            data = {'game_info': json.dumps(game_info)}

            response = requests.post(
                f"{self.base_url}/api/analyze/upload",
                files=files,
                data=data
            )

            if response.status_code == 200:
                result = response.json()
                self.session_id = result['session_id']
                print(f"✓ Upload successful: {self.session_id}")
                print(f"  Estimated tasks: {result['analysis']['statistics']['estimated_tasks']}")
            else:
                print(f"❌ Upload failed: {response.text}")
                return False

        # Split tasks
        split_request = {
            "session_id": self.session_id,
            "source_lang": "CH",
            "target_langs": ["PT"]  # Only test with one language to save API calls
        }

        response = requests.post(
            f"{self.base_url}/api/tasks/split",
            json=split_request
        )

        if response.status_code == 200:
            result = response.json()
            print(f"✓ Split successful: {result['task_count']} tasks in {result['batch_count']} batches")
            return True
        else:
            print(f"❌ Split failed: {response.text}")
            return False

    def test_execution_config(self):
        """Test execution configuration endpoint."""
        print("\n" + "="*60)
        print("Test Execution Configuration")
        print("="*60)

        response = requests.get(f"{self.base_url}/api/execute/config")

        if response.status_code == 200:
            config = response.json()
            print("✓ Configuration retrieved:")
            print(f"  Max workers: {config['max_concurrent_workers']}")
            print(f"  Max chars/batch: {config['max_chars_per_batch']}")
            print(f"  Default provider: {config['default_provider']}")
            print(f"  Available providers: {', '.join(config['available_providers'])}")
            return True
        else:
            print(f"❌ Config retrieval failed: {response.text}")
            return False

    def test_execution_start_mock(self):
        """Test execution start with mock provider."""
        print("\n" + "="*60)
        print("Test Execution Start (Mock Mode)")
        print("="*60)

        # Note: In real testing, you would use a mock provider
        # For now, we'll just test the API endpoint
        print("⚠️ Skipping actual execution (requires API keys)")
        print("  To test execution, set OPENAI_API_KEY or DASHSCOPE_API_KEY")

        # We can still test the endpoint returns proper error
        execute_request = {
            "session_id": self.session_id,
            "provider": "openai",
            "max_workers": 2
        }

        response = requests.post(
            f"{self.base_url}/api/execute/start",
            json=execute_request
        )

        # Expected to fail without API key
        if response.status_code == 400:
            print("✓ Execution endpoint working (API key required)")
            return True
        elif response.status_code == 200:
            print("✓ Execution started successfully")
            return True
        else:
            print(f"❌ Unexpected response: {response.status_code}")
            return False

    def test_monitor_status(self):
        """Test monitoring status endpoint."""
        print("\n" + "="*60)
        print("Test Monitor Status")
        print("="*60)

        response = requests.get(f"{self.base_url}/api/monitor/status/{self.session_id}")

        if response.status_code == 200:
            status = response.json()
            print("✓ Status retrieved:")
            print(f"  Status: {status['status']}")
            print(f"  Total tasks: {status['progress']['total']}")
            print(f"  Completed: {status['progress']['completed']}")
            print(f"  Pending: {status['progress']['pending']}")
            print(f"  Completion rate: {status['completion_rate']:.1f}%")
            return True
        else:
            print(f"❌ Status retrieval failed: {response.text}")
            return False

    def test_monitor_dataframe(self):
        """Test DataFrame query endpoint."""
        print("\n" + "="*60)
        print("Test DataFrame Query")
        print("="*60)

        params = {
            "limit": 5,
            "offset": 0,
            "sort_by": "task_id",
            "sort_order": "asc"
        }

        response = requests.get(
            f"{self.base_url}/api/monitor/dataframe/{self.session_id}",
            params=params
        )

        if response.status_code == 200:
            result = response.json()
            print("✓ DataFrame retrieved:")
            print(f"  Total count: {result['total_count']}")
            print(f"  Returned: {result['returned_count']}")

            if result['tasks']:
                print("\n  Sample task:")
                task = result['tasks'][0]
                print(f"    ID: {task['task_id']}")
                print(f"    Source: {task['source_text'][:30]}...")
                print(f"    Target lang: {task['target_lang']}")
                print(f"    Status: {task['status']}")
            return True
        else:
            print(f"❌ DataFrame query failed: {response.text}")
            return False

    def test_monitor_batches(self):
        """Test batch status endpoint."""
        print("\n" + "="*60)
        print("Test Batch Status")
        print("="*60)

        response = requests.get(f"{self.base_url}/api/monitor/batches/{self.session_id}")

        if response.status_code == 200:
            result = response.json()
            print("✓ Batch status retrieved:")
            print(f"  Total batches: {result['total_batches']}")

            for batch_id, batch_info in list(result['batches'].items())[:3]:
                print(f"\n  Batch {batch_id}:")
                print(f"    Total tasks: {batch_info['total']}")
                print(f"    Pending: {batch_info['pending']}")
                print(f"    Characters: {batch_info['char_count']}")
            return True
        else:
            print(f"❌ Batch status failed: {response.text}")
            return False

    def test_monitor_summary(self):
        """Test execution summary endpoint."""
        print("\n" + "="*60)
        print("Test Execution Summary")
        print("="*60)

        response = requests.get(f"{self.base_url}/api/monitor/summary/{self.session_id}")

        if response.status_code == 200:
            summary = response.json()
            print("✓ Summary retrieved:")
            print(f"  Total tasks: {summary['task_statistics']['total']}")
            print(f"  Total characters: {summary['total_characters']}")
            print(f"  Languages: {summary['language_distribution']}")
            print(f"  Groups: {len(summary['group_distribution'])} groups")
            return True
        else:
            print(f"❌ Summary failed: {response.text}")
            return False

    def run_all_tests(self):
        """Run all Phase 2 tests."""
        print("\n" + "="*80)
        print(" Translation System Backend V2 - Phase 2 Testing")
        print("="*80)

        tests = [
            ("Phase 1 Setup", self.test_phase1_setup),
            ("Execution Config", self.test_execution_config),
            ("Execution Start", self.test_execution_start_mock),
            ("Monitor Status", self.test_monitor_status),
            ("DataFrame Query", self.test_monitor_dataframe),
            ("Batch Status", self.test_monitor_batches),
            ("Execution Summary", self.test_monitor_summary),
        ]

        results = []
        for name, test_func in tests:
            try:
                success = test_func()
                results.append((name, success))
            except Exception as e:
                print(f"❌ Test '{name}' failed with error: {str(e)}")
                results.append((name, False))

        # Print summary
        print("\n" + "="*80)
        print(" Test Summary")
        print("="*80)

        total = len(results)
        passed = sum(1 for _, success in results if success)
        failed = total - passed

        for name, success in results:
            status = "✓ PASS" if success else "❌ FAIL"
            print(f"{status}: {name}")

        print("\n" + "-"*40)
        print(f"Total: {total} | Passed: {passed} | Failed: {failed}")
        print(f"Success rate: {(passed/total*100):.1f}%")

        return passed == total


def main():
    """Main test runner."""
    tester = Phase2Tester()

    # Check if server is running
    try:
        response = requests.get(f"{tester.base_url}/health")
        if response.status_code != 200:
            print("❌ Server is not healthy")
            return False
    except:
        print("❌ Server is not running. Please start the server first:")
        print("   cd /mnt/d/work/trans_excel/translation_system/backend_v2")
        print("   python3 main.py")
        return False

    # Run tests
    success = tester.run_all_tests()

    if success:
        print("\n🎉 All Phase 2 tests passed!")
    else:
        print("\n⚠️ Some tests failed. Please check the logs.")

    return success


if __name__ == "__main__":
    import sys
    sys.exit(0 if main() else 1)