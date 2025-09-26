"""System integration tests."""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from pathlib import Path

# Test imports
print("Testing imports...")

try:
    from models.game_info import GameInfo
    from models.excel_dataframe import ExcelDataFrame
    from models.task_dataframe import TaskDataFrameManager
    from services.excel_loader import ExcelLoader
    from services.language_detector import LanguageDetector
    from services.excel_analyzer import ExcelAnalyzer
    from services.context_extractor import ContextExtractor
    from services.batch_allocator import BatchAllocator
    from services.task_splitter import TaskSplitter
    from utils.config_manager import config_manager
    from utils.session_manager import session_manager
    print("✓ All imports successful")
except Exception as e:
    print(f"✗ Import error: {e}")
    sys.exit(1)


def test_excel_loader():
    """Test Excel loading."""
    print("\nTesting Excel Loader...")

    test_file = "tests/test_data/small.xlsx"
    if not Path(test_file).exists():
        print(f"✗ Test file not found: {test_file}")
        return False

    try:
        loader = ExcelLoader()
        excel_df = loader.load_excel(test_file)

        assert excel_df is not None
        assert len(excel_df.sheets) > 0
        assert excel_df.filename == "small.xlsx"

        print(f"✓ Loaded Excel with {len(excel_df.sheets)} sheet(s)")
        return True
    except Exception as e:
        print(f"✗ Excel loader error: {e}")
        return False


def test_language_detector():
    """Test language detection."""
    print("\nTesting Language Detector...")

    try:
        detector = LanguageDetector()

        # Test Chinese detection
        ch_text = "开始游戏"
        ch_lang = detector.detect_language(ch_text)
        assert ch_lang == 'CH', f"Expected CH, got {ch_lang}"

        # Test English detection
        en_text = "Start Game"
        en_lang = detector.detect_language(en_text)
        assert en_lang == 'EN', f"Expected EN, got {en_lang}"

        print("✓ Language detection working")
        return True
    except Exception as e:
        print(f"✗ Language detector error: {e}")
        return False


def test_game_info():
    """Test GameInfo model."""
    print("\nTesting GameInfo...")

    try:
        game_info = GameInfo(
            game_type="RPG",
            world_view="Fantasy world with magic",
            target_regions=["BR", "TH", "VN"],
            game_style="Anime",
            additional_context="Mobile game"
        )

        context_str = game_info.to_context_string()
        assert "RPG" in context_str
        assert "BR, TH, VN" in context_str

        print("✓ GameInfo model working")
        return True
    except Exception as e:
        print(f"✗ GameInfo error: {e}")
        return False


def test_excel_analyzer():
    """Test Excel analyzer."""
    print("\nTesting Excel Analyzer...")

    test_file = "tests/test_data/small.xlsx"
    if not Path(test_file).exists():
        print(f"✗ Test file not found: {test_file}")
        return False

    try:
        loader = ExcelLoader()
        excel_df = loader.load_excel(test_file)

        analyzer = ExcelAnalyzer()
        analysis = analyzer.analyze(excel_df)

        assert 'file_info' in analysis
        assert 'language_detection' in analysis
        assert 'statistics' in analysis

        print(f"✓ Analysis complete: {analysis['statistics'].get('estimated_tasks', 0)} tasks estimated")
        return True
    except Exception as e:
        print(f"✗ Analyzer error: {e}")
        return False


def test_task_splitter():
    """Test task splitting."""
    print("\nTesting Task Splitter...")

    test_file = "tests/test_data/small.xlsx"
    if not Path(test_file).exists():
        print(f"✗ Test file not found: {test_file}")
        return False

    try:
        # Load Excel
        loader = ExcelLoader()
        excel_df = loader.load_excel(test_file)

        # Create game info
        game_info = GameInfo(
            game_type="RPG",
            world_view="Fantasy",
            target_regions=["PT", "TH"],
            game_style="Anime"
        )

        # Split tasks
        splitter = TaskSplitter(excel_df, game_info)
        task_manager = splitter.split_tasks(
            source_lang="CH",
            target_langs=["PT", "TH"]
        )

        stats = task_manager.get_statistics()
        print(f"✓ Created {stats['total']} tasks")
        return True
    except Exception as e:
        print(f"✗ Task splitter error: {e}")
        return False


def test_batch_allocator():
    """Test batch allocation."""
    print("\nTesting Batch Allocator...")

    try:
        allocator = BatchAllocator()

        # Create test tasks
        tasks = [
            {'task_id': f'TASK_{i:04d}',
             'source_text': 'x' * (100 * (i % 10 + 1)),  # Variable length
             'source_context': 'Test context',
             'target_lang': 'PT' if i % 2 == 0 else 'TH'}
            for i in range(20)
        ]

        # Allocate batches
        allocated = allocator.allocate_batches(tasks)

        # Check batch assignment
        batch_ids = set(t['batch_id'] for t in allocated)
        assert len(batch_ids) > 0

        # Get statistics
        stats = allocator.calculate_batch_statistics(allocated)
        print(f"✓ Allocated {len(batch_ids)} batches for {len(tasks)} tasks")
        print(f"  Average chars per batch: {stats['avg_chars_per_batch']:.0f}")
        return True
    except Exception as e:
        print(f"✗ Batch allocator error: {e}")
        return False


def test_session_manager():
    """Test session management."""
    print("\nTesting Session Manager...")

    try:
        # Create session
        session_id = session_manager.create_session()
        assert session_id is not None

        # Store data
        game_info = GameInfo(game_type="RPG")
        session_manager.set_game_info(session_id, game_info)

        # Retrieve data
        retrieved = session_manager.get_game_info(session_id)
        assert retrieved is not None
        assert retrieved.game_type == "RPG"

        print(f"✓ Session manager working (ID: {session_id[:8]}...)")
        return True
    except Exception as e:
        print(f"✗ Session manager error: {e}")
        return False


def test_config_manager():
    """Test configuration management."""
    print("\nTesting Config Manager...")

    try:
        max_chars = config_manager.max_chars_per_batch
        max_workers = config_manager.max_concurrent_workers

        assert max_chars == 50000
        assert max_workers == 10

        print(f"✓ Config loaded: {max_chars} chars/batch, {max_workers} workers")
        return True
    except Exception as e:
        print(f"✗ Config manager error: {e}")
        return False


def run_all_tests():
    """Run all tests."""
    print("=" * 50)
    print("Running Backend V2 System Tests")
    print("=" * 50)

    tests = [
        test_config_manager,
        test_excel_loader,
        test_language_detector,
        test_game_info,
        test_excel_analyzer,
        test_task_splitter,
        test_batch_allocator,
        test_session_manager
    ]

    passed = 0
    failed = 0

    for test in tests:
        if test():
            passed += 1
        else:
            failed += 1

    print("\n" + "=" * 50)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("=" * 50)

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)