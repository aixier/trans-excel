"""Test full system with real Excel file."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.game_info import GameInfo
from services.excel_loader import ExcelLoader
from services.excel_analyzer import ExcelAnalyzer
from services.task_splitter import TaskSplitter
from services.batch_allocator import BatchAllocator


def test_full_system(file_path):
    """Test the complete system with real Excel file."""
    print(f"\n{'#'*60}")
    print("# Testing Complete System")
    print(f"{'#'*60}")

    # Step 1: Load Excel
    print("\n1. Loading Excel file...")
    loader = ExcelLoader()
    excel_df = loader.load_excel(file_path)
    print(f"✓ Loaded: {excel_df.filename}")
    print(f"  Sheets: {excel_df.get_sheet_names()}")

    # Step 2: Create game info
    print("\n2. Setting game context...")
    game_info = GameInfo(
        game_type="MMORPG",
        world_view="Fantasy martial arts world",
        target_regions=["TH", "PT", "VN"],
        game_style="Realistic",
        additional_context="Mobile MMORPG with PvP focus"
    )
    print(f"✓ Game type: {game_info.game_type}")

    # Step 3: Analyze Excel
    print("\n3. Analyzing Excel content...")
    analyzer = ExcelAnalyzer()
    analysis = analyzer.analyze(excel_df, game_info)

    print(f"✓ Analysis complete:")
    print(f"  - Source languages: {analysis['language_detection']['source_langs']}")
    print(f"  - Target languages: {analysis['language_detection']['target_langs']}")
    print(f"  - Estimated tasks: {analysis['statistics']['estimated_tasks']}")

    # Count colored cells per sheet
    for sheet_name in excel_df.get_sheet_names():
        colors = excel_df.color_map.get(sheet_name, {})
        if colors:
            # Count yellow cells
            yellow_count = sum(1 for color in colors.values() if 'FFFF' in str(color))
            print(f"  - {sheet_name}: {yellow_count} yellow cells")

    # Step 4: Split tasks
    print("\n4. Splitting into translation tasks...")
    splitter = TaskSplitter(excel_df, game_info)

    # Use detected or specified languages
    task_manager = splitter.split_tasks(
        source_lang="EN",  # English as source
        target_langs=["TH", "PT", "VN"]  # Three target languages
    )

    stats = task_manager.get_statistics()
    print(f"✓ Tasks created: {stats['total']}")
    print(f"  - By language: PT={stats['by_language'].get('PT', 0)}, "
          f"TH={stats['by_language'].get('TH', 0)}, "
          f"VN={stats['by_language'].get('VN', 0)}")

    # Step 5: Analyze batch allocation
    print("\n5. Analyzing batch allocation...")
    if task_manager.df is not None and len(task_manager.df) > 0:
        allocator = BatchAllocator()
        tasks_list = task_manager.df.to_dict('records')
        batch_stats = allocator.calculate_batch_statistics(tasks_list)

        print(f"✓ Batch allocation:")
        print(f"  - Total batches: {batch_stats['total_batches']}")
        print(f"  - Distribution: {batch_stats['batch_distribution']}")
        print(f"  - Avg chars/batch: {batch_stats['avg_chars_per_batch']:.0f}")

        # Show sample tasks
        print(f"\n6. Sample tasks (first 3):")
        for idx, task in task_manager.df.head(3).iterrows():
            print(f"\n  Task #{idx+1}:")
            print(f"    ID: {task['task_id']}")
            print(f"    Source: {task['source_text'][:100]}...")
            print(f"    Target: {task['target_lang']}")
            print(f"    Batch: {task['batch_id']}")
            print(f"    Sheet: {task['sheet_name']}")
            print(f"    Cell: {task['cell_ref']}")

        # Export tasks to Excel
        export_path = "tasks_output.xlsx"
        print(f"\n7. Exporting tasks to {export_path}...")
        task_manager.export_to_excel(export_path)
        print(f"✓ Exported {stats['total']} tasks")

    print(f"\n{'='*60}")
    print("System test completed successfully!")
    print('='*60)


if __name__ == "__main__":
    test_file = "/mnt/d/work/trans_excel/test_text_targ3_5tab_normall_有注释.xlsx"

    if not os.path.exists(test_file):
        print(f"File not found: {test_file}")
        sys.exit(1)

    try:
        test_full_system(test_file)
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()