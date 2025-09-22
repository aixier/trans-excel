"""
术语表管理路由
"""
from typing import List, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update, or_
from pydantic import BaseModel
from datetime import datetime
import json
import uuid
import io
import pandas as pd

from database.connection import get_db
from database.models import Terminology

router = APIRouter(tags=["terminology"])


class TerminologyItem(BaseModel):
    """术语项"""
    id: Optional[str] = None
    source: str
    target_translations: Dict[str, str]  # {"pt": "Portuguese", "es": "Spanish", ...}
    category: Optional[str] = None
    context: Optional[str] = None
    case_sensitive: Optional[bool] = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class TerminologyCreateRequest(BaseModel):
    """创建术语请求"""
    source: str
    target_translations: Dict[str, str]
    category: Optional[str] = "general"
    context: Optional[str] = None
    case_sensitive: Optional[bool] = False
    project_id: Optional[str] = None


class TerminologyUpdateRequest(BaseModel):
    """更新术语请求"""
    source: Optional[str] = None
    target_translations: Optional[Dict[str, str]] = None
    category: Optional[str] = None
    context: Optional[str] = None
    case_sensitive: Optional[bool] = None


class TerminologyBatchImportResponse(BaseModel):
    """批量导入响应"""
    total: int
    success: int
    failed: int
    errors: List[str]


@router.get("/list", response_model=List[TerminologyItem])
async def list_terminology(
    project_id: Optional[str] = None,
    category: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """获取术语列表"""
    query = select(Terminology)

    # 添加过滤条件
    if project_id:
        query = query.where(Terminology.project_id == project_id)
    if category:
        query = query.where(Terminology.category == category)
    if search:
        query = query.where(
            or_(
                Terminology.source.contains(search),
                Terminology.context.contains(search)
            )
        )

    # 排序和分页
    query = query.order_by(Terminology.created_at.desc())
    query = query.limit(limit).offset(offset)

    result = await db.execute(query)
    terms = result.scalars().all()

    return [
        TerminologyItem(
            id=term.id,
            source=term.source,
            target_translations=term.target_translations or {},
            category=term.category,
            context=term.context,
            case_sensitive=term.case_sensitive,
            created_at=term.created_at,
            updated_at=term.updated_at
        )
        for term in terms
    ]


@router.get("/categories")
async def get_categories(
    db: AsyncSession = Depends(get_db)
):
    """获取所有术语分类"""
    result = await db.execute(
        select(Terminology.category).distinct().where(Terminology.category.isnot(None))
    )
    categories = [row[0] for row in result.fetchall()]

    return {"categories": categories}


@router.get("/{term_id}", response_model=TerminologyItem)
async def get_terminology(
    term_id: str,
    db: AsyncSession = Depends(get_db)
):
    """获取单个术语"""
    result = await db.execute(
        select(Terminology).where(Terminology.id == term_id)
    )
    term = result.scalar_one_or_none()

    if not term:
        raise HTTPException(status_code=404, detail="Terminology not found")

    return TerminologyItem(
        id=term.id,
        source=term.source,
        target_translations=term.target_translations or {},
        category=term.category,
        context=term.context,
        case_sensitive=term.case_sensitive,
        created_at=term.created_at,
        updated_at=term.updated_at
    )


@router.post("/create", response_model=TerminologyItem)
async def create_terminology(
    request: TerminologyCreateRequest,
    db: AsyncSession = Depends(get_db)
):
    """创建术语"""
    term = Terminology(
        id=str(uuid.uuid4()),
        project_id=request.project_id or "default",  # 使用默认项目ID
        source=request.source,
        target_translations=request.target_translations,
        category=request.category,
        context=request.context,
        case_sensitive=request.case_sensitive,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    db.add(term)
    await db.commit()
    await db.refresh(term)

    return TerminologyItem(
        id=term.id,
        source=term.source,
        target_translations=term.target_translations,
        category=term.category,
        context=term.context,
        case_sensitive=term.case_sensitive,
        created_at=term.created_at,
        updated_at=term.updated_at
    )


@router.put("/{term_id}", response_model=TerminologyItem)
async def update_terminology(
    term_id: str,
    request: TerminologyUpdateRequest,
    db: AsyncSession = Depends(get_db)
):
    """更新术语"""
    result = await db.execute(
        select(Terminology).where(Terminology.id == term_id)
    )
    term = result.scalar_one_or_none()

    if not term:
        raise HTTPException(status_code=404, detail="Terminology not found")

    # 更新字段
    if request.source is not None:
        term.source = request.source
    if request.target_translations is not None:
        term.target_translations = request.target_translations
    if request.category is not None:
        term.category = request.category
    if request.context is not None:
        term.context = request.context
    if request.case_sensitive is not None:
        term.case_sensitive = request.case_sensitive

    term.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(term)

    return TerminologyItem(
        id=term.id,
        source=term.source,
        target_translations=term.target_translations,
        category=term.category,
        context=term.context,
        case_sensitive=term.case_sensitive,
        created_at=term.created_at,
        updated_at=term.updated_at
    )


@router.delete("/{term_id}")
async def delete_terminology(
    term_id: str,
    db: AsyncSession = Depends(get_db)
):
    """删除术语"""
    result = await db.execute(
        select(Terminology).where(Terminology.id == term_id)
    )
    term = result.scalar_one_or_none()

    if not term:
        raise HTTPException(status_code=404, detail="Terminology not found")

    await db.delete(term)
    await db.commit()

    return {"message": "Terminology deleted successfully"}


@router.post("/batch-delete")
async def batch_delete_terminology(
    term_ids: List[str],
    db: AsyncSession = Depends(get_db)
):
    """批量删除术语"""
    result = await db.execute(
        delete(Terminology).where(Terminology.id.in_(term_ids))
    )
    await db.commit()

    return {"message": f"Deleted {result.rowcount} terms"}


@router.post("/import/json", response_model=TerminologyBatchImportResponse)
async def import_json_terminology(
    file: UploadFile = File(...),
    project_id: Optional[str] = Form(None),
    category: Optional[str] = Form("imported"),
    db: AsyncSession = Depends(get_db)
):
    """导入JSON格式术语表"""
    if not file.filename.endswith('.json'):
        raise HTTPException(status_code=400, detail="File must be JSON format")

    content = await file.read()

    try:
        data = json.loads(content)
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON format: {str(e)}")

    total = len(data)
    success = 0
    failed = 0
    errors = []

    for source, target in data.items():
        try:
            # 处理目标翻译
            if isinstance(target, str):
                # 如果是字符串，默认为英文翻译
                target_translations = {"en": target}
            elif isinstance(target, dict):
                target_translations = target
            else:
                raise ValueError(f"Invalid target format for '{source}'")

            # 检查是否已存在
            existing = await db.execute(
                select(Terminology).where(
                    Terminology.source == source,
                    Terminology.project_id == project_id
                )
            )
            existing_term = existing.scalar_one_or_none()

            if existing_term:
                # 更新现有术语
                existing_term.target_translations = target_translations
                existing_term.updated_at = datetime.utcnow()
            else:
                # 创建新术语
                term = Terminology(
                    id=str(uuid.uuid4()),
                    project_id=project_id or "default",  # 使用默认项目ID
                    source=source,
                    target_translations=target_translations,
                    category=category,
                    case_sensitive=False,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                db.add(term)

            success += 1

        except Exception as e:
            failed += 1
            errors.append(f"Failed to import '{source}': {str(e)}")

    await db.commit()

    return TerminologyBatchImportResponse(
        total=total,
        success=success,
        failed=failed,
        errors=errors
    )


@router.post("/import/excel", response_model=TerminologyBatchImportResponse)
async def import_excel_terminology(
    file: UploadFile = File(...),
    project_id: Optional[str] = Form(None),
    category: Optional[str] = Form("imported"),
    db: AsyncSession = Depends(get_db)
):
    """导入Excel格式术语表

    Excel格式要求：
    - 第一列：源语言术语
    - 后续列：各目标语言翻译（列标题为语言代码，如pt, es, en等）
    """
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="File must be Excel format")

    content = await file.read()

    try:
        # 读取Excel文件
        df = pd.read_excel(io.BytesIO(content))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read Excel file: {str(e)}")

    if df.empty:
        raise HTTPException(status_code=400, detail="Excel file is empty")

    # 获取列名
    columns = df.columns.tolist()
    if len(columns) < 2:
        raise HTTPException(status_code=400, detail="Excel must have at least 2 columns (source and target)")

    source_col = columns[0]
    target_cols = columns[1:]

    total = len(df)
    success = 0
    failed = 0
    errors = []

    for index, row in df.iterrows():
        try:
            source = str(row[source_col]).strip()
            if not source or source == 'nan':
                continue

            # 构建目标翻译字典
            target_translations = {}
            for col in target_cols:
                value = row[col]
                if pd.notna(value) and str(value).strip():
                    # 尝试从列名推断语言代码
                    lang_code = col.lower()[:2] if len(col) >= 2 else 'en'
                    target_translations[lang_code] = str(value).strip()

            if not target_translations:
                errors.append(f"Row {index + 2}: No target translations found for '{source}'")
                failed += 1
                continue

            # 检查是否已存在
            existing = await db.execute(
                select(Terminology).where(
                    Terminology.source == source,
                    Terminology.project_id == project_id
                )
            )
            existing_term = existing.scalar_one_or_none()

            if existing_term:
                # 更新现有术语
                existing_term.target_translations = target_translations
                existing_term.updated_at = datetime.utcnow()
            else:
                # 创建新术语
                term = Terminology(
                    id=str(uuid.uuid4()),
                    project_id=project_id or "default",  # 使用默认项目ID
                    source=source,
                    target_translations=target_translations,
                    category=category,
                    case_sensitive=False,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                db.add(term)

            success += 1

        except Exception as e:
            failed += 1
            errors.append(f"Row {index + 2}: {str(e)}")

    await db.commit()

    return TerminologyBatchImportResponse(
        total=total,
        success=success,
        failed=failed,
        errors=errors[:10]  # 限制错误信息数量
    )


@router.get("/export/json")
async def export_json_terminology(
    project_id: Optional[str] = None,
    category: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """导出术语表为JSON格式"""
    query = select(Terminology)

    if project_id:
        query = query.where(Terminology.project_id == project_id)
    if category:
        query = query.where(Terminology.category == category)

    query = query.order_by(Terminology.source)

    result = await db.execute(query)
    terms = result.scalars().all()

    # 构建导出数据
    export_data = {}
    for term in terms:
        # 如果只有一个目标语言，直接使用字符串
        if term.target_translations and len(term.target_translations) == 1:
            export_data[term.source] = list(term.target_translations.values())[0]
        else:
            export_data[term.source] = term.target_translations or {}

    return export_data


