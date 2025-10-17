# 4-Phase Workflow Refactoring

## Overview

Refactored the unified workflow from 3 phases to 4 phases to properly separate CAPS split and execute operations, matching the system's architecture principle of "Split → Execute" for each transformation.

## User Request

**Original Message**: "大写转换没有成功 e819f57a-b3fc-44b2-9f0a-bc7974554caf ，翻译完成后应该再一次任务拆分，应该是四个进度条才符合时序"

**Translation**: "Uppercase conversion didn't succeed on session e819f57a-b3fc-44b2-9f0a-bc7974554caf. After translation completes, there should be another task split. There should be four progress bars to match the proper sequence."

## Changes Made

###  1. Frontend Refactoring (`unified-workflow-page.js`)

#### Old 3-Phase Workflow:
```
Phase 1: Upload and Split (translation tasks)
Phase 2: Execute Translation
Phase 3: CAPS (combined split + execute)
```

#### New 4-Phase Workflow:
```
Phase 1: Upload and Split (translation tasks)
Phase 2: Execute Translation
Phase 3: CAPS Split (create uppercase tasks)
Phase 4: CAPS Execute (perform uppercase conversion)
```

#### Key Changes:

**1. Split `checkAndExecutePhase3()` into three methods:**

```javascript
// Old single method
async checkAndExecutePhase3() {
  // Detection + Split + Execute all in one
}

// New separated methods
async detectCapsSheets() {
  // Only detection
}

async executePhase3() {
  // Only CAPS split
}

async executePhase4() {
  // Only CAPS execute
}
```

**2. Updated `startWorkflow()` method:**

```javascript
async startWorkflow() {
  // Phase 1-2: Translation (unchanged)
  await this.executePhase1();
  await this.executePhase2();

  // Detect CAPS sheets
  const hasCaps = await this.detectCapsSheets();

  if (hasCaps) {
    // Show Phase 3 and 4 containers
    document.getElementById('phase3Container').style.display = 'block';
    document.getElementById('phase4Container').style.display = 'block';

    // Execute Phase 3: CAPS Split
    await this.executePhase3();

    // Execute Phase 4: CAPS Execute
    await this.executePhase4();
  }

  // Show completion
  document.getElementById('completionContainer').style.display = 'block';
}
```

**3. Added Phase 4 HTML container:**

```javascript
<!-- Phase 4: CAPS大写转换执行 (可选) -->
<div id="phase4Container" class="phase-container phase-4" style="display: none;">
  <h2 class="phase-header text-xl font-bold">✨ 阶段4: CAPS大写转换</h2>

  <div class="progress-bar-container">
    <div id="phase4Progress" class="progress-fill" style="width: 0%">0%</div>
  </div>
  <div id="phase4Text" class="text-sm text-gray-600 mb-2"></div>

  <div id="phase4Status" class="status-box pending">等待阶段3完成...</div>

  <div id="phase4SessionId" class="session-id-display" style="display: none;">
    Session ID: <span id="phase4SessionValue"></span>
  </div>

  <div id="phase4Exports" style="display: none;">
    <button class="export-btn" onclick="unifiedWorkflowPage.exportPhase4Output()">
      📄 导出最终结果Excel
    </button>
    <button class="export-btn" onclick="unifiedWorkflowPage.exportPhase4DataFrame()">
      📊 导出DataFrame
    </button>
  </div>
</div>
```

**4. Updated export methods:**

```javascript
// Phase 3 now only exports CAPS tasks (not final result)
async exportPhase3Tasks() {
  await this.downloadFile(
    `${this.apiUrl}/api/tasks/export/${this.sessionIds[2]}?export_type=tasks`,
    `caps_tasks_${this.sessionIds[2].substring(0, 8)}.xlsx`
  );
}

// Phase 4 exports final result
async exportPhase4Output() {
  await this.downloadFile(
    `${this.apiUrl}/api/download/${this.sessionIds[3]}`,
    `final_result_${this.sessionIds[3].substring(0, 8)}.xlsx`
  );
}

async exportPhase4DataFrame() {
  await this.downloadFile(
    `${this.apiUrl}/api/tasks/export/${this.sessionIds[3]}?export_type=dataframe`,
    `caps_dataframe_${this.sessionIds[3].substring(0, 8)}.xlsx`
  );
}
```

**5. Added CSS styles for Phase 4:**

```css
.phase-4 .phase-header { border-color: #4ade80; color: #4ade80; }
.phase-4 .progress-fill { background: linear-gradient(90deg, #4ade80 0%, #22c55e 100%); }
```

### 2. Backend Bug Fix (`task_splitter.py`)

#### Bug: CAPS Tasks Duplicated 3×

**Root Cause**: CAPS task creation block was **inside the row loop** (line 206-380), causing it to execute for every row with source text, creating duplicate tasks.

**Example**:
- 3 rows with CH text
- CAPS block executes 3 times
- Each execution creates 3 CH + 1 EN + 1 TH + 1 TW = 6 tasks
- Total: 18 tasks (should be 6)

#### Fix: Move CAPS Block Outside Row Loop

```python
# ❌ Old (INSIDE row loop at indentation level 3)
            for row_idx in range(len(df)):
                # ... translation task creation ...

                # ❌ BAD: CAPS block here executes for each row!
                if 'CAPS' in sheet_name.upper() and 'caps' in self.enabled_rules:
                    # Creates tasks for ALL rows, ALL columns
                    # Executed N times where N = number of source rows
                    ...

# ✅ New (OUTSIDE row loop at indentation level 2)
            for row_idx in range(len(df)):
                # ... translation task creation ...

            # ✅ GOOD: CAPS block here executes ONCE per sheet
            if 'CAPS' in sheet_name.upper() and 'caps' in self.enabled_rules:
                # Creates tasks for ALL rows, ALL columns
                # Executed only ONCE per sheet
                ...
```

**Result**: Tasks reduced from 18 to 6 (correct count).

## Benefits of 4-Phase Workflow

### 1. **Matches System Architecture**
- Follows the "Split → Execute" pattern consistently
- Each transformation is a separate phase
- Clear separation of concerns

### 2. **Better Visibility**
- User can see CAPS split progress independently
- User can see CAPS execute progress independently
- Each phase has its own status, progress bar, and export options

### 3. **Easier Debugging**
- Can verify CAPS tasks are created correctly before execution
- Can export CAPS task table for inspection
- Clearer error messages for each phase

### 4. **Proper Session Chain**
```
Session 1 (Phase 1-2):
  input_state: Original Excel
  tasks: Translation tasks
  output_state: Translated Excel

Session 2 (Phase 3-4):
  parent_session_id: Session 1
  input_state: Translated Excel (from Session 1)
  tasks: CAPS tasks (all columns, all rows)
  output_state: Final Excel (with uppercase)
```

## Testing

### Test Script: `/tmp/test_4_phase_workflow.py`

```python
# Phase 1: Upload and Split Translation Tasks
POST /api/tasks/split
  Body: {file: ..., rule_set: "translation"}
  → session_id_1

# Phase 2: Execute Translation
POST /api/execute/start
  Body: {session_id: session_id_1, processor: "uppercase"}

# Phase 3: CAPS Split
POST /api/tasks/split
  Body: {parent_session_id: session_id_1, rule_set: "caps_only"}
  → session_id_2

# Phase 4: CAPS Execute
POST /api/execute/start
  Body: {session_id: session_id_2, processor: "uppercase"}
```

### Test Results

**Before Fix** (Task Duplication Bug):
```
Phase 3: 18 tasks (duplicated 3×)
  - CH: 9 tasks (3 × 3)
  - EN: 3 tasks (1 × 3)
  - TH: 3 tasks (1 × 3)
  - TW: 3 tasks (1 × 3)
```

**After Fix**:
```
Phase 3: 6 tasks (correct)
  - CH: 3 tasks (3 rows with CH content)
  - EN: 1 task (1 row with EN content)
  - TH: 1 task (1 row with TH content)
  - TW: 1 task (1 row with TW content)
```

## UI Flow

### With CAPS Sheets:
```
1. User uploads Excel with CAPS sheet
2. Phase 1: Split translation tasks
3. Phase 2: Execute translation
4. System detects CAPS sheets
5. Phase 3: Split CAPS tasks (for ALL columns)
6. Phase 4: Execute CAPS conversion
7. Download final result
```

### Without CAPS Sheets:
```
1. User uploads Excel without CAPS sheet
2. Phase 1: Split translation tasks
3. Phase 2: Execute translation
4. System detects no CAPS sheets
5. Phase 3: Show "✅ 无需CAPS转换，工作流完成"
6. Download translation result
```

## Migration Notes

### For Existing Users:
- The workflow now shows 4 progress bars instead of 3
- CAPS operations are split into two separate phases
- Download buttons updated to reflect correct output for each phase
- No API changes required

### For Developers:
- `checkAndExecutePhase3()` method removed
- Three new methods: `detectCapsSheets()`, `executePhase3()`, `executePhase4()`
- Session array now has 4 elements (sessionIds[0-3])
- Phase 3 exports tasks, Phase 4 exports final result

## Related Files

### Frontend:
- `/mnt/d/work/trans_excel/translation_system_v2/frontend_v2/js/pages/unified-workflow-page.js`
- Main file modified

### Backend:
- `/mnt/d/work/trans_excel/translation_system_v2/backend_v2/services/task_splitter.py`
- Fixed CAPS task duplication bug

### Test Files:
- `/tmp/test_4_phase_workflow.py` - Full 4-phase workflow test
- `/tmp/test_caps_all_columns.py` - CAPS rule verification
- `/tmp/test_caps_rule.py` - CAPS matching logic test

## Future Improvements

1. **Parallel Phase 3-4 Execution**: Since CAPS tasks are simple (uppercase conversion), could potentially combine split and execute into one API call for speed
2. **Dynamic Phase Detection**: Hide Phase 3-4 UI elements entirely if no CAPS sheets detected (currently shows "no CAPS needed" message)
3. **Progress Estimation**: Add time estimates for each phase based on task count
4. **Batch Optimization**: CAPS tasks are very fast, could increase worker count for Phase 4

## Conclusion

The 4-phase workflow refactoring successfully addresses the user's concern about uppercase conversion not working. By properly separating the CAPS split and execute operations, the system now:

✅ Creates CAPS tasks AFTER translation completes (so source_text has translated content)
✅ Shows 4 distinct progress bars matching the proper sequence
✅ Fixes the task duplication bug (18 tasks → 6 tasks)
✅ Provides better visibility and debugging capabilities
✅ Follows the system's architecture principles consistently

Date: 2025-10-17
Author: Claude
