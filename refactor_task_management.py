#!/usr/bin/env python3
"""
重构task_management.html，去除重复代码
"""

import re

def refactor_html():
    # 读取原文件
    with open('/mnt/d/work/trans_excel/excel_processor/frontend/task_management.html', 'r', encoding='utf-8') as f:
        content = f.read()

    # 查找renderTaskItems函数
    render_task_items_start = content.find('renderTaskItems(tasks) {')
    if render_task_items_start == -1:
        print("未找到renderTaskItems函数")
        return content

    # 查找函数结束位置
    render_task_items_end = content.find('updateOverview(tasks) {', render_task_items_start)
    if render_task_items_end == -1:
        print("未找到renderTaskItems函数结束位置")
        return content

    # 获取原始renderTaskItems函数内容
    original_render_items = content[render_task_items_start:render_task_items_end]

    # 创建统一的任务行生成函数，使用createTaskRowHTML
    optimized_render_items = """renderTaskItems(tasks) {
                const tbody = document.getElementById('task-list-body');
                const emptyState = document.getElementById('empty-state');

                if (!tasks || tasks.length === 0) {
                    tbody.innerHTML = '';
                    emptyState.style.display = 'block';
                    return;
                }

                emptyState.style.display = 'none';

                // 使用统一的createTaskRowHTML方法生成所有任务行
                tbody.innerHTML = tasks.map(task => {
                    // 先更新内部任务Map
                    this.tasks.set(task.task_id, task);
                    // 生成任务行HTML
                    return `<tr data-task-id="${task.task_id}">${this.createTaskRowHTML(task)}</tr>`;
                }).join('');
            }

            """

    # 替换renderTaskItems函数
    content = content[:render_task_items_start] + optimized_render_items + content[render_task_items_end:]

    # 统一createTaskRowHTML函数，使用辅助函数
    create_row_pattern = r'createTaskRowHTML\(task\) \{[\s\S]*?\n\s*\}'

    unified_create_row = """createTaskRowHTML(task) {
                // 统一的任务行HTML生成函数
                const progressText = this.formatProgressText(task);
                const actionButtons = this.generateActionButtons(task);

                return `
                    <td>
                        <input type="checkbox" class="task-checkbox"
                               onchange="app.toggleTaskSelection('${task.task_id}', this.checked)">
                    </td>
                    <td>
                        <div class="task-file-info">
                            <div class="task-filename">${task.filename || task.file_name || task.task_id}</div>
                            <div class="task-filepath">${task.file_path || ''}</div>
                        </div>
                    </td>
                    <td>
                        <div class="task-sheets">
                            <div>${task.sheets_selected || 0}/${task.sheets_total || 0}</div>
                            <div class="sheet-progress">已选择工作表</div>
                        </div>
                    </td>
                    <td>
                        <span class="strategy-badge strategy-${task.strategy || 'auto'}">${this.getStrategyText(task.strategy)}</span>
                    </td>
                    <td>
                        <div class="progress-container">
                            <div class="progress-bar">
                                <div class="progress-fill" style="width: ${task.progress || 0}%"></div>
                            </div>
                            <div class="progress-text">${progressText}</div>
                        </div>
                    </td>
                    <td>
                        <span class="status-badge status-${task.status}">${this.getStatusText(task.status)}</span>
                    </td>
                    <td>
                        <div class="time-info">
                            <div>${this.formatTime(task.created_at)}</div>
                            ${task.elapsed_time ? `<div>${Math.round(task.elapsed_time)}s</div>` : ''}
                        </div>
                    </td>
                    <td>
                        <div class="action-buttons">${actionButtons}</div>
                    </td>
                `;
            }"""

    # 替换createTaskRowHTML函数
    content = re.sub(create_row_pattern, unified_create_row, content, flags=re.DOTALL)

    # 添加辅助函数（如果不存在）
    if 'formatProgressText(task)' not in content:
        # 在getStatusText函数之前添加辅助函数
        status_text_pos = content.find('getStatusText(status) {')
        if status_text_pos != -1:
            helper_functions = """
            // 格式化进度文本 - 统一处理进度显示
            formatProgressText(task) {
                const rowText = `${task.processed_rows || 0}/${task.total_rows || 0}行`;
                const stepText = task.current_step || '';
                return `${rowText} ${stepText}`.trim();
            }

            // 生成操作按钮 - 统一处理按钮生成逻辑
            generateActionButtons(task) {
                const buttons = [];

                // 根据状态生成不同的操作按钮
                if (task.status === 'processing') {
                    buttons.push(`<button class="action-btn btn-warning" onclick="app.pauseTask('${task.task_id}')" title="暂停">
                        <i class="fas fa-pause"></i>
                    </button>`);
                }

                if (task.status === 'paused') {
                    buttons.push(`<button class="action-btn btn-primary" onclick="app.resumeTask('${task.task_id}')" title="继续">
                        <i class="fas fa-play"></i>
                    </button>`);
                }

                if (task.status === 'completed') {
                    buttons.push(`<button class="action-btn btn-success" onclick="app.downloadTask('${task.task_id}')" title="下载">
                        <i class="fas fa-download"></i>
                    </button>`);
                }

                if (task.status === 'failed') {
                    buttons.push(`<button class="action-btn btn-primary" onclick="app.retryTask('${task.task_id}')" title="重试">
                        <i class="fas fa-redo"></i>
                    </button>`);
                }

                // 查看详情按钮 - 所有状态都显示
                buttons.push(`<button class="action-btn btn-info" onclick="app.viewTaskDetails('${task.task_id}')" title="查看详情">
                    <i class="fas fa-eye"></i>
                </button>`);

                // 取消按钮 - 进行中的任务
                if (['pending', 'processing', 'paused'].includes(task.status)) {
                    buttons.push(`<button class="action-btn btn-danger" onclick="app.cancelTask('${task.task_id}')" title="取消">
                        <i class="fas fa-times"></i>
                    </button>`);
                }

                // 删除按钮 - 已完成的任务
                if (['completed', 'failed', 'cancelled'].includes(task.status)) {
                    buttons.push(`<button class="action-btn btn-danger" onclick="app.deleteTask('${task.task_id}')" title="删除">
                        <i class="fas fa-trash"></i>
                    </button>`);
                }

                return buttons.join('');
            }

            """
            content = content[:status_text_pos] + helper_functions + content[status_text_pos:]

    # 优化updateTaskProgress函数，使用formatProgressText
    update_progress_pattern = r'const progressStr = `\$\{task\.processed_rows \|\| 0\}/\$\{task\.total_rows \|\| 0\}行`;'
    content = re.sub(update_progress_pattern,
                     'const progressStr = this.formatProgressText(task);',
                     content)

    return content

def main():
    print("开始重构task_management.html...")

    # 执行重构
    refactored_content = refactor_html()

    # 写入重构后的文件
    output_path = '/mnt/d/work/trans_excel/excel_processor/frontend/task_management.html'
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(refactored_content)

    print(f"重构完成！文件已保存到: {output_path}")

    # 统计优化效果
    with open('/mnt/d/work/trans_excel/excel_processor/frontend/task_management.html.backup.20250916_080538', 'r', encoding='utf-8') as f:
        original_lines = len(f.readlines())

    refactored_lines = len(refactored_content.split('\n'))

    print(f"原始文件行数: {original_lines}")
    print(f"重构后行数: {refactored_lines}")
    print(f"减少了 {original_lines - refactored_lines} 行 ({(1 - refactored_lines/original_lines)*100:.1f}%)")

if __name__ == "__main__":
    main()