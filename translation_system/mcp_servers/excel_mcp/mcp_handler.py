"""MCP tool handler - implements tool execution logic."""

import asyncio
import logging
import base64
import json
from typing import Dict, Any
from io import BytesIO

from utils.token_validator import token_validator
from utils.session_manager import session_manager
from models.session_data import SessionStatus
from services.task_queue import task_queue

logger = logging.getLogger(__name__)


class MCPHandler:
    """Handler for MCP tool calls."""

    async def handle_tool_call(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle MCP tool call.

        Args:
            tool_name: Name of the tool to execute
            arguments: Tool arguments

        Returns:
            Tool execution result
        """
        try:
            # Validate token
            token = arguments.get('token')
            if not token:
                return self._error_response("Missing token")

            try:
                payload = token_validator.validate(token)
            except Exception as e:
                return self._error_response(f"Token validation failed: {str(e)}")

            # Route to appropriate handler
            if tool_name == "excel_analyze":
                return await self._handle_excel_analyze(arguments, payload)
            elif tool_name == "excel_get_status":
                return await self._handle_excel_get_status(arguments, payload)
            elif tool_name == "excel_get_sheets":
                return await self._handle_excel_get_sheets(arguments, payload)
            elif tool_name == "excel_parse_sheet":
                return await self._handle_excel_parse_sheet(arguments, payload)
            elif tool_name == "excel_convert_to_json":
                return await self._handle_excel_convert_to_json(arguments, payload)
            elif tool_name == "excel_convert_to_csv":
                return await self._handle_excel_convert_to_csv(arguments, payload)
            elif tool_name == "excel_split_tasks":
                return await self._handle_excel_split_tasks(arguments, payload)
            elif tool_name == "excel_get_tasks":
                return await self._handle_excel_get_tasks(arguments, payload)
            elif tool_name == "excel_get_batches":
                return await self._handle_excel_get_batches(arguments, payload)
            elif tool_name == "excel_export_tasks":
                return await self._handle_excel_export_tasks(arguments, payload)
            else:
                return self._error_response(f"Unknown tool: {tool_name}")

        except Exception as e:
            logger.error(f"Error handling tool call {tool_name}: {e}")
            return self._error_response(str(e))

    async def _handle_excel_analyze(self, arguments: Dict[str, Any], payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle excel_analyze tool."""
        file_url = arguments.get('file_url')
        file_base64 = arguments.get('file')
        filename = arguments.get('filename', 'uploaded.xlsx')
        options = arguments.get('options', {})

        # Must provide either file_url or file
        if not file_url and not file_base64:
            return self._error_response("Must provide either file_url or file")

        # Create session
        session_id = session_manager.create_session()
        session = session_manager.get_session(session_id)

        # Prepare file data
        file_data = None
        if file_base64:
            try:
                file_bytes = base64.b64decode(file_base64)
                file_data = BytesIO(file_bytes)
            except Exception as e:
                return self._error_response(f"Invalid file encoding: {str(e)}")

        # Submit task to queue
        await task_queue.submit_analysis_task(
            session_id=session_id,
            file_data=file_data,
            file_url=file_url,
            filename=filename,
            options=options
        )

        return {
            "session_id": session_id,
            "status": "queued",
            "message": "Analysis task submitted to queue",
            "estimated_time": 30
        }

    async def _handle_excel_get_status(self, arguments: Dict[str, Any], payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle excel_get_status tool."""
        session_id = arguments.get('session_id')
        if not session_id:
            return self._error_response("Missing session_id")

        session = session_manager.get_session(session_id)
        if not session:
            return self._error_response("Session not found")

        response = {
            "session_id": session_id,
            "status": session.status.value,
            "progress": session.progress,
            "has_analysis": session.has_analysis,
            "has_tasks": session.has_tasks
        }

        if session.status == SessionStatus.COMPLETED:
            response["result"] = session.analysis
        elif session.status == SessionStatus.FAILED:
            response["error"] = session.error
        elif session.status == SessionStatus.PROCESSING:
            response["message"] = f"Processing... {session.progress}%"
        elif session.status == SessionStatus.SPLITTING:
            response["message"] = f"Splitting tasks... {session.progress}%"

        return response

    async def _handle_excel_get_sheets(self, arguments: Dict[str, Any], payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle excel_get_sheets tool."""
        session_id = arguments.get('session_id')
        if not session_id:
            return self._error_response("Missing session_id")

        session = session_manager.get_session(session_id)
        if not session:
            return self._error_response("Session not found")

        if session.status != SessionStatus.COMPLETED:
            return self._error_response("Analysis not completed yet")

        if not session.excel_df:
            return self._error_response("Excel data not available")

        sheets = []
        for sheet_name in session.excel_df.get_sheet_names():
            df = session.excel_df.get_sheet(sheet_name)
            sheets.append({
                "name": sheet_name,
                "rows": len(df),
                "cols": len(df.columns)
            })

        return {
            "session_id": session_id,
            "sheets": sheets
        }

    async def _handle_excel_parse_sheet(self, arguments: Dict[str, Any], payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle excel_parse_sheet tool."""
        session_id = arguments.get('session_id')
        sheet_name = arguments.get('sheet_name')
        limit = arguments.get('limit')
        offset = arguments.get('offset', 0)

        if not session_id or not sheet_name:
            return self._error_response("Missing required parameters")

        session = session_manager.get_session(session_id)
        if not session:
            return self._error_response("Session not found")

        if session.status != SessionStatus.COMPLETED:
            return self._error_response("Analysis not completed yet")

        df = session.excel_df.get_sheet(sheet_name)
        if df is None:
            return self._error_response(f"Sheet not found: {sheet_name}")

        # Apply offset and limit
        total_rows = len(df)
        df_subset = df.iloc[offset:offset + limit if limit else None]

        # Convert to list of dicts
        data = df_subset.to_dict(orient='records')

        return {
            "session_id": session_id,
            "sheet_name": sheet_name,
            "data": data,
            "total_rows": total_rows,
            "returned_rows": len(data),
            "offset": offset
        }

    async def _handle_excel_convert_to_json(self, arguments: Dict[str, Any], payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle excel_convert_to_json tool."""
        session_id = arguments.get('session_id')
        sheet_name = arguments.get('sheet_name')

        if not session_id:
            return self._error_response("Missing session_id")

        session = session_manager.get_session(session_id)
        if not session:
            return self._error_response("Session not found")

        if session.status != SessionStatus.COMPLETED:
            return self._error_response("Analysis not completed yet")

        result = {}

        if sheet_name:
            # Convert specific sheet
            df = session.excel_df.get_sheet(sheet_name)
            if df is None:
                return self._error_response(f"Sheet not found: {sheet_name}")
            result[sheet_name] = df.to_dict(orient='records')
        else:
            # Convert all sheets
            for sname in session.excel_df.get_sheet_names():
                df = session.excel_df.get_sheet(sname)
                result[sname] = df.to_dict(orient='records')

        return {
            "session_id": session_id,
            "data": result
        }

    async def _handle_excel_convert_to_csv(self, arguments: Dict[str, Any], payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle excel_convert_to_csv tool."""
        session_id = arguments.get('session_id')
        sheet_name = arguments.get('sheet_name')

        if not session_id or not sheet_name:
            return self._error_response("Missing required parameters")

        session = session_manager.get_session(session_id)
        if not session:
            return self._error_response("Session not found")

        if session.status != SessionStatus.COMPLETED:
            return self._error_response("Analysis not completed yet")

        df = session.excel_df.get_sheet(sheet_name)
        if df is None:
            return self._error_response(f"Sheet not found: {sheet_name}")

        # Convert to CSV
        csv_data = df.to_csv(index=False)

        return {
            "session_id": session_id,
            "sheet_name": sheet_name,
            "csv": csv_data
        }

    async def _handle_excel_split_tasks(self, arguments: Dict[str, Any], payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle excel_split_tasks tool."""
        session_id = arguments.get('session_id')
        target_langs = arguments.get('target_langs')
        source_lang = arguments.get('source_lang')
        extract_context = arguments.get('extract_context', True)
        context_options = arguments.get('context_options', {})

        if not session_id or not target_langs:
            return self._error_response("Missing required parameters: session_id, target_langs")

        session = session_manager.get_session(session_id)
        if not session:
            return self._error_response("Session not found")

        # Check if analysis is completed
        if not session.has_analysis:
            return self._error_response("Excel analysis not completed yet. Run excel_analyze first.")

        if not session.excel_df:
            return self._error_response("Excel data not available")

        # Submit task splitting to queue
        await task_queue.submit_task_split(
            session_id=session_id,
            source_lang=source_lang,
            target_langs=target_langs,
            extract_context=extract_context,
            context_options=context_options
        )

        return {
            "session_id": session_id,
            "status": "splitting",
            "message": "Task splitting submitted to queue",
            "target_langs": target_langs
        }

    async def _handle_excel_get_tasks(self, arguments: Dict[str, Any], payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle excel_get_tasks tool."""
        session_id = arguments.get('session_id')
        preview_limit = arguments.get('preview_limit', 10)

        if not session_id:
            return self._error_response("Missing session_id")

        session = session_manager.get_session(session_id)
        if not session:
            return self._error_response("Session not found")

        response = {
            "session_id": session_id,
            "status": session.status.value,
            "progress": session.progress
        }

        if session.status == SessionStatus.COMPLETED and session.has_tasks:
            # Return task summary and preview
            response["result"] = {
                "summary": session.tasks_summary,
                "preview_tasks": session.tasks[:preview_limit],
                "total_tasks": len(session.tasks)
            }
        elif session.status == SessionStatus.FAILED:
            response["error"] = session.error
        elif session.status == SessionStatus.SPLITTING:
            response["message"] = f"Splitting tasks... {session.progress}%"
        else:
            response["message"] = "Tasks not available. Run excel_split_tasks first."

        return response

    async def _handle_excel_get_batches(self, arguments: Dict[str, Any], payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle excel_get_batches tool."""
        session_id = arguments.get('session_id')

        if not session_id:
            return self._error_response("Missing session_id")

        session = session_manager.get_session(session_id)
        if not session:
            return self._error_response("Session not found")

        if not session.has_tasks:
            return self._error_response("Tasks not available. Run excel_split_tasks first.")

        # Extract batch information from tasks
        batches = {}
        for task in session.tasks:
            batch_id = task.get('batch_id')
            if batch_id:
                if batch_id not in batches:
                    batches[batch_id] = {
                        "batch_id": batch_id,
                        "target_lang": task.get('target_lang'),
                        "task_count": 0,
                        "char_count": 0,
                        "task_types": {}
                    }

                batches[batch_id]["task_count"] += 1
                batches[batch_id]["char_count"] += len(task.get('source_text', ''))

                task_type = task.get('task_type', 'normal')
                batches[batch_id]["task_types"][task_type] = batches[batch_id]["task_types"].get(task_type, 0) + 1

        return {
            "session_id": session_id,
            "batches": list(batches.values())
        }

    async def _handle_excel_export_tasks(self, arguments: Dict[str, Any], payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle excel_export_tasks tool."""
        session_id = arguments.get('session_id')
        export_format = arguments.get('format', 'excel')
        include_context = arguments.get('include_context', True)

        if not session_id:
            return self._error_response("Missing session_id")

        session = session_manager.get_session(session_id)
        if not session:
            return self._error_response("Session not found")

        if not session.has_tasks:
            return self._error_response("Tasks not available. Run excel_split_tasks first.")

        # Submit export task to queue
        await task_queue.submit_export_task(
            session_id=session_id,
            export_format=export_format,
            include_context=include_context
        )

        # Check if export is already completed (in metadata)
        if 'download_url' in session.metadata:
            return {
                "session_id": session_id,
                "status": "completed",
                "download_url": session.metadata['download_url'],
                "export_path": session.metadata.get('export_path'),
                "format": export_format
            }

        return {
            "session_id": session_id,
            "status": "exporting",
            "message": f"Exporting tasks to {export_format} format",
            "format": export_format
        }

    def _error_response(self, message: str) -> Dict[str, Any]:
        """Create error response."""
        return {
            "error": {
                "code": "ERROR",
                "message": message
            }
        }


# Global handler instance
mcp_handler = MCPHandler()
