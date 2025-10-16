"""Checkpoint service for saving and restoring session state."""

import asyncio
import logging
import pickle
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
import pandas as pd
import aiofiles

from models.task_dataframe import TaskDataFrameManager
from models.excel_dataframe import ExcelDataFrame
from utils.pipeline_session_manager import pipeline_session_manager

logger = logging.getLogger(__name__)


class CheckpointService:
    """Save and restore execution checkpoints."""

    def __init__(self, checkpoint_dir: str = "./checkpoints"):
        """
        Initialize checkpoint service.

        Args:
            checkpoint_dir: Directory to store checkpoints
        """
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.auto_checkpoint_tasks: Dict[str, asyncio.Task] = {}
        self.checkpoint_interval = 60  # seconds

    async def save_checkpoint(
        self,
        session_id: str,
        checkpoint_type: str = 'auto'
    ) -> Dict[str, Any]:
        """
        Save a checkpoint for a session.

        Args:
            session_id: Session ID
            checkpoint_type: Type of checkpoint (auto, manual, error)

        Returns:
            Checkpoint information
        """
        start_time = datetime.now()
        self.logger.info(f"Saving {checkpoint_type} checkpoint for session {session_id}")

        try:
            # Get managers
            task_manager = pipeline_session_manager.get_tasks(session_id)
            excel_manager = pipeline_session_manager.get_excel_manager(session_id)

            if not task_manager or task_manager.df is None:
                raise ValueError(f"No task manager found for session {session_id}")

            # Create checkpoint directory for session
            session_dir = self.checkpoint_dir / session_id
            session_dir.mkdir(exist_ok=True)

            # Generate checkpoint ID
            checkpoint_id = datetime.now().strftime("%Y%m%d_%H%M%S")
            checkpoint_path = session_dir / f"checkpoint_{checkpoint_id}"
            checkpoint_path.mkdir(exist_ok=True)

            # Save task DataFrame using pickle (no external dependency needed)
            task_df_path = checkpoint_path / "tasks.pkl"
            async with aiofiles.open(task_df_path, 'wb') as f:
                await f.write(pickle.dumps(task_manager.df))

            # Save Excel DataFrames if available
            excel_df_path = None
            if excel_manager and excel_manager.sheets:
                excel_df_path = checkpoint_path / "excel_dfs.pkl"
                # Save the entire ExcelDataFrame object
                async with aiofiles.open(excel_df_path, 'wb') as f:
                    await f.write(pickle.dumps(excel_manager))

            # Calculate progress statistics
            df = task_manager.df
            progress_data = {
                'total_tasks': len(df),
                'completed_tasks': len(df[df['status'] == 'completed']),
                'failed_tasks': len(df[df['status'] == 'failed']),
                'processing_tasks': len(df[df['status'] == 'processing']),
                'pending_tasks': len(df[df['status'] == 'pending']),
                'completion_rate': len(df[df['status'] == 'completed']) / len(df) * 100 if len(df) > 0 else 0
            }

            # Save metadata
            metadata = {
                'session_id': session_id,
                'checkpoint_id': checkpoint_id,
                'checkpoint_type': checkpoint_type,
                'created_at': datetime.now().isoformat(),
                'task_df_path': str(task_df_path),
                'excel_df_path': str(excel_df_path) if excel_df_path else None,
                'progress_data': progress_data,
                'task_count': len(df)
            }

            metadata_path = checkpoint_path / "metadata.json"
            async with aiofiles.open(metadata_path, 'w') as f:
                await f.write(json.dumps(metadata, indent=2))

            duration = (datetime.now() - start_time).total_seconds()
            self.logger.info(
                f"Checkpoint saved for session {session_id}: "
                f"{progress_data['completed_tasks']}/{progress_data['total_tasks']} tasks, "
                f"duration={duration:.2f}s"
            )

            return metadata

        except Exception as e:
            self.logger.error(f"Failed to save checkpoint: {e}")
            raise

    async def restore_checkpoint(
        self,
        session_id: str,
        checkpoint_id: str = None
    ) -> Dict[str, Any]:
        """
        Restore a checkpoint for a session.

        Args:
            session_id: Session ID
            checkpoint_id: Specific checkpoint ID (latest if None)

        Returns:
            Restored checkpoint information
        """
        self.logger.info(f"Restoring checkpoint for session {session_id}")

        try:
            # Find checkpoint
            checkpoint_path = await self._find_checkpoint(session_id, checkpoint_id)
            if not checkpoint_path:
                raise ValueError(f"No checkpoint found for session {session_id}")

            # Load metadata
            metadata_path = checkpoint_path / "metadata.json"
            async with aiofiles.open(metadata_path, 'r') as f:
                metadata = json.loads(await f.read())

            # Restore task DataFrame from pickle
            task_df_path = checkpoint_path / "tasks.pkl"
            if task_df_path.exists():
                async with aiofiles.open(task_df_path, 'rb') as f:
                    task_df = pickle.loads(await f.read())
                
                # Create or update task manager
                task_manager = pipeline_session_manager.get_tasks(session_id)
                if not task_manager:
                    task_manager = TaskDataFrameManager(session_id)
                    pipeline_session_manager.set_task_manager(session_id, task_manager)
                
                task_manager.df = task_df
                self.logger.info(f"Restored {len(task_df)} tasks")

            # Restore Excel DataFrames if available
            excel_df_path = checkpoint_path / "excel_dfs.pkl"
            if excel_df_path.exists():
                async with aiofiles.open(excel_df_path, 'rb') as f:
                    excel_manager = pickle.loads(await f.read())

                # Set restored Excel manager
                pipeline_session_manager.set_excel_df(session_id, excel_manager)
                self.logger.info(f"Restored Excel data with {len(excel_manager.sheets)} sheets")

            self.logger.info(
                f"Checkpoint restored: {metadata['progress_data']['completed_tasks']}/"
                f"{metadata['progress_data']['total_tasks']} tasks completed"
            )

            return metadata

        except Exception as e:
            self.logger.error(f"Failed to restore checkpoint: {e}")
            raise

    async def _find_checkpoint(
        self,
        session_id: str,
        checkpoint_id: str = None
    ) -> Optional[Path]:
        """
        Find checkpoint directory.

        Args:
            session_id: Session ID
            checkpoint_id: Specific checkpoint ID or None for latest

        Returns:
            Path to checkpoint directory or None
        """
        session_dir = self.checkpoint_dir / session_id
        if not session_dir.exists():
            return None

        if checkpoint_id:
            # Find specific checkpoint
            checkpoint_path = session_dir / f"checkpoint_{checkpoint_id}"
            if checkpoint_path.exists():
                return checkpoint_path
        else:
            # Find latest checkpoint
            checkpoints = sorted(session_dir.glob("checkpoint_*"))
            if checkpoints:
                return checkpoints[-1]

        return None

    async def start_auto_checkpoint(self, session_id: str):
        """
        Start automatic checkpoint saving.

        Args:
            session_id: Session ID
        """
        # Stop existing task if any
        await self.stop_auto_checkpoint(session_id)

        # Start new checkpoint task
        task = asyncio.create_task(self._auto_checkpoint_loop(session_id))
        self.auto_checkpoint_tasks[session_id] = task
        self.logger.info(f"Started auto-checkpoint for session {session_id}")

    async def stop_auto_checkpoint(self, session_id: str):
        """
        Stop automatic checkpoint saving.

        Args:
            session_id: Session ID
        """
        if session_id in self.auto_checkpoint_tasks:
            task = self.auto_checkpoint_tasks[session_id]
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            del self.auto_checkpoint_tasks[session_id]
            self.logger.info(f"Stopped auto-checkpoint for session {session_id}")

    async def _auto_checkpoint_loop(self, session_id: str):
        """
        Automatic checkpoint loop.

        Args:
            session_id: Session ID
        """
        while True:
            try:
                await asyncio.sleep(self.checkpoint_interval)
                await self.save_checkpoint(session_id, 'auto')
                
                # Check if execution is complete
                task_manager = pipeline_session_manager.get_tasks(session_id)
                if task_manager and task_manager.df is not None:
                    df = task_manager.df
                    pending = len(df[df['status'] == 'pending'])
                    processing = len(df[df['status'] == 'processing'])
                    
                    if pending == 0 and processing == 0:
                        # Final checkpoint
                        await self.save_checkpoint(session_id, 'manual')
                        break
                        
            except asyncio.CancelledError:
                # Save final checkpoint on cancellation
                await self.save_checkpoint(session_id, 'error')
                raise
            except Exception as e:
                self.logger.error(f"Error in auto-checkpoint loop: {e}")

    async def list_checkpoints(self, session_id: str) -> List[Dict[str, Any]]:
        """
        List all checkpoints for a session.

        Args:
            session_id: Session ID

        Returns:
            List of checkpoint metadata
        """
        checkpoints = []
        session_dir = self.checkpoint_dir / session_id
        
        if session_dir.exists():
            for checkpoint_dir in sorted(session_dir.glob("checkpoint_*")):
                metadata_path = checkpoint_dir / "metadata.json"
                if metadata_path.exists():
                    async with aiofiles.open(metadata_path, 'r') as f:
                        metadata = json.loads(await f.read())
                        checkpoints.append(metadata)

        return checkpoints

    async def cleanup_old_checkpoints(self, days_old: int = 7):
        """
        Clean up old checkpoints.

        Args:
            days_old: Remove checkpoints older than this many days
        """
        import shutil
        from datetime import timedelta
        
        cutoff_date = datetime.now() - timedelta(days=days_old)
        removed_count = 0
        
        for session_dir in self.checkpoint_dir.iterdir():
            if session_dir.is_dir():
                for checkpoint_dir in session_dir.glob("checkpoint_*"):
                    metadata_path = checkpoint_dir / "metadata.json"
                    if metadata_path.exists():
                        async with aiofiles.open(metadata_path, 'r') as f:
                            metadata = json.loads(await f.read())
                            created_at = datetime.fromisoformat(metadata['created_at'])
                            if created_at < cutoff_date:
                                shutil.rmtree(checkpoint_dir)
                                removed_count += 1
        
        self.logger.info(f"Cleaned up {removed_count} old checkpoints")


# Global checkpoint service instance
checkpoint_service = CheckpointService()