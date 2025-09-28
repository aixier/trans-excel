# 设计文档：Excel处理模块

## 架构概述

Excel处理模块采用分层架构，以pandas DataFrame为核心数据结构，实现高效的Excel文件处理。

```
┌─────────────────────────────────────┐
│         API Layer (FastAPI)         │
│        /api/analyze/upload          │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│       Service Layer                 │
│  ┌─────────────────────────────┐   │
│  │     ExcelLoader             │   │
│  ├─────────────────────────────┤   │
│  │     ExcelAnalyzer           │   │
│  ├─────────────────────────────┤   │
│  │     ContextExtractor        │   │
│  └─────────────────────────────┘   │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│      Data Model Layer               │
│         ExcelDataFrame              │
│         TaskDataFrame               │
└─────────────────────────────────────┘
```

## 核心组件设计

### 1. ExcelLoader 服务

```python
class ExcelLoader:
    """Excel文件加载服务"""

    def __init__(self, config: LoaderConfig):
        self.max_file_size = config.max_file_size
        self.chunk_size = config.chunk_size

    async def load_excel(
        self,
        file_path: str,
        options: Dict[str, Any]
    ) -> ExcelDataFrame:
        """
        加载Excel文件到DataFrame
        - 支持大文件分块读取
        - 自动检测编码
        - 多Sheet处理
        """
        pass
```

### 2. ExcelAnalyzer 服务

```python
class ExcelAnalyzer:
    """Excel内容分析服务"""

    def analyze(
        self,
        excel_df: ExcelDataFrame,
        game_info: Optional[GameInfo]
    ) -> AnalysisResult:
        """
        分析Excel内容
        - 统计文本单元格
        - 识别语言类型
        - 评估翻译工作量
        - 计算预期成本
        """
        pass
```

### 3. ContextExtractor 服务

```python
class ContextExtractor:
    """上下文提取服务"""

    def extract_context(
        self,
        cell_position: CellPosition,
        excel_df: ExcelDataFrame,
        radius: int = 2
    ) -> Context:
        """
        提取单元格上下文
        - 相邻单元格内容
        - 列标题信息
        - Sheet名称
        - 游戏背景信息
        """
        pass
```

## 数据模型设计

### ExcelDataFrame Schema

```python
@dataclass
class ExcelDataFrame:
    """Excel数据框架模型"""

    # 元数据
    file_id: str           # 文件唯一标识
    file_name: str         # 文件名
    file_size: int         # 文件大小(bytes)

    # Sheet数据
    sheets: Dict[str, pd.DataFrame]  # Sheet名->数据

    # 样式信息
    styles: Dict[str, CellStyle]     # 单元格样式

    # 统计信息
    total_cells: int       # 总单元格数
    text_cells: int        # 文本单元格数
    formula_cells: int     # 公式单元格数

    # 处理信息
    created_at: datetime
    processing_time_ms: int
```

### CellPosition 模型

```python
@dataclass
class CellPosition:
    """单元格位置"""
    sheet_name: str
    row_idx: int
    col_idx: int
    cell_ref: str  # 如 "A1"
```

## 接口设计

### REST API

```yaml
POST /api/analyze/upload:
  description: 上传并分析Excel文件
  request:
    content-type: multipart/form-data
    body:
      file: binary
      game_info: json (optional)
  response:
    200:
      body:
        session_id: string
        analysis: object
        status: string
    400:
      body:
        error: string
```

## 处理流程

### 文件上传流程

```
Client                API              Service           Storage
  │                    │                 │                 │
  ├──Upload File──────▶│                 │                 │
  │                    ├──Validate──────▶│                 │
  │                    │                 ├──Save Temp─────▶│
  │                    │                 │◀──File Path─────┤
  │                    │                 ├──Load Excel     │
  │                    │                 ├──Analyze        │
  │                    │◀──Analysis──────┤                 │
  │◀──Response─────────┤                 │                 │
```

## 性能优化策略

### 1. 分块读取
```python
def read_large_excel(file_path: str, chunk_size: int = 10000):
    """分块读取大文件"""
    for chunk in pd.read_excel(file_path, chunksize=chunk_size):
        yield process_chunk(chunk)
```

### 2. 内存优化
```python
# 使用category类型减少内存
df['cell_type'] = df['cell_type'].astype('category')

# 及时释放不需要的对象
del temporary_data
gc.collect()
```

### 3. 并发处理
```python
async def process_sheets_concurrently(sheets: List[Sheet]):
    """并发处理多个Sheet"""
    tasks = [process_sheet(sheet) for sheet in sheets]
    return await asyncio.gather(*tasks)
```

## 错误处理

### 错误类型
- `FileFormatError`: 文件格式不支持
- `FileSizeError`: 文件过大
- `ProcessingError`: 处理失败
- `MemoryError`: 内存不足

### 重试机制
```python
@retry(max_attempts=3, backoff=exponential)
async def process_with_retry(file_path: str):
    """带重试的处理"""
    return await process_file(file_path)
```

## 安全考虑

### 1. 文件验证
- 检查文件魔术字节
- 限制文件大小
- 沙箱环境处理

### 2. 资源限制
- 内存使用上限
- 处理时间超时
- 并发数量限制

## 测试策略

### 单元测试
- 文件加载测试
- 内容分析测试
- 上下文提取测试

### 集成测试
- 完整上传流程测试
- 大文件处理测试
- 并发处理测试

### 性能测试
- 不同大小文件测试
- 内存使用测试
- 响应时间测试

---
*文档版本*: 1.0.0
*创建日期*: 2025-01-29
*状态*: 待实现