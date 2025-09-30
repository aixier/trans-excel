"""WebSocket API for real-time progress updates."""

import asyncio
import logging
import json
from typing import Dict, Any, Set, Optional
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect, WebSocketException
from fastapi import APIRouter, Depends, Query, status

from services.executor.progress_tracker import progress_tracker
from utils.session_manager import session_manager
from models.task_dataframe import TaskStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["WebSocket"])


class ConnectionManager:
    """Manage WebSocket connections."""

    def __init__(self):
        """Initialize connection manager."""
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.connection_sessions: Dict[WebSocket, str] = {}
        self.logger = logging.getLogger(self.__class__.__name__)

    async def connect(self, websocket: WebSocket, session_id: str):
        """
        Accept and register a WebSocket connection.

        Args:
            websocket: WebSocket connection
            session_id: Session ID
        """
        await websocket.accept()
        
        if session_id not in self.active_connections:
            self.active_connections[session_id] = set()
        
        self.active_connections[session_id].add(websocket)
        self.connection_sessions[websocket] = session_id
        
        self.logger.info(f"WebSocket connected for session {session_id}")
        
        # Send initial status
        await self.send_initial_status(websocket, session_id)

    async def disconnect(self, websocket: WebSocket):
        """
        Remove a WebSocket connection.

        Args:
            websocket: WebSocket connection
        """
        session_id = self.connection_sessions.get(websocket)
        
        if session_id and session_id in self.active_connections:
            self.active_connections[session_id].discard(websocket)
            
            # Clean up empty session
            if not self.active_connections[session_id]:
                del self.active_connections[session_id]
        
        if websocket in self.connection_sessions:
            del self.connection_sessions[websocket]
        
        self.logger.info(f"WebSocket disconnected for session {session_id}")

    async def send_initial_status(self, websocket: WebSocket, session_id: str):
        """
        Send initial status to newly connected client.

        Args:
            websocket: WebSocket connection
            session_id: Session ID
        """
        try:
            # Get current progress
            progress = progress_tracker.get_progress(session_id)
            
            # Get session info - SessionData is an object, not a dict
            session_data = session_manager.get_session(session_id)

            # Extract status from SessionData object
            if session_data:
                session_status = getattr(session_data, 'status', 'unknown')
            else:
                session_status = 'not_found'

            initial_data = {
                'type': 'initial_status',
                'timestamp': datetime.now().isoformat(),
                'session_id': session_id,
                'progress': progress,
                'session_status': session_status
            }
            
            await websocket.send_json(initial_data)
            
        except Exception as e:
            self.logger.error(f"Failed to send initial status: {e}")

    async def broadcast_to_session(
        self,
        session_id: str,
        message: Dict[str, Any]
    ):
        """
        Broadcast message to all connections for a session.

        Args:
            session_id: Session ID
            message: Message to broadcast
        """
        if session_id not in self.active_connections:
            return
        
        # Add timestamp if not present
        if 'timestamp' not in message:
            message['timestamp'] = datetime.now().isoformat()
        
        # Send to all connections for this session
        disconnected = []
        for websocket in self.active_connections[session_id]:
            try:
                await websocket.send_json(message)
            except Exception as e:
                self.logger.warning(f"Failed to send to WebSocket: {e}")
                disconnected.append(websocket)
        
        # Clean up disconnected sockets
        for websocket in disconnected:
            await self.disconnect(websocket)

    async def send_progress_update(
        self,
        session_id: str,
        progress: Dict[str, Any]
    ):
        """
        Send progress update to session connections.

        Args:
            session_id: Session ID
            progress: Progress data
        """
        message = {
            'type': 'progress',
            'session_id': session_id,
            'data': progress  # Changed from 'progress' to 'data' to match frontend
        }

        await self.broadcast_to_session(session_id, message)

    async def send_task_update(
        self,
        session_id: str,
        task_id: str,
        status: str,
        **kwargs
    ):
        """
        Send task update to session connections.

        Args:
            session_id: Session ID
            task_id: Task ID
            status: Task status
            **kwargs: Additional task data
        """
        message = {
            'type': 'task_update',
            'session_id': session_id,
            'task_id': task_id,
            'status': status
        }
        message.update(kwargs)
        
        await self.broadcast_to_session(session_id, message)

    async def send_error(
        self,
        session_id: str,
        error_message: str,
        error_type: str = 'error'
    ):
        """
        Send error message to session connections.

        Args:
            session_id: Session ID
            error_message: Error message
            error_type: Type of error
        """
        message = {
            'type': 'error',
            'session_id': session_id,
            'error_type': error_type,
            'message': error_message
        }
        
        await self.broadcast_to_session(session_id, message)

    def get_connection_count(self, session_id: str = None) -> int:
        """
        Get number of active connections.

        Args:
            session_id: Optional session ID to filter by

        Returns:
            Number of active connections
        """
        if session_id:
            return len(self.active_connections.get(session_id, set()))
        
        return sum(len(conns) for conns in self.active_connections.values())

    def get_active_sessions(self) -> Set[str]:
        """
        Get set of sessions with active connections.

        Returns:
            Set of session IDs
        """
        return set(self.active_connections.keys())


# Global connection manager
connection_manager = ConnectionManager()


# Register progress callback
async def progress_callback(session_id: str, progress: Dict[str, Any]):
    """Callback for progress updates."""
    await connection_manager.send_progress_update(session_id, progress)

progress_tracker.register_callback(progress_callback)


@router.websocket("/progress/{session_id}")
async def websocket_progress(
    websocket: WebSocket,
    session_id: str
):
    """
    WebSocket endpoint for real-time progress updates.

    Args:
        websocket: WebSocket connection
        session_id: Session ID to monitor
    """
    await connection_manager.connect(websocket, session_id)
    
    try:
        # Keep connection alive and handle messages
        while True:
            try:
                # Receive message from client
                data = await websocket.receive_json()
                
                # Handle different message types
                message_type = data.get('type')
                
                if message_type == 'ping':
                    # Respond to ping
                    await websocket.send_json({
                        'type': 'pong',
                        'timestamp': datetime.now().isoformat()
                    })
                    
                elif message_type == 'get_progress':
                    # Send current progress
                    progress = progress_tracker.get_progress(session_id)
                    await connection_manager.send_progress_update(session_id, progress)
                    
                elif message_type == 'get_tasks':
                    # Send task information
                    task_manager = session_manager.get_task_manager(session_id)
                    if task_manager and task_manager.df is not None:
                        # Get task summary
                        df = task_manager.df
                        task_summary = {
                            'total': len(df),
                            'by_status': df['status'].value_counts().to_dict()
                        }
                        
                        await websocket.send_json({
                            'type': 'task_summary',
                            'session_id': session_id,
                            'tasks': task_summary,
                            'timestamp': datetime.now().isoformat()
                        })
                    
                else:
                    # Unknown message type
                    await websocket.send_json({
                        'type': 'error',
                        'message': f'Unknown message type: {message_type}',
                        'timestamp': datetime.now().isoformat()
                    })
                    
            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                await websocket.send_json({
                    'type': 'error',
                    'message': 'Invalid JSON received',
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                await websocket.send_json({
                    'type': 'error',
                    'message': str(e),
                    'timestamp': datetime.now().isoformat()
                })
                
    except WebSocketDisconnect:
        await connection_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
        await connection_manager.disconnect(websocket)


@router.websocket("/monitor")
async def websocket_monitor(websocket: WebSocket):
    """
    WebSocket endpoint for system monitoring.
    
    Args:
        websocket: WebSocket connection
    """
    await websocket.accept()
    logger.info("Monitor WebSocket connected")
    
    try:
        # Send system status periodically
        while True:
            try:
                # Gather system information
                active_sessions = connection_manager.get_active_sessions()
                total_connections = connection_manager.get_connection_count()
                
                # Get session statistics
                session_stats = []
                for session_id in active_sessions:
                    progress = progress_tracker.get_progress(session_id)
                    session_stats.append({
                        'session_id': session_id,
                        'connections': connection_manager.get_connection_count(session_id),
                        'progress': progress
                    })
                
                # Send monitoring data
                monitor_data = {
                    'type': 'monitor_update',
                    'timestamp': datetime.now().isoformat(),
                    'active_sessions': len(active_sessions),
                    'total_connections': total_connections,
                    'sessions': session_stats
                }
                
                await websocket.send_json(monitor_data)
                
                # Wait before next update
                await asyncio.sleep(5)
                
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"Monitor error: {e}")
                await asyncio.sleep(5)
                
    except WebSocketDisconnect:
        logger.info("Monitor WebSocket disconnected")
    except Exception as e:
        logger.error(f"Monitor connection error: {e}")


# Utility functions for sending updates from other services
async def notify_task_completed(session_id: str, task_id: str, result: str):
    """
    Notify clients that a task is completed.
    
    Args:
        session_id: Session ID
        task_id: Task ID
        result: Translation result
    """
    await connection_manager.send_task_update(
        session_id,
        task_id,
        TaskStatus.COMPLETED,
        result=result
    )


async def notify_task_failed(session_id: str, task_id: str, error: str):
    """
    Notify clients that a task failed.
    
    Args:
        session_id: Session ID
        task_id: Task ID
        error: Error message
    """
    await connection_manager.send_task_update(
        session_id,
        task_id,
        TaskStatus.FAILED,
        error_message=error
    )


async def notify_session_completed(session_id: str):
    """
    Notify clients that a session is completed.
    
    Args:
        session_id: Session ID
    """
    message = {
        'type': 'session_completed',
        'session_id': session_id,
        'timestamp': datetime.now().isoformat()
    }
    
    await connection_manager.broadcast_to_session(session_id, message)