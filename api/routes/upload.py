"""
文件上传 API
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import shutil
import zipfile
from pathlib import Path
import uuid
import json
import asyncio
import logging

from ..core.database import get_db, async_session_maker
from ..core.config import settings
from ..core.deps import get_current_active_user, get_current_workspace
from ..core.task_manager import task_manager, TaskStatus
from ..models.user import User
from ..models.workspace import Workspace
from ..models.paper import Paper
from ..models.theme import Theme
from ..schemas.paper import UploadResponse

from ..core.pdf_extractor import extract_pdf_text
from ..core.llm_client import async_call_llm, init_async_client, clean_json_response
from ..core.credit_service import check_credits, deduct_credits
from ..core.config import load_scenario_weights
from ..models.credit import CreditType
from shared.scoring import compute_weighted_score

logger = logging.getLogger(__name__)

# ── 场景评分计算 ──


def _compute_scenario_scores(scores: dict) -> dict | None:
    """根据五维分数和场景权重计算各场景加权评分"""
    cfg = load_scenario_weights()
    scenarios = cfg.get("scenarios", {})
    if not scenarios:
        return None

    rigor = scores.get("rigor") or 0
    innovation = scores.get("innovation") or 0
    practicality = scores.get("practicality") or 0
    impact = scores.get("impact") or 0
    readability = scores.get("readability") or 0

    result = {}
    for name, sc in scenarios.items():
        w = sc.get("weights", {})
        result[name] = compute_weighted_score(rigor, innovation, practicality, impact, readability, w)
    return result if result else None

router = APIRouter(prefix="/upload", tags=["文件上传"])


def _build_paper_model(paper_data: dict, user_id: int, workspace_id: int, theme_id: int, theme_name: str, filename: str, file_path: Path) -> Paper:
    """根据 LLM 解析结果构建 Paper ORM 对象（共用逻辑，消除重复）"""
    title = _to_text(paper_data.get("title")) or filename
    authors = _to_text(paper_data.get("authors"))
    if isinstance(paper_data.get("authors"), list):
        authors = _to_csv(paper_data.get("authors"))

    return Paper(
        user_id=user_id,
        workspace_id=workspace_id,
        theme_id=theme_id,
        theme_name=theme_name,
        title=title,
        authors=authors,
        year=_to_int(paper_data.get("year")),
        venue=_to_text(paper_data.get("venue")),
        keywords=_to_csv(paper_data.get("keywords")),
        domain_tags=_to_csv(paper_data.get("domain_tags")),
        paper_type=_to_text(paper_data.get("paper_type")),
        problem=_to_text(paper_data.get("problem")),
        methodology=_to_text(paper_data.get("methodology")),
        conclusion=_to_text(paper_data.get("conclusion")),
        contribution=_to_text(paper_data.get("contribution")),
        implementation_path=_format_implementation_path(paper_data.get("implementation_path")),
        score_rigor=paper_data.get("scores", {}).get("rigor"),
        score_innovation=paper_data.get("scores", {}).get("innovation"),
        score_practicality=paper_data.get("scores", {}).get("practicality"),
        score_impact=paper_data.get("scores", {}).get("impact"),
        score_readability=paper_data.get("scores", {}).get("readability"),
        overall_score=paper_data.get("scores", {}).get("overall"),
        scenario_scores=_compute_scenario_scores(paper_data.get("scores", {})),
        file_path=str(file_path),
        original_filename=filename
    )


async def _process_pdf_background_async(task_id: str, file_path: Path, user_id: int, workspace_id: int, theme_id: int, theme_name: str, filename: str):
    """后台异步处理 PDF（在 asyncio 事件循环中运行，无需线程池）"""
    try:
        task_manager.update_task(task_id, progress=10, current_step="正在提取PDF文本...")
        task_manager.update_task(task_id, progress=20, current_step="正在AI分析论文内容...")
        task_manager.update_task(task_id, progress=30, current_step="AI分析中（预计1-2分钟）...")

        paper_data = await _async_extract_and_analyze_pdf(file_path)

        task_manager.update_task(task_id, progress=80, current_step="正在保存分析结果...")

        async with async_session_maker() as session:
            paper = _build_paper_model(paper_data, user_id, workspace_id, theme_id, theme_name, filename, file_path)
            session.add(paper)
            await session.commit()
            await session.refresh(paper)
            paper_id = paper.id
        
        task_manager.update_task(task_id, progress=100, current_step="完成")
        logger.info(f"论文保存成功，ID: {paper_id}")
        
        return {"paper_id": paper_id, "title": paper_data.get("title", filename)}
        
    except Exception as e:
        logger.error(f"后台处理失败: {e}", exc_info=True)
        raise


def _to_text(value) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        parts: list[str] = []
        for idx, item in enumerate(value, 1):
            if item is None:
                continue
            if isinstance(item, str):
                s = item.strip()
                if s:
                    # 添加编号格式: "1. xxx 2. xxx"
                    parts.append(f"{idx}. {s}")
                continue
            parts.append(f"{idx}. {json.dumps(item, ensure_ascii=False)}")
        return " ".join(parts) if parts else None
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def _format_implementation_path(value) -> str | None:
    """专门处理implementation_path字段，将嵌套结构转为可读文本"""
    if value is None:
        return None
    if isinstance(value, str):
        # 尝试解析JSON字符串
        try:
            value = json.loads(value)
        except (json.JSONDecodeError, ValueError, TypeError):
            return value
    
    if not isinstance(value, dict):
        return str(value)
    
    # 格式化嵌套结构: {"维度名": {"description": "...", "keywords": [...]}}
    parts = []
    for idx, (dimension, content) in enumerate(value.items(), 1):
        if isinstance(content, dict):
            desc = content.get("description", "")
            keywords = content.get("keywords", [])
            if isinstance(keywords, list):
                keywords_str = "、".join(keywords)
            else:
                keywords_str = str(keywords)
            
            # 格式: "1. 维度名 → 描述 [关键词]"
            if keywords_str:
                parts.append(f"{idx}. {dimension} → {desc} [{keywords_str}]")
            else:
                parts.append(f"{idx}. {dimension} → {desc}")
        else:
            parts.append(f"{idx}. {dimension}: {content}")
    
    return " ".join(parts) if parts else None


def _to_csv(value) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        parts = [str(x).strip() for x in value if x is not None and str(x).strip()]
        return ", ".join(parts) if parts else None
    return str(value)


def _to_int(value) -> int | None:
    if value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        s = value.strip()
        if not s:
            return None
        try:
            return int(s)
        except ValueError:
            return None
    try:
        return int(value)
    except Exception:
        return None


def _validate_pdf_magic_bytes(file_path: Path) -> bool:
    """校验文件的 magic bytes 是否为 PDF 格式"""
    try:
        with open(file_path, 'rb') as f:
            header = f.read(5)
        return header == b'%PDF-'
    except Exception:
        return False


async def save_upload_file(upload_file: UploadFile, user_id: int) -> Path:
    """保存上传的文件，同时校验文件大小"""
    # 创建用户专属目录
    user_dir = settings.UPLOAD_DIR / f"user_{user_id}"
    user_dir.mkdir(parents=True, exist_ok=True)
    
    # 生成唯一文件名
    file_ext = Path(upload_file.filename).suffix
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = user_dir / unique_filename
    
    # 保存文件并检查大小
    total_size = 0
    with file_path.open("wb") as buffer:
        while chunk := await upload_file.read(8192):
            total_size += len(chunk)
            if total_size > settings.MAX_UPLOAD_SIZE:
                file_path.unlink(missing_ok=True)
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"文件大小超过限制 ({settings.MAX_UPLOAD_SIZE // (1024*1024)}MB)"
                )
            buffer.write(chunk)
    
    return file_path


async def extract_zip(zip_path: Path, user_id: int) -> List[Path]:
    """解压 ZIP 文件并返回 PDF 文件列表（含路径穿越防护和大小限制）"""
    extract_dir = settings.UPLOAD_DIR / f"user_{user_id}" / f"extracted_{uuid.uuid4()}"
    extract_dir.mkdir(parents=True, exist_ok=True)
    
    pdf_files = []
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        # 检查解压后总大小，防止 ZIP 炸弹
        total_uncompressed = sum(info.file_size for info in zip_ref.infolist())
        if total_uncompressed > settings.MAX_UPLOAD_SIZE * 5:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"ZIP 解压后总大小超过限制 ({settings.MAX_UPLOAD_SIZE * 5 // (1024*1024)}MB)"
            )
        
        for info in zip_ref.infolist():
            # 路径穿越防护：检查文件名是否包含 .. 或绝对路径
            if '..' in info.filename or info.filename.startswith('/'):
                logger.warning(f"ZIP 路径穿越尝试: {info.filename}")
                continue
            
            target_path = extract_dir / info.filename
            # 二次校验：确保解压目标在 extract_dir 内
            try:
                target_path.resolve().relative_to(extract_dir.resolve())
            except ValueError:
                logger.warning(f"ZIP 路径穿越尝试(resolve): {info.filename}")
                continue
            
            zip_ref.extract(info, extract_dir)
        
        # 递归查找所有 PDF 文件
        for pdf_file in extract_dir.rglob("*.pdf"):
            pdf_files.append(pdf_file)
    
    return pdf_files


async def _async_extract_and_analyze_pdf(file_path: Path) -> dict:
    """纯异步：提取 PDF 并调用 LLM 分析（无线程池，直接 await）"""
    # 1. 提取 PDF 文本（CPU 密集操作，放到线程避免阻塞事件循环）
    logger.info(f"开始提取 PDF: {file_path}")
    pdf_text = await asyncio.to_thread(extract_pdf_text, file_path)
    logger.info(f"PDF 提取完成，文本长度: {len(pdf_text)}")
    
    # 2. 读取 Prompt 模板
    with open(settings.PROMPT_FILE, 'r', encoding='utf-8') as f:
        prompt_template = f.read()
    
    full_prompt = f"{prompt_template}\n\n论文内容：\n{pdf_text}"
    
    # 3. 异步调用 LLM（I/O 密集，直接 await，不阻塞事件循环）
    logger.info("开始调用 LLM API（异步）...")
    response = await async_call_llm(full_prompt)
    logger.info("LLM API 调用完成")
    clean_response = clean_json_response(response)
    
    # 4. 解析 JSON
    paper_data = json.loads(clean_response)
    logger.info(f"解析完成，标题: {paper_data.get('title', 'N/A')}")
    return paper_data


async def process_pdf_async(file_path: Path, user_id: int, workspace_id: int, theme_id: int, theme_name: str, filename: str, db: AsyncSession) -> int:
    """异步处理 PDF 文件（纯 async，无线程池）"""
    try:
        paper_data = await _async_extract_and_analyze_pdf(file_path)
    except Exception as e:
        logger.error(f"PDF 处理失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"PDF 处理失败: {str(e)}")
    
    try:
        paper = _build_paper_model(paper_data, user_id, workspace_id, theme_id, theme_name, filename, file_path)
        db.add(paper)
        await db.commit()
        await db.refresh(paper)
        logger.info(f"论文保存成功，ID: {paper.id}")
        return paper.id
    except Exception as e:
        logger.error(f"数据库保存失败: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"数据库保存失败: {str(e)}")


@router.post("/pdf/async")
async def upload_pdf_async(
    theme_id: int = Form(..., description="主题ID（必填）"),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    workspace: Workspace = Depends(get_current_workspace),
):
    """上传单个 PDF 文件（异步模式）- 立即返回task_id，后台处理"""
    # 积分检查
    await check_credits(current_user, CreditType.PAPER_EXTRACT)
    
    # 验证主题
    result = await db.execute(
        select(Theme).where(Theme.id == theme_id, Theme.user_id == current_user.id)
    )
    theme = result.scalar_one_or_none()
    if not theme:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="主题不存在或无权访问")
    
    # 验证文件类型
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="只支持 PDF 文件")
    
    # 保存文件
    file_path = await save_upload_file(file, current_user.id)
    
    # 校验 PDF magic bytes
    if not _validate_pdf_magic_bytes(file_path):
        file_path.unlink(missing_ok=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="文件内容不是有效的 PDF 格式")
    
    # 扣减积分（提前扣减，防止并发超额提交）
    await deduct_credits(db, current_user, CreditType.PAPER_EXTRACT, f"上传论文: {file.filename}")
    await db.commit()
    
    # 创建后台任务（纯异步，无线程池）
    task_id = task_manager.create_task()
    task_manager.submit_async_task(
        task_id,
        _process_pdf_background_async,
        file_path, current_user.id, workspace.id, theme_id, theme.name, file.filename
    )
    
    # 立即返回
    return {
        "task_id": task_id,
        "filename": file.filename,
        "status": "processing",
        "message": "文件已提交，正在后台处理",
        "credits_used": 1,
        "credits_remaining": current_user.credits,
    }


@router.get("/task/{task_id}")
async def get_task_status(
    task_id: str,
    current_user: User = Depends(get_current_active_user),
):
    """查询任务状态"""
    task = task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    return {
        "task_id": task.task_id,
        "status": task.status.value,
        "progress": task.progress,
        "current_step": task.current_step,
        "result": task.result,
        "error": task.error
    }


@router.post("/pdf", response_model=UploadResponse)
async def upload_pdf(
    theme_id: int = Form(..., description="主题ID（必填）"),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    workspace: Workspace = Depends(get_current_workspace),
):
    """上传单个 PDF 文件（必须指定主题）- 同步处理模式（兼容旧接口）"""
    # 积分检查
    await check_credits(current_user, CreditType.PAPER_EXTRACT)
    
    # 验证主题是否存在且属于当前用户
    result = await db.execute(
        select(Theme).where(
            Theme.id == theme_id,
            Theme.user_id == current_user.id
        )
    )
    theme = result.scalar_one_or_none()
    if not theme:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="主题不存在或无权访问"
        )
    
    # 验证文件类型
    if not file.filename.endswith('.pdf'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只支持 PDF 文件"
        )
    
    # 保存文件
    file_path = await save_upload_file(file, current_user.id)
    
    # 校验 PDF magic bytes
    if not _validate_pdf_magic_bytes(file_path):
        file_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="文件内容不是有效的 PDF 格式"
        )
    
    # 扣减积分
    await deduct_credits(db, current_user, CreditType.PAPER_EXTRACT, f"上传论文: {file.filename}")
    await db.commit()
    
    try:
        # 异步处理 PDF（阻塞操作在线程池中运行）
        paper_id = await process_pdf_async(
            file_path=file_path,
            user_id=current_user.id,
            workspace_id=workspace.id,
            theme_id=theme_id,
            theme_name=theme.name,
            filename=file.filename,
            db=db
        )
        
        return UploadResponse(
            filename=file.filename,
            file_path=str(file_path),
            file_size=file_path.stat().st_size,
            task_id=str(paper_id)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"上传处理异常: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"处理失败: {str(e)}"
        )


@router.post("/pdfs", response_model=List[UploadResponse])
async def upload_multiple_pdfs(
    theme_id: int = Form(..., description="主题ID（必填）"),
    files: List[UploadFile] = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    workspace: Workspace = Depends(get_current_workspace),
):
    """批量上传 PDF 文件（必须指定主题）"""
    # 验证主题是否存在且属于当前用户
    result = await db.execute(
        select(Theme).where(
            Theme.id == theme_id,
            Theme.user_id == current_user.id
        )
    )
    theme = result.scalar_one_or_none()
    if not theme:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="主题不存在或无权访问"
        )
    
    responses = []
    
    for file in files:
        # 验证文件类型
        if not file.filename.endswith('.pdf'):
            continue
        
        # 积分检查与扣减（每篇扣减）
        await check_credits(current_user, CreditType.PAPER_EXTRACT)
        await deduct_credits(db, current_user, CreditType.PAPER_EXTRACT, f"上传论文: {file.filename}")
        await db.commit()
        
        # 保存文件
        file_path = await save_upload_file(file, current_user.id)
        
        try:
            # 异步处理 PDF
            paper_id = await process_pdf_async(
                file_path=file_path,
                user_id=current_user.id,
                workspace_id=workspace.id,
                theme_id=theme_id,
                theme_name=theme.name,
                filename=file.filename,
                db=db
            )
            
            responses.append(UploadResponse(
                filename=file.filename,
                file_path=str(file_path),
                file_size=file_path.stat().st_size,
                task_id=str(paper_id)
            ))
        except Exception as e:
            logger.error(f"批量上传单文件失败 {file.filename}: {e}")
            continue
    
    return responses


@router.post("/zip", response_model=List[UploadResponse])
async def upload_zip(
    theme_id: int = Form(..., description="主题ID（必填）"),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    workspace: Workspace = Depends(get_current_workspace),
):
    """上传 ZIP 压缩包（必须指定主题）"""
    # 验证主题是否存在且属于当前用户
    result = await db.execute(
        select(Theme).where(
            Theme.id == theme_id,
            Theme.user_id == current_user.id
        )
    )
    theme = result.scalar_one_or_none()
    if not theme:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="主题不存在或无权访问"
        )
    
    # 验证文件类型
    if not file.filename.endswith('.zip'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只支持 ZIP 压缩包"
        )
    
    # 保存 ZIP 文件
    zip_path = await save_upload_file(file, current_user.id)
    
    # 解压并获取 PDF 文件列表
    try:
        pdf_files = await extract_zip(zip_path, current_user.id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"解压失败: {str(e)}"
        )
    
    # 异步处理每个 PDF
    responses = []
    for pdf_file in pdf_files:
        # 积分检查与扣减（每篇扣减）
        await check_credits(current_user, CreditType.PAPER_EXTRACT)
        await deduct_credits(db, current_user, CreditType.PAPER_EXTRACT, f"上传论文: {pdf_file.name}")
        await db.commit()
        
        try:
            paper_id = await process_pdf_async(
                file_path=pdf_file,
                user_id=current_user.id,
                workspace_id=workspace.id,
                theme_id=theme_id,
                theme_name=theme.name,
                filename=pdf_file.name,
                db=db
            )
            
            responses.append(UploadResponse(
                filename=pdf_file.name,
                file_path=str(pdf_file),
                file_size=pdf_file.stat().st_size,
                task_id=str(paper_id)
            ))
        except Exception as e:
            logger.error(f"ZIP上传单文件失败 {pdf_file.name}: {e}")
            continue
    
    return responses
