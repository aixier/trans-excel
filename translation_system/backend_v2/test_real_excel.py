"""Test with real Excel file."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import json
import pandas as pd
from models.game_info import GameInfo
from services.excel_loader import ExcelLoader
from services.excel_analyzer import ExcelAnalyzer
from services.task_splitter import TaskSplitter
from services.batch_allocator import BatchAllocator


def analyze_excel_file(file_path):
    """Analyze the Excel file structure."""
    print(f"\n{'='*60}")
    print(f"Analyzing Excel File: {os.path.basename(file_path)}")
    print('='*60)

    # First use pandas to get basic info
    try:
        excel_data = pd.read_excel(file_path, sheet_name=None)
        print(f"\nNumber of sheets: {len(excel_data)}")

        for sheet_name, df in excel_data.items():
            print(f"\n[Sheet: {sheet_name}]")
            print(f"  - Shape: {df.shape[0]} rows x {df.shape[1]} columns")
            print(f"  - Columns: {list(df.columns)}")

            # Sample first few rows
            print(f"  - First 3 rows:")
            for idx, row in df.head(3).iterrows():
                print(f"    Row {idx}: {row.to_dict()}")

    except Exception as e:
        print(f"Error reading with pandas: {e}")
        return


def test_excel_loader(file_path):
    """Test Excel loading with color and comment extraction."""
    print(f"\n{'='*60}")
    print("Testing Excel Loader")
    print('='*60)

    try:
        loader = ExcelLoader()
        excel_df = loader.load_excel(file_path)

        stats = excel_df.get_statistics()
        print(f"\nFile Statistics:")
        print(f"  - Excel ID: {excel_df.excel_id}")
        print(f"  - Total sheets: {stats['sheet_count']}")
        print(f"  - Total rows: {stats['total_rows']}")
        print(f"  - Total cells: {stats['total_cells']}")
        print(f"  - Non-empty cells: {stats['total_non_empty']}")

        # Check colors
        for sheet_name in excel_df.get_sheet_names():
            colors = excel_df.color_map.get(sheet_name, {})
            if colors:
                print(f"\n  Colors in {sheet_name}: {len(colors)} cells")
                # Show first 5 colors
                for (row, col), color in list(colors.items())[:5]:
                    print(f"    Cell ({row},{col}): {color}")

            # Check comments
            comments = excel_df.comment_map.get(sheet_name, {})
            if comments:
                print(f"\n  Comments in {sheet_name}: {len(comments)} cells")
                for (row, col), comment in list(comments.items())[:5]:
                    print(f"    Cell ({row},{col}): {comment}")

        return excel_df

    except Exception as e:
        print(f"Error in Excel loader: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_analyzer(excel_df):
    """Test Excel analyzer."""
    print(f"\n{'='*60}")
    print("Testing Excel Analyzer")
    print('='*60)

    try:
        # Create game info
        game_info = GameInfo(
            game_type="RPG",
            world_view="Fantasy medieval world",
            target_regions=["PT", "TH", "VN"],
            game_style="Realistic",
            additional_context="Mobile RPG game with turn-based combat"
        )

        analyzer = ExcelAnalyzer()
        analysis = analyzer.analyze(excel_df, game_info)

        print(f"\nAnalysis Results:")
        print(f"  - Detected source languages: {analysis['language_detection']['source_langs']}")
        print(f"  - Detected target languages: {analysis['language_detection']['target_langs']}")
        print(f"  - Estimated translation tasks: {analysis['statistics']['estimated_tasks']}")

        if analysis['statistics']['char_distribution']['count'] > 0:
            print(f"  - Character distribution:")
            print(f"    * Min: {analysis['statistics']['char_distribution']['min']}")
            print(f"    * Max: {analysis['statistics']['char_distribution']['max']}")
            print(f"    * Avg: {analysis['statistics']['char_distribution']['avg']:.1f}")
            print(f"    * Total: {analysis['statistics']['char_distribution']['total']}")

        # Show sheet-level language detection
        print(f"\n  Sheet-level language analysis:")
        for sheet_detail in analysis['language_detection']['sheet_details']:
            print(f"    [{sheet_detail['sheet_name']}]")
            print(f"      Source langs: {sheet_detail['source_languages']}")
            print(f"      Target langs: {sheet_detail['target_languages']}")
            print(f"      Has pairs: {sheet_detail['has_translation_pairs']}")

        return analysis

    except Exception as e:
        print(f"Error in analyzer: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_task_splitter(excel_df):
    """Test task splitting."""
    print(f"\n{'='*60}")
    print("Testing Task Splitter")
    print('='*60)

    try:
        # Create game info
        game_info = GameInfo(
            game_type="RPG",
            world_view="Fantasy medieval world",
            target_regions=["PT", "TH", "VN"],
            game_style="Realistic"
        )

        splitter = TaskSplitter(excel_df, game_info)

        # Split tasks (let it auto-detect languages)
        task_manager = splitter.split_tasks(
            source_lang=None,  # Auto-detect
            target_langs=["PT", "TH", "VN"]  # All three targets
        )

        stats = task_manager.get_statistics()
        print(f"\nTask Statistics:")
        print(f"  - Total tasks created: {stats['total']}")
        print(f"  - By status: {stats['by_status']}")
        print(f"  - By language: {stats['by_language']}")
        print(f"  - By group: {stats['by_group']}")

        # Show sample tasks
        if task_manager.df is not None and len(task_manager.df) > 0:
            print(f"\n  Sample tasks (first 5):")
            for idx, task in task_manager.df.head(5).iterrows():
                print(f"    [{task['task_id']}]")
                print(f"      Source: {task['source_text'][:50]}...")
                print(f"      Target lang: {task['target_lang']}")
                print(f"      Batch: {task['batch_id']}")
                print(f"      Group: {task['group_id']}")
                print(f"      Context: {task['source_context'][:100]}...")

        # Test batch allocation
        if task_manager.df is not None:
            allocator = BatchAllocator()
            tasks_list = task_manager.df.to_dict('records')
            batch_stats = allocator.calculate_batch_statistics(tasks_list)

            print(f"\n  Batch Allocation:")
            print(f"    Total batches: {batch_stats['total_batches']}")
            print(f"    Distribution: {batch_stats['batch_distribution']}")
            print(f"    Avg chars/batch: {batch_stats['avg_chars_per_batch']:.0f}")
            print(f"    Max chars: {batch_stats['max_chars_in_batch']}")
            print(f"    Min chars: {batch_stats['min_chars_in_batch']}")

        return task_manager

    except Exception as e:
        print(f"Error in task splitter: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """Main test function."""
    # Test file path
    test_file = "/mnt/d/work/trans_excel/test_text_targ3_5tab_normall_有注释.xlsx"

    if not os.path.exists(test_file):
        print(f"File not found: {test_file}")
        return

    # Run tests
    print(f"\n{'#'*60}")
    print(f"# Testing Backend V2 with Real Excel File")
    print(f"# File: {os.path.basename(test_file)}")
    print(f"{'#'*60}")

    # Step 1: Analyze file structure
    analyze_excel_file(test_file)

    # Step 2: Test Excel loader
    excel_df = test_excel_loader(test_file)
    if not excel_df:
        print("Failed to load Excel file")
        return

    # Step 3: Test analyzer
    analysis = test_analyzer(excel_df)

    # Step 4: Test task splitter
    task_manager = test_task_splitter(excel_df)

    print(f"\n{'='*60}")
    print("All tests completed!")
    print('='*60)


if __name__ == "__main__":
    main()