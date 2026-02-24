"""
轻量级后台任务管理器（不依赖Redis）
使用 asyncio.create_task + 内存状态存储
"""
import uuid
import asyncio
import logging
from datetime import datetime
from typing import Dict, Optional, Callable, Coroutine, Any
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class TaskStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class TaskInfo:
    """任务信息"""
    task_id: str
    status: TaskStatus = TaskStatus.PENDING
    progress: int = 0
    current_step: str = ""
    result: Optional[Dict] = None
    error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


class TaskManager:
    """后台任务管理器（asyncio 原生版）"""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._tasks: Dict[str, TaskInfo] = {}
        self._cleanup_started = False
        logger.info("TaskManager 初始化完成（asyncio 模式）")
    
    def _ensure_cleanup_loop(self):
        """确保后台清理循环已启动"""
        if self._cleanup_started:
            return
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self._periodic_cleanup())
            self._cleanup_started = True
        except RuntimeError:
            pass
    
    async def _periodic_cleanup(self, interval_seconds: int = 3600):
        """每小时自动清理过期任务"""
        while True:
            await asyncio.sleep(interval_seconds)
            self.cleanup_old_tasks()
    
    def create_task(self) -> str:
        """创建新任务，返回task_id"""
        self._ensure_cleanup_loop()
        task_id = str(uuid.uuid4())
        self._tasks[task_id] = TaskInfo(task_id=task_id)
        logger.info(f"创建任务: {task_id}")
        return task_id
    
    def get_task(self, task_id: str) -> Optional[TaskInfo]:
        """获取任务信息"""
        return self._tasks.get(task_id)
    
    def update_task(self, task_id: str, 
                    status: TaskStatus = None,
                    progress: int = None, 
                    current_step: str = None,
                    result: Dict = None,
                    error: str = None):
        """更新任务状态"""
        task = self._tasks.get(task_id)
        if not task:
            return
        
        if status is not None:
            task.status = status
        if progress is not None:
            task.progress = progress
        if current_step is not None:
            task.current_step = current_step
        if result is not None:
            task.result = result
        if error is not None:
            task.error = error
        task.updated_at = datetime.now()
        
        logger.debug(f"任务 {task_id} 更新: status={task.status}, progress={task.progress}")
    
    def submit_async_task(self, task_id: str, coro_func: Callable[..., Coroutine], *args, **kwargs):
        """提交异步协程任务到事件循环"""
        async def wrapper():
            try:
                self.update_task(task_id, status=TaskStatus.PROCESSING, progress=0)
                result = await coro_func(task_id, *args, **kwargs)
                self.update_task(task_id, status=TaskStatus.COMPLETED, progress=100, result=result)
            except Exception as e:
                logger.error(f"任务 {task_id} 失败: {e}", exc_info=True)
                self.update_task(task_id, status=TaskStatus.FAILED, error=str(e))
        
        asyncio.create_task(wrapper())
        logger.info(f"任务 {task_id} 已提交到事件循环")
    
    def cleanup_old_tasks(self, max_age_hours: int = 24):
        """清理过期任务"""
        now = datetime.now()
        to_delete = []
        for task_id, task in self._tasks.items():
            age = (now - task.created_at).total_seconds() / 3600
            if age > max_age_hours:
                to_delete.append(task_id)
        
        for task_id in to_delete:
            del self._tasks[task_id]
        
        if to_delete:
            logger.info(f"清理了 {len(to_delete)} 个过期任务")


# 全局单例
task_manager = TaskManager()
