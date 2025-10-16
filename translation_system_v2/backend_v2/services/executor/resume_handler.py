"""Resume handler for interrupted translation sessions."""

import os
import json
import pickle
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
import pandas as pd

from models.excel_dataframe import ExcelDataFrame
from models.task_dataframe import TaskDataFrameManager, TaskStatus
from models.game_info import GameInfo
from utils.pipeline_session_manager import pipeline_session_manager
from database.mysql_connector import mysql_connector


logger = logging.getLogger(__name__)


class ResumeHandler:
    """Handle resumption of interrupted translation sessions."""

    def __init__(self, checkpoint_dir: str = None):
        """
        Initialize ResumeHandler.

        Args:
            checkpoint_dir: Directory for storing checkpoints
        """
        self.checkpoint_dir = Path(checkpoint_dir) if checkpoint_dir else Path("./checkpoints")
        self.checkpoint_dir.mkdir(exist_ok=True)
        self.logger = logging.getLogger(self.__class__.__name__)

        # Checkpoint configuration
        self.max_checkpoint_age = timedelta(days=7)  # Keep checkpoints for 7 days
        self.compression_enabled = True

    async def create_checkpoint(self, session_id: str) -> str:
        """
        Create a checkpoint for the current session state.

        Args:
            session_id: Session identifier

        Returns:
            Checkpoint file path
        """
        try:
            # Get session using pipeline architecture
            session = pipeline_session_manager.get_session(session_id)
            if not session:
                raise ValueError(f"Session {session_id} not found")

            excel_df = session.output_state or session.input_state
            task_manager = session.tasks

            if not excel_df or not task_manager:
                raise ValueError(f"Incomplete session data for {session_id}")

            # Create checkpoint data structure
            checkpoint_data = {
                'session_id': session_id,
                'checkpoint_time': datetime.now().isoformat(),
                'version': '1.0',
                'metadata': {
                    'filename': excel_df.filename,
                    'total_tasks': len(task_manager.df) if task_manager.df is not None else 0,
                    'completed_tasks': len(task_manager.get_tasks_by_status('completed')),
                    'failed_tasks': len(task_manager.get_tasks_by_status('failed')),
                    'pending_tasks': len(task_manager.get_pending_tasks())
                }
            }

            # Create checkpoint filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            checkpoint_filename = f"checkpoint_{session_id}_{timestamp}.pkl"
            checkpoint_path = self.checkpoint_dir / checkpoint_filename

            # Prepare data for serialization (pipeline architecture)
            serialization_data = {
                'checkpoint_info': checkpoint_data,
                'excel_df': excel_df,
                'task_df': task_manager.df.to_dict('records') if task_manager.df is not None else [],
                'session_metadata': session.metadata,
                'session_stage': session.stage.value,
                'parent_session_id': session.parent_session_id
            }

            # Save checkpoint
            if self.compression_enabled:
                import gzip
                with gzip.open(str(checkpoint_path) + '.gz', 'wb') as f:
                    pickle.dump(serialization_data, f, protocol=pickle.HIGHEST_PROTOCOL)
                checkpoint_path = Path(str(checkpoint_path) + '.gz')
            else:
                with open(checkpoint_path, 'wb') as f:
                    pickle.dump(serialization_data, f, protocol=pickle.HIGHEST_PROTOCOL)

            # Also save metadata as JSON for easy inspection
            metadata_path = checkpoint_path.with_suffix('.json')
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(checkpoint_data, f, indent=2, ensure_ascii=False)

            # Store checkpoint reference in session
            pipeline_session_manager.set_metadata(session_id, 'latest_checkpoint', str(checkpoint_path))

            # Persist checkpoint info to database if available
            try:
                await mysql_connector.log_execution(
                    session_id, 'INFO',
                    f"Checkpoint created: {checkpoint_filename}",
                    {'checkpoint_path': str(checkpoint_path), 'metadata': checkpoint_data['metadata']},
                    'ResumeHandler'
                )
            except Exception as e:
                self.logger.warning(f"Failed to log checkpoint to database: {e}")

            self.logger.info(f"Checkpoint created: {checkpoint_path}")
            return str(checkpoint_path)

        except Exception as e:
            self.logger.error(f"Failed to create checkpoint for session {session_id}: {e}")
            raise

    async def restore_checkpoint(self, checkpoint_path: str) -> str:
        """
        Restore session from checkpoint.

        Args:
            checkpoint_path: Path to checkpoint file

        Returns:
            Restored session ID
        """
        try:
            checkpoint_file = Path(checkpoint_path)
            if not checkpoint_file.exists():
                raise FileNotFoundError(f"Checkpoint file not found: {checkpoint_path}")

            self.logger.info(f"Restoring checkpoint: {checkpoint_path}")

            # Load checkpoint data
            if checkpoint_file.suffix == '.gz':
                import gzip
                with gzip.open(checkpoint_file, 'rb') as f:
                    data = pickle.load(f)
            else:
                with open(checkpoint_file, 'rb') as f:
                    data = pickle.load(f)

            # Extract data (pipeline architecture compatible)
            checkpoint_info = data['checkpoint_info']
            excel_df = data['excel_df']
            task_records = data['task_df']
            session_metadata = data.get('session_metadata', {})
            parent_session_id = data.get('parent_session_id')

            original_session_id = checkpoint_info['session_id']

            # Create new session for restoration (pipeline architecture)
            new_session = pipeline_session_manager.create_session(parent_session_id=parent_session_id)
            new_session_id = new_session.session_id

            # Restore input state with Excel DataFrame
            pipeline_session_manager.set_input_from_file(new_session_id, excel_df)

            # Restore Task DataFrame
            if task_records:
                task_manager = TaskDataFrameManager()
                task_df = pd.DataFrame(task_records)

                # Ensure proper data types
                for col, dtype in task_manager.TASK_DF_COLUMNS.items():
                    if col in task_df.columns:
                        if dtype == 'datetime64[ns]':
                            task_df[col] = pd.to_datetime(task_df[col])
                        elif dtype in ['int8', 'int32']:
                            task_df[col] = task_df[col].astype(dtype, errors='ignore')
                        elif dtype == 'float32':
                            task_df[col] = task_df[col].astype(dtype, errors='ignore')
                        elif dtype == 'category':
                            task_df[col] = task_df[col].astype('category')
                        elif dtype == bool:
                            task_df[col] = task_df[col].astype(bool, errors='ignore')

                task_manager.df = task_df
                pipeline_session_manager.set_tasks(new_session_id, task_manager)

            # Restore metadata (all app-specific data stored here in new architecture)
            for key, value in session_metadata.items():
                pipeline_session_manager.set_metadata(new_session_id, key, value)

            # Mark as restored session
            pipeline_session_manager.set_metadata(new_session_id, 'restored_from', original_session_id)
            pipeline_session_manager.set_metadata(new_session_id, 'restored_at', datetime.now().isoformat())
            pipeline_session_manager.set_metadata(new_session_id, 'checkpoint_path', checkpoint_path)

            # Log restoration
            try:
                await mysql_connector.log_execution(
                    new_session_id, 'INFO',
                    f"Session restored from checkpoint",
                    {
                        'original_session_id': original_session_id,
                        'checkpoint_path': checkpoint_path,
                        'restored_tasks': len(task_records) if task_records else 0
                    },
                    'ResumeHandler'
                )
            except Exception as e:
                self.logger.warning(f"Failed to log restoration to database: {e}")

            self.logger.info(
                f"Successfully restored session {new_session_id} from {original_session_id}"
            )

            return new_session_id

        except Exception as e:
            self.logger.error(f"Failed to restore checkpoint {checkpoint_path}: {e}")
            raise

    async def find_latest_checkpoint(self, session_id: str) -> Optional[str]:
        """
        Find the latest checkpoint for a session.

        Args:
            session_id: Session identifier

        Returns:
            Path to latest checkpoint or None
        """
        try:
            # Check session metadata first
            latest_checkpoint = pipeline_session_manager.get_metadata(session_id, 'latest_checkpoint')
            if latest_checkpoint and Path(latest_checkpoint).exists():
                return latest_checkpoint

            # Search checkpoint directory
            pattern = f"checkpoint_{session_id}_*.pkl*"
            checkpoint_files = list(self.checkpoint_dir.glob(pattern))

            if not checkpoint_files:
                return None

            # Sort by modification time (newest first)
            checkpoint_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

            latest_file = checkpoint_files[0]
            self.logger.debug(f"Found latest checkpoint: {latest_file}")

            return str(latest_file)

        except Exception as e:
            self.logger.error(f"Failed to find latest checkpoint for {session_id}: {e}")
            return None

    async def list_checkpoints(self, session_id: str = None) -> List[Dict[str, Any]]:
        """
        List available checkpoints.

        Args:
            session_id: Optional session ID to filter by

        Returns:
            List of checkpoint information
        """
        try:
            checkpoints = []

            if session_id:
                pattern = f"checkpoint_{session_id}_*.pkl*"
            else:
                pattern = "checkpoint_*.pkl*"

            for checkpoint_file in self.checkpoint_dir.glob(pattern):
                try:
                    # Try to read metadata JSON file
                    metadata_file = checkpoint_file.with_suffix('.json')
                    if metadata_file.exists():
                        with open(metadata_file, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)
                    else:
                        # Fallback: extract from filename
                        filename = checkpoint_file.stem
                        if filename.endswith('.pkl'):
                            filename = filename[:-4]  # Remove .pkl extension

                        parts = filename.split('_')
                        if len(parts) >= 3:
                            session_id_from_name = parts[1]
                            timestamp_str = '_'.join(parts[2:])
                        else:
                            session_id_from_name = 'unknown'
                            timestamp_str = 'unknown'

                        metadata = {
                            'session_id': session_id_from_name,
                            'checkpoint_time': timestamp_str,
                            'metadata': {}
                        }

                    # Add file information
                    file_stat = checkpoint_file.stat()
                    metadata['file_info'] = {
                        'path': str(checkpoint_file),
                        'size_bytes': file_stat.st_size,
                        'modified_time': datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
                        'compressed': checkpoint_file.suffix == '.gz'
                    }

                    checkpoints.append(metadata)

                except Exception as e:
                    self.logger.warning(f"Failed to read checkpoint metadata {checkpoint_file}: {e}")
                    continue

            # Sort by checkpoint time (newest first)
            checkpoints.sort(
                key=lambda x: x.get('checkpoint_time', ''),
                reverse=True
            )

            return checkpoints

        except Exception as e:
            self.logger.error(f"Failed to list checkpoints: {e}")
            return []

    async def can_resume_session(self, session_id: str) -> Dict[str, Any]:
        """
        Check if a session can be resumed.

        Args:
            session_id: Session identifier

        Returns:
            Resume capability information
        """
        try:
            # Check if session exists in memory
            session = pipeline_session_manager.get_session(session_id)
            has_active_session = session is not None

            # Check for checkpoints
            latest_checkpoint = await self.find_latest_checkpoint(session_id)
            has_checkpoint = latest_checkpoint is not None

            # Get session status from database if available
            db_session = None
            incomplete_tasks = 0

            try:
                db_session = await mysql_connector.get_session(session_id)
                if db_session:
                    pending_tasks = await mysql_connector.get_tasks_by_session(
                        session_id, 'pending'
                    )
                    processing_tasks = await mysql_connector.get_tasks_by_session(
                        session_id, 'processing'
                    )
                    incomplete_tasks = len(pending_tasks) + len(processing_tasks)
            except Exception as e:
                self.logger.warning(f"Failed to query database for session {session_id}: {e}")

            # Determine resumability
            can_resume = has_active_session or has_checkpoint or (db_session and incomplete_tasks > 0)

            resume_info = {
                'session_id': session_id,
                'can_resume': can_resume,
                'has_active_session': has_active_session,
                'has_checkpoint': has_checkpoint,
                'latest_checkpoint': latest_checkpoint,
                'incomplete_tasks': incomplete_tasks,
                'database_session': db_session is not None,
                'resume_options': []
            }

            # Add resume options
            if has_active_session:
                resume_info['resume_options'].append('continue_active')

            if has_checkpoint:
                resume_info['resume_options'].append('restore_checkpoint')

            if db_session and incomplete_tasks > 0:
                resume_info['resume_options'].append('restore_from_database')

            return resume_info

        except Exception as e:
            self.logger.error(f"Failed to check resume capability for {session_id}: {e}")
            return {
                'session_id': session_id,
                'can_resume': False,
                'error': str(e)
            }

    async def cleanup_old_checkpoints(self, max_age_days: int = 7):
        """
        Clean up old checkpoint files.

        Args:
            max_age_days: Maximum age of checkpoints to keep
        """
        try:
            if not self.checkpoint_dir.exists():
                return

            current_time = datetime.now()
            cleanup_count = 0

            for checkpoint_file in self.checkpoint_dir.glob("checkpoint_*.pkl*"):
                try:
                    file_time = datetime.fromtimestamp(checkpoint_file.stat().st_mtime)
                    age_days = (current_time - file_time).days

                    if age_days > max_age_days:
                        # Remove checkpoint file
                        checkpoint_file.unlink()
                        cleanup_count += 1

                        # Remove associated JSON metadata file
                        json_file = checkpoint_file.with_suffix('.json')
                        if json_file.exists():
                            json_file.unlink()

                        self.logger.debug(f"Removed old checkpoint: {checkpoint_file}")

                except Exception as e:
                    self.logger.warning(f"Failed to remove checkpoint {checkpoint_file}: {e}")

            if cleanup_count > 0:
                self.logger.info(f"Cleaned up {cleanup_count} old checkpoint files")

        except Exception as e:
            self.logger.error(f"Failed to cleanup old checkpoints: {e}")

    async def get_checkpoint_info(self, checkpoint_path: str) -> Dict[str, Any]:
        """
        Get information about a specific checkpoint.

        Args:
            checkpoint_path: Path to checkpoint file

        Returns:
            Checkpoint information
        """
        try:
            checkpoint_file = Path(checkpoint_path)
            if not checkpoint_file.exists():
                return {'error': 'Checkpoint file not found'}

            # Try to read metadata JSON first
            metadata_file = checkpoint_file.with_suffix('.json')
            if metadata_file.exists():
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
            else:
                # Load checkpoint to extract metadata
                if checkpoint_file.suffix == '.gz':
                    import gzip
                    with gzip.open(checkpoint_file, 'rb') as f:
                        data = pickle.load(f)
                else:
                    with open(checkpoint_file, 'rb') as f:
                        data = pickle.load(f)

                metadata = data.get('checkpoint_info', {})

            # Add file information
            file_stat = checkpoint_file.stat()
            metadata['file_info'] = {
                'path': str(checkpoint_file),
                'size_bytes': file_stat.st_size,
                'size_mb': round(file_stat.st_size / (1024 * 1024), 2),
                'modified_time': datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
                'compressed': checkpoint_file.suffix == '.gz'
            }

            return metadata

        except Exception as e:
            self.logger.error(f"Failed to get checkpoint info for {checkpoint_path}: {e}")
            return {'error': str(e)}


# Global resume handler instance
resume_handler = ResumeHandler()