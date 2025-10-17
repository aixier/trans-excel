# 修复 "source.on is not a function" 错误

## 错误信息

```
NodeApiError: source.on is not a function
at ExecuteContext.execute (...HttpRequestV3.node.ts:847:16)
```

**错误节点**: Upload & Split Tasks (n8n-nodes-base.httpRequest v4.1)

## 根本原因

在 **Process Form Data** Code 节点中，二进制数据传递方式不正确：

```javascript
// ❌ 错误的方式
return {
  json: {...},
  binary: {
    data: $input.item.binary.data  // 尝试访问不存在的 .data 属性
  }
};
```

**问题**:
- Form Trigger 将上传的文件存储在 `$input.item.binary['Excel 文件']` 中（key 是字段名）
- 不存在 `$input.item.binary.data` 这个路径
- 重新构造 binary 对象破坏了数据结构
- HTTP Request 节点无法正确处理这个格式的数据

## 解决方案

### 1. 修复 Process Form Data 节点

**修改前**:
```javascript
return {
  json: {
    target_langs: targetLangs,
    glossary_id: glossaryId,
    processor: processor,
    file_name: fileData.filename || 'uploaded_file.xlsx'
  },
  binary: {
    data: $input.item.binary.data  // ❌ 错误
  }
};
```

**修改后**:
```javascript
return {
  json: {
    target_langs: targetLangs,
    glossary_id: glossaryId,
    processor: processor,
    file_name: fileName
  },
  binary: $input.item.binary  // ✅ 直接传递整个 binary 对象
};
```

**关键改变**:
- 直接传递 `$input.item.binary`，保留原始数据结构
- n8n 会自动处理 binary 数据的传递

### 2. 修复 Upload & Split Tasks 节点

**修改前**:
```json
{
  "name": "file",
  "value": "={{ $binary.data }}"
}
```

**修改后** (最终方案):
```json
{
  "name": "file",
  "value": "={{ $binary['Excel 文件'] }}"
}
```

**原因**:
- `$binary` 是一个对象，格式：`{ "Excel 文件": <binary_data> }`
- `$binary.data` 不存在
- **推荐方式**: 使用具体的字段名 `$binary['Excel 文件']`
- 备选方式: `Object.values($binary)[0]` 获取第一个文件（不够明确）

## 验证修复

运行以下脚本验证更新：

```bash
cd /mnt/d/work/trans_excel/translation_system_v2/integrations/n8n/scripts
python3 << 'EOF'
import requests
from config import get_api_headers

headers = get_api_headers()
response = requests.get('http://localhost:5678/api/v1/workflows/1xQAR3UTNGrk0X6B', headers=headers)
workflow = response.json()

# 检查 Process Form Data 节点
code_nodes = [n for n in workflow['nodes'] if n['name'] == 'Process Form Data']
if code_nodes:
    code = code_nodes[0]['parameters']['jsCode']
    if 'binary: $input.item.binary' in code:
        print("✅ Process Form Data 节点已修复")
    else:
        print("❌ Process Form Data 节点未修复")

# 检查 Upload & Split Tasks 节点
http_nodes = [n for n in workflow['nodes'] if n['name'] == 'Upload & Split Tasks']
if http_nodes:
    params = http_nodes[0]['parameters']['bodyParameters']['parameters']
    file_param = [p for p in params if p['name'] == 'file'][0]
    if 'Object.values($binary)[0]' in file_param['value']:
        print("✅ Upload & Split Tasks 节点已修复")
    else:
        print("❌ Upload & Split Tasks 节点未修复")
EOF
```

## 测试步骤

### 1. 访问表单

```
http://localhost:5678/form/translation
```

### 2. 提交测试数据

- 上传 Excel 文件
- 选择目标语言（EN）
- 点击提交

### 3. 检查执行历史

```bash
python3 << 'EOF'
import requests
from config import get_api_headers

headers = get_api_headers()
response = requests.get(
    'http://localhost:5678/api/v1/executions',
    headers=headers,
    params={'workflowId': '1xQAR3UTNGrk0X6B', 'limit': 1}
)

latest = response.json()['data'][0]
print(f"最新执行状态: {latest['status']}")
print(f"执行时间: {latest['startedAt']}")

if latest['status'] == 'success':
    print("✅ 工作流执行成功！")
elif latest['status'] == 'error':
    print("❌ 工作流执行失败")
    print("需要查看 n8n UI 中的执行详情")
elif latest['status'] == 'running':
    print("⏳ 工作流正在运行...")
EOF
```

## n8n Binary 数据格式说明

### Form Trigger 的 Binary 输出

当用户上传文件时，Form Trigger 输出：

```javascript
{
  json: {
    "Excel 文件": {
      filename: "example.xlsx",
      ...
    },
    "目标语言": "EN",
    ...
  },
  binary: {
    "Excel 文件": {  // key 是表单字段名
      data: Buffer(...),
      mimeType: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
      fileName: "example.xlsx",
      fileSize: 12345
    }
  }
}
```

### Code 节点传递 Binary

**正确方式**:
```javascript
// 完整传递
return {
  json: {...},
  binary: $input.item.binary  // ✅
};

// 或者指定 key
return {
  json: {...},
  binary: {
    data: $input.item.binary['Excel 文件']  // ✅ 明确指定字段名
  }
};
```

**错误方式**:
```javascript
return {
  json: {...},
  binary: {
    data: $input.item.binary.data  // ❌ 路径不存在
  }
};
```

### HTTP Request 引用 Binary

```javascript
// 方式1（推荐）: 明确指定 key
"={{ $binary['Excel 文件'] }}"

// 方式2: 获取第一个文件（不够明确）
"={{ Object.values($binary)[0] }}"

// 方式3: 如果 Code 节点重命名为 'data'
"={{ $binary.data }}"
```

## 相关文档

- [n8n Binary Data 文档](https://docs.n8n.io/data/data-structure/#binary-data)
- [HTTP Request 节点文档](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.httprequest/)
- [Code 节点文档](https://docs.n8n.io/code/builtin/code-node/)

## 常见错误模式

### 错误 1: 假设 binary.data 存在

```javascript
// ❌ 错误
$input.item.binary.data

// ✅ 正确
Object.values($input.item.binary)[0]
```

### 错误 2: 重新构造 binary 对象

```javascript
// ❌ 错误 - 破坏数据结构
return {
  binary: {
    data: someBinaryData
  }
};

// ✅ 正确 - 保留原始结构
return {
  binary: $input.item.binary
};
```

### 错误 3: HTTP Request 引用错误

```json
// ❌ 错误
{
  "name": "file",
  "value": "={{ $binary.data }}"
}

// ✅ 正确
{
  "name": "file",
  "value": "={{ Object.values($binary)[0] }}"
}
```

## 最佳实践

1. **不要重新构造 binary 对象** - 直接传递即可
2. **使用 Object.values() 处理动态 key** - 适用于不确定字段名的情况
3. **明确指定 key 更安全** - 如果知道字段名，直接使用
4. **在 UI 中测试** - 使用 n8n 的执行测试功能验证数据流
5. **查看执行日志** - 出错时检查每个节点的输入输出

## 更新日志

- **2025-01-17 19:30**: 修复 `source.on is not a function` 错误（最终方案）
  - 更新 Process Form Data 节点：直接传递 binary 对象 `binary: $input.item.binary`
  - 更新 Upload & Split Tasks 节点：使用具体字段名 `$binary['Excel 文件']`
  - 工作流 ID: 1xQAR3UTNGrk0X6B
  - 工作流版本: v2

---

**状态**: ✅ 配置已修复
**验证**: 运行 `python3 scripts/verify_form.py` 检查配置
**下一步**:
1. 在 n8n UI 中保存工作流以注册 webhook
   - 访问: http://localhost:5678/workflow/1xQAR3UTNGrk0X6B
   - 点击 Save 按钮 (💾)
2. 再次运行 verify_form.py 确认 webhook 已注册
3. 测试表单提交
