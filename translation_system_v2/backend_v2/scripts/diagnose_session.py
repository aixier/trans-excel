#!/usr/bin/env python3
"""Session diagnostics script to check session state and data."""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.pipeline_session_manager import pipeline_session_manager
from models.pipeline_session import TransformationStage


def diagnose_session(session_id: str):
    """Diagnose a session and print detailed information."""
    print(f"\n{'='*60}")
    print(f"🔍 Session 诊断: {session_id}")
    print(f"{'='*60}\n")

    # 1. Check if session exists
    session = pipeline_session_manager.get_session(session_id)
    if not session:
        print(f"❌ Session 不存在")
        print(f"\n可用的 Session IDs:")
        for sid in pipeline_session_manager.sessions.keys():
            print(f"  - {sid}")
        return

    print(f"✅ Session 存在")

    # 2. Check session stage
    stage = session.stage
    print(f"\n📊 Session 阶段: {stage.value}")
    stage_map = {
        TransformationStage.CREATED: "已创建（需要上传分析）",
        TransformationStage.ANALYZED: "已分析（可以拆分任务）",
        TransformationStage.SPLIT_COMPLETE: "拆分完成（可以执行翻译）",
        TransformationStage.EXECUTING: "执行中",
        TransformationStage.COMPLETED: "已完成",
        TransformationStage.FAILED: "失败"
    }
    print(f"   说明: {stage_map.get(stage, '未知')}")

    # 3. Check Excel data
    print(f"\n📁 Excel 数据:")
    if session.input_state:
        sheets = session.input_state.get_sheet_names()
        print(f"   ✅ 已加载 ({len(sheets)} 个表格)")
        for sheet in sheets:
            print(f"      - {sheet}")
    else:
        print(f"   ❌ 未加载")

    # 4. Check split progress
    print(f"\n✂️ 拆分进度:")
    if session.split_progress:
        sp = session.split_progress
        print(f"   状态: {sp.status.value}")
        print(f"   阶段: {sp.stage.value}")
        print(f"   进度: {sp.progress}%")
        print(f"   消息: {sp.message}")
        print(f"   准备执行: {sp.ready_for_next_stage}")
        if sp.error:
            print(f"   ⚠️ 错误: {sp.error}")
        if sp.metadata:
            print(f"   元数据: {sp.metadata}")
    else:
        print(f"   ⚠️ 未初始化（还未开始拆分）")

    # 5. Check task manager
    print(f"\n📋 任务管理器:")
    task_manager = session.tasks
    if task_manager:
        print(f"   ✅ 已创建")
        if task_manager.df is not None:
            stats = task_manager.get_statistics()
            print(f"   总任务数: {stats.get('total', 0)}")
            print(f"   待处理: {stats.get('pending', 0)}")
            print(f"   处理中: {stats.get('processing', 0)}")
            print(f"   已完成: {stats.get('completed', 0)}")
            print(f"   失败: {stats.get('failed', 0)}")
        else:
            print(f"   ⚠️ DataFrame 为空")
    else:
        print(f"   ❌ 未创建（需要先拆分任务）")

    # 6. Check execution progress
    print(f"\n⚡ 执行进度:")
    if session.execution_progress:
        ep = session.execution_progress
        print(f"   状态: {ep.status.value}")
        print(f"   准备监控: {ep.ready_for_monitoring}")
        print(f"   准备下载: {ep.ready_for_download}")
        stats = ep.statistics
        print(f"   统计: 总{stats['total']}, 完成{stats['completed']}, 失败{stats['failed']}")
        if ep.error:
            print(f"   ⚠️ 错误: {ep.error}")
    else:
        print(f"   ⚠️ 未初始化（还未开始执行）")

    # 7. Diagnosis and recommendations
    print(f"\n{'='*60}")
    print(f"💡 诊断建议:")
    print(f"{'='*60}")

    if stage == TransformationStage.CREATED:
        print(f"📤 需要先上传并分析 Excel 文件")
        print(f"   API: POST /api/analyze/upload")
    elif stage == TransformationStage.ANALYZED:
        if not task_manager:
            print(f"✂️ 需要拆分任务")
            print(f"   API: POST /api/tasks/split")
        else:
            print(f"✅ 任务已拆分，可以执行翻译")
    elif stage == TransformationStage.SPLIT_COMPLETE:
        print(f"✅ 可以开始执行翻译")
        print(f"   API: POST /api/execute/start")
    elif stage == TransformationStage.EXECUTING:
        print(f"⚡ 正在执行中，可以监控进度")
        print(f"   API: GET /api/execute/status/{session_id}")
    elif stage == TransformationStage.COMPLETED:
        print(f"✅ 翻译已完成，可以下载结果")
    elif stage == TransformationStage.FAILED:
        print(f"❌ Session 失败，请检查错误信息")

    # Check specific issue from error message
    if not task_manager and stage != TransformationStage.CREATED:
        print(f"\n⚠️ 检测到问题:")
        print(f"   Session 阶段为 {stage.value}，但任务管理器不存在")
        if session.split_progress:
            if session.split_progress.status.value == 'failed':
                print(f"   ❌ 任务拆分失败: {session.split_progress.error}")
                print(f"   建议: 请重新执行任务拆分")
            elif session.split_progress.status.value != 'completed':
                print(f"   ⏳ 任务拆分尚未完成 (状态: {session.split_progress.status.value})")
                print(f"   建议: 等待拆分完成或重新执行拆分")
        else:
            print(f"   建议: 请执行任务拆分")

    print(f"\n{'='*60}\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python diagnose_session.py <session_id>")
        print("\n可用的 Session IDs:")
        for sid in pipeline_session_manager.sessions.keys():
            print(f"  - {sid}")
        sys.exit(1)

    session_id = sys.argv[1]
    diagnose_session(session_id)
