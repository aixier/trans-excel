# 🔧 修复"工作流已归档"问题

## 问题
导入工作流后提示: **"This workflow is archived so it cannot be activated"**

---

## ✅ 解决方案1: 在 n8n UI 中取消归档（最简单）

### 步骤：

1. **打开 n8n**: http://localhost:5678

2. **进入工作流列表**：
   - 点击左侧菜单 "Workflows"

3. **显示归档的工作流**：
   - 点击右上角的筛选图标（漏斗形状）
   - 勾选 "Archived" 或 "Show archived"

4. **取消归档**：
   - 找到 "Web Form Translation" 工作流
   - 点击工作流右侧的 "..." 三个点菜单
   - 选择 "Unarchive"（取消归档）

5. **激活工作流**：
   - 工作流会回到正常列表
   - 打开工作流
   - 点击右上角 "Inactive" 开关改为 "Active"
   - 点击 "Save"

---

## ✅ 解决方案2: 使用修复后的工作流文件

### 步骤：

1. **删除已导入的工作流**：
   - 在 n8n 工作流列表中
   - 找到 "Web Form Translation"
   - 删除它

2. **导入修复后的文件**：
   - 点击 "Add workflow"
   - 右上角 "..." → "Import from URL / File"
   - 选择文件：
     ```
     /mnt/d/work/trans_excel/translation_system_v2/integrations/n8n/workflows/08_web_form_translation_fixed.json
     ```

3. **激活工作流**：
   - 导入成功后
   - 点击 "Inactive" → "Active"
   - 点击 "Save"

---

## ✅ 解决方案3: 通过 n8n 设置取消归档

如果找不到 UI 选项，可以直接在工作流编辑器中：

1. 打开被归档的工作流
2. 点击右上角 "Settings"（齿轮图标）
3. 找到 "Archived" 选项
4. 取消勾选 "Archived"
5. 保存并激活工作流

---

## 📝 为什么会被归档？

n8n 的新版本可能有以下行为：
- 导入的工作流默认被标记为归档
- 某些元数据字段导致工作流被归档

修复后的文件移除了可能导致问题的元数据。

---

## 🎯 验证成功

取消归档并激活后，你应该能看到：

- ✅ 工作流状态显示为 "Active"（绿色）
- ✅ 可以点击 "Translation Form" 节点查看 Form URL
- ✅ Form URL 可以正常访问

---

**推荐使用解决方案1（最简单）！** 🚀
