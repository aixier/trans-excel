"""
Integration tests for Transformer with other system components.

These tests verify that Transformer integrates correctly with:
- DataState (ExcelState)
- Processors (UppercaseProcessor, LLMProcessor mock)
- TaskDataFrame model

Target: Verify module boundaries and data flow
"""

import pytest
import pandas as pd
from datetime import datetime

from services.transformer import BaseTransformer
from services.processors import UppercaseProcessor
from services.data_state import ExcelState
from models.excel_dataframe import ExcelDataFrame


class TestTransformerDataStateIntegration:
    """Test integration with DataState module."""

    def test_with_excel_state(self):
        """Verify Transformer works with ExcelState."""
        # Create ExcelState
        excel_df = ExcelDataFrame()
        excel_df.filename = "integration_test.xlsx"
        excel_df.excel_id = "int_001"

        test_data = pd.DataFrame({
            'CH': ['你好世界', '测试数据'],
            'EN': ['', ''],
        })
        excel_df.sheets = {'TestSheet': test_data}
        excel_df.total_rows = len(test_data)
        excel_df.total_cols = len(test_data.columns)
        excel_df.color_map = {}
        excel_df.comment_map = {}

        state = ExcelState(excel_df)

        # Create tasks
        tasks = pd.DataFrame({
            'task_id': ['INT001', 'INT002'],
            'operation': ['uppercase', 'uppercase'],
            'sheet_name': ['TestSheet', 'TestSheet'],
            'row_idx': [0, 1],
            'col_idx': [1, 1],  # EN column
            'source_text': ['hello', 'world'],
            'status': ['pending', 'pending'],
            'result': ['', ''],
            'error_message': ['', ''],
            'updated_at': [datetime.now(), datetime.now()]
        })

        # Execute transformation
        processor = UppercaseProcessor()
        transformer = BaseTransformer(processor)
        new_state = transformer.execute(state, tasks)

        # Verify
        assert isinstance(new_state, ExcelState)
        assert new_state.get_cell_value('TestSheet', 0, 1) == 'HELLO'
        assert new_state.get_cell_value('TestSheet', 1, 1) == 'WORLD'

    def test_preserves_excel_metadata(self):
        """Verify that Excel metadata is preserved during transformation."""
        # Create ExcelState with metadata
        excel_df = ExcelDataFrame()
        excel_df.filename = "metadata_test.xlsx"
        excel_df.excel_id = "meta_001"

        test_data = pd.DataFrame({
            'A': ['test1'],
            'B': [''],
        })
        excel_df.sheets = {'Sheet1': test_data}
        excel_df.total_rows = len(test_data)
        excel_df.total_cols = len(test_data.columns)
        excel_df.color_map = {'Sheet1': {(0, 0): 'FFFF00'}}  # Yellow color
        excel_df.comment_map = {'Sheet1': {(0, 0): 'Important note'}}

        state = ExcelState(excel_df)

        # Create task
        tasks = pd.DataFrame({
            'task_id': ['META001'],
            'operation': ['uppercase'],
            'sheet_name': ['Sheet1'],
            'row_idx': [0],
            'col_idx': [1],
            'source_text': ['lowercase'],
            'status': ['pending'],
            'result': [''],
            'error_message': [''],
            'updated_at': [datetime.now()]
        })

        # Execute
        processor = UppercaseProcessor()
        transformer = BaseTransformer(processor)
        new_state = transformer.execute(state, tasks)

        # Verify metadata preserved
        metadata = new_state.get_metadata()
        assert metadata['filename'] == 'metadata_test.xlsx'
        assert metadata['excel_id'] == 'meta_001'
        assert (0, 0) in metadata['color_map']['Sheet1']
        assert metadata['color_map']['Sheet1'][(0, 0)] == 'FFFF00'


class TestTransformerProcessorIntegration:
    """Test integration with Processor module."""

    def test_processor_interface_compliance(self):
        """Verify Transformer correctly uses Processor interface."""
        # This test verifies that Transformer:
        # 1. Calls processor.process() correctly
        # 2. Handles processor return values
        # 3. Passes context correctly

        from services.processors import Processor
        from typing import Dict, Any, Optional

        class TestProcessor(Processor):
            """Test processor to verify interface usage."""

            def __init__(self):
                super().__init__()
                self.call_count = 0
                self.received_tasks = []
                self.received_contexts = []

            def get_operation_type(self) -> str:
                return 'test'

            def process(self, task: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> str:
                self.call_count += 1
                self.received_tasks.append(task)
                self.received_contexts.append(context)
                return f"processed_{task['task_id']}"

        # Create state
        excel_df = ExcelDataFrame()
        excel_df.filename = "test.xlsx"
        excel_df.excel_id = "test_001"
        test_data = pd.DataFrame({'A': [''], 'B': ['']})
        excel_df.sheets = {'Sheet1': test_data}
        excel_df.total_rows = len(test_data)
        excel_df.total_cols = len(test_data.columns)
        excel_df.color_map = {}
        excel_df.comment_map = {}
        state = ExcelState(excel_df)

        # Create tasks
        tasks = pd.DataFrame({
            'task_id': ['T1', 'T2'],
            'operation': ['test', 'test'],
            'sheet_name': ['Sheet1', 'Sheet1'],
            'row_idx': [0, 0],
            'col_idx': [0, 1],
            'source_text': ['src1', 'src2'],
            'status': ['pending', 'pending'],
            'result': ['', ''],
            'error_message': ['', ''],
            'updated_at': [datetime.now(), datetime.now()]
        })

        # Create context
        context = {'key': 'value'}

        # Execute
        processor = TestProcessor()
        transformer = BaseTransformer(processor)
        new_state = transformer.execute(state, tasks, context=context)

        # Verify interface usage
        assert processor.call_count == 2
        assert len(processor.received_tasks) == 2
        assert all(ctx == context for ctx in processor.received_contexts)
        assert all('task_id' in task for task in processor.received_tasks)


class TestTransformerTaskDataFrameIntegration:
    """Test integration with TaskDataFrame model."""

    def test_updates_task_dataframe_columns(self):
        """Verify Transformer correctly updates TaskDataFrame columns."""
        # Create state
        excel_df = ExcelDataFrame()
        excel_df.filename = "test.xlsx"
        excel_df.excel_id = "test_001"
        test_data = pd.DataFrame({'A': ['']})
        excel_df.sheets = {'Sheet1': test_data}
        excel_df.total_rows = len(test_data)
        excel_df.total_cols = len(test_data.columns)
        excel_df.color_map = {}
        excel_df.comment_map = {}
        state = ExcelState(excel_df)

        # Create tasks with all TaskDataFrame columns
        from models.task_dataframe import TASK_DF_COLUMNS
        task_data = {
            'task_id': ['TDF001'],
            'batch_id': ['B001'],
            'group_id': ['G001'],
            'source_lang': ['CH'],
            'source_text': ['test'],
            'target_lang': ['EN'],
            'operation': ['uppercase'],
            'sheet_name': ['Sheet1'],
            'row_idx': [0],
            'col_idx': [0],
            'status': ['pending'],
            'result': [''],
            'error_message': [''],
            'priority': [5],
            'char_count': [4],
            'created_at': [datetime.now()],
            'updated_at': [datetime.now()]
        }

        tasks = pd.DataFrame(task_data)

        # Execute
        processor = UppercaseProcessor()
        transformer = BaseTransformer(processor)
        new_state = transformer.execute(state, tasks)

        # Verify TaskDataFrame columns updated
        assert tasks.loc[0, 'status'] == 'completed'
        assert tasks.loc[0, 'result'] == 'TEST'
        assert isinstance(tasks.loc[0, 'updated_at'], pd.Timestamp)


class TestEndToEndScenarios:
    """Test complete end-to-end scenarios."""

    def test_multi_sheet_transformation(self):
        """Test transformation across multiple sheets."""
        # Create multi-sheet ExcelState
        excel_df = ExcelDataFrame()
        excel_df.filename = "multi_sheet.xlsx"
        excel_df.excel_id = "multi_001"

        sheet1_data = pd.DataFrame({'A': ['hello'], 'B': ['']})
        sheet2_data = pd.DataFrame({'A': ['world'], 'B': ['']})

        excel_df.sheets = {
            'Sheet1': sheet1_data,
            'Sheet2': sheet2_data
        }
        excel_df.total_rows = 2
        excel_df.total_cols = 2
        excel_df.color_map = {}
        excel_df.comment_map = {}

        state = ExcelState(excel_df)

        # Create tasks for both sheets
        tasks = pd.DataFrame({
            'task_id': ['MS001', 'MS002'],
            'operation': ['uppercase', 'uppercase'],
            'sheet_name': ['Sheet1', 'Sheet2'],
            'row_idx': [0, 0],
            'col_idx': [1, 1],
            'source_text': ['hello', 'world'],
            'status': ['pending', 'pending'],
            'result': ['', ''],
            'error_message': ['', ''],
            'updated_at': [datetime.now(), datetime.now()]
        })

        # Execute
        processor = UppercaseProcessor()
        transformer = BaseTransformer(processor)
        new_state = transformer.execute(state, tasks)

        # Verify both sheets updated
        assert new_state.get_cell_value('Sheet1', 0, 1) == 'HELLO'
        assert new_state.get_cell_value('Sheet2', 0, 1) == 'WORLD'
        assert all(tasks['status'] == 'completed')

    def test_chained_transformations(self):
        """Test chaining multiple transformations (simulating multi-stage pipeline)."""
        # Create initial state
        excel_df = ExcelDataFrame()
        excel_df.filename = "chain.xlsx"
        excel_df.excel_id = "chain_001"
        test_data = pd.DataFrame({'A': ['original'], 'B': ['']})
        excel_df.sheets = {'Sheet1': test_data}
        excel_df.total_rows = len(test_data)
        excel_df.total_cols = len(test_data.columns)
        excel_df.color_map = {}
        excel_df.comment_map = {}

        state_0 = ExcelState(excel_df)

        # Stage 1: First transformation
        tasks_1 = pd.DataFrame({
            'task_id': ['C001'],
            'operation': ['uppercase'],
            'sheet_name': ['Sheet1'],
            'row_idx': [0],
            'col_idx': [1],
            'source_text': ['stage1'],
            'status': ['pending'],
            'result': [''],
            'error_message': [''],
            'updated_at': [datetime.now()]
        })

        processor_1 = UppercaseProcessor()
        transformer_1 = BaseTransformer(processor_1)
        state_1 = transformer_1.execute(state_0, tasks_1)

        # Stage 2: Second transformation (using result from stage 1)
        tasks_2 = pd.DataFrame({
            'task_id': ['C002'],
            'operation': ['uppercase'],
            'sheet_name': ['Sheet1'],
            'row_idx': [0],
            'col_idx': [1],
            'source_text': ['stage2_should_be_replaced'],
            'depends_on': ['C001'],
            'status': ['pending'],
            'result': [''],
            'error_message': [''],
            'updated_at': [datetime.now()]
        })

        # Pass stage 1 results as context
        context = {
            'previous_tasks': {
                'C001': {'result': tasks_1.loc[0, 'result']}
            }
        }

        processor_2 = UppercaseProcessor()
        transformer_2 = BaseTransformer(processor_2)
        state_2 = transformer_2.execute(state_1, tasks_2, context=context)

        # Verify chaining worked
        assert state_0 is not state_1
        assert state_1 is not state_2
        assert tasks_1.loc[0, 'status'] == 'completed'
        assert tasks_2.loc[0, 'status'] == 'completed'


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
