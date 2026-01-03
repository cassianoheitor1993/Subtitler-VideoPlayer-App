"""
Background Task Manager
Manages long-running tasks (AI generation, translation) in background threads
"""

from PyQt6.QtCore import QObject, QThread, pyqtSignal
from typing import Callable, Optional, Any, List
from dataclasses import dataclass
from enum import Enum
import time


class TaskType(Enum):
    """Types of background tasks"""
    AI_GENERATION = "ai_generation"
    TRANSLATION = "translation"
    PROXY_TRANSCODE = "proxy_transcode"


class TaskStatus(Enum):
    """Status of a background task"""
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class TaskInfo:
    """Information about a background task"""
    task_id: str
    task_type: TaskType
    status: TaskStatus
    progress: int  # 0-100
    message: str
    result: Any = None
    error: str = None


class BackgroundWorker(QThread):
    """Worker thread for executing background tasks"""
    
    progress_updated = pyqtSignal(str, int)  # task_id, progress
    message_updated = pyqtSignal(str, str)   # task_id, message
    task_completed = pyqtSignal(str, object)  # task_id, result
    task_failed = pyqtSignal(str, str)        # task_id, error
    
    def __init__(self, task_id: str, task_func: Callable, *args, **kwargs):
        super().__init__()
        self.task_id = task_id
        self.task_func = task_func
        self.args = args
        self.kwargs = kwargs
        self._cancelled = False
    
    def run(self):
        """Execute the task in background thread"""
        try:
            # Create progress callback
            def progress_callback(message: str, progress: int):
                if self._cancelled:
                    return
                self.progress_updated.emit(self.task_id, progress)
                self.message_updated.emit(self.task_id, message)
            
            # Create cancel check callback
            def cancel_check():
                return self._cancelled
            
            # Add callbacks to kwargs
            self.kwargs['progress_callback'] = progress_callback
            if 'cancel_check' not in self.kwargs:
                self.kwargs['cancel_check'] = cancel_check
            
            # Execute task
            result = self.task_func(*self.args, **self.kwargs)
            
            if self._cancelled:
                return
            
            # Emit completion
            self.task_completed.emit(self.task_id, result)
            
        except Exception as e:
            error_msg = str(e)
            self.task_failed.emit(self.task_id, error_msg)
    
    def cancel(self):
        """Request task cancellation"""
        self._cancelled = True


class BackgroundTaskManager(QObject):
    """Manages background tasks with status tracking"""
    
    task_started = pyqtSignal(TaskInfo)
    task_progress = pyqtSignal(TaskInfo)
    task_completed = pyqtSignal(TaskInfo)
    task_failed = pyqtSignal(TaskInfo)
    
    def __init__(self):
        super().__init__()
        self.tasks = {}  # task_id -> TaskInfo
        self.workers = {}  # task_id -> BackgroundWorker
    
    def start_task(
        self,
        task_type: TaskType,
        task_func: Callable,
        *args,
        **kwargs
    ) -> str:
        """
        Start a background task
        
        Args:
            task_type: Type of task
            task_func: Function to execute
            *args, **kwargs: Arguments for task_func
            
        Returns:
            task_id: Unique identifier for this task
        """
        # Generate unique task ID
        task_id = f"{task_type.value}_{int(time.time() * 1000)}"
        
        # Create task info
        task_info = TaskInfo(
            task_id=task_id,
            task_type=task_type,
            status=TaskStatus.RUNNING,
            progress=0,
            message="Starting..."
        )
        
        self.tasks[task_id] = task_info
        
        # Create worker thread
        worker = BackgroundWorker(task_id, task_func, *args, **kwargs)
        worker.progress_updated.connect(self._on_progress_updated)
        worker.message_updated.connect(self._on_message_updated)
        worker.task_completed.connect(self._on_task_completed)
        worker.task_failed.connect(self._on_task_failed)
        worker.finished.connect(lambda: self._cleanup_worker(task_id))
        
        self.workers[task_id] = worker
        
        # Start worker
        worker.start()
        
        # Emit started signal
        self.task_started.emit(task_info)
        
        return task_id
    
    def cancel_task(self, task_id: str):
        """Cancel a running task"""
        if task_id in self.workers:
            worker = self.workers[task_id]
            worker.cancel()
            
            if task_id in self.tasks:
                self.tasks[task_id].status = TaskStatus.CANCELLED
                self.tasks[task_id].message = "Cancelled by user"
                self.task_failed.emit(self.tasks[task_id])
    
    def get_task(self, task_id: str) -> Optional[TaskInfo]:
        """Get task information"""
        return self.tasks.get(task_id)
    
    def get_active_tasks(self) -> list[TaskInfo]:
        """Get all active (running) tasks"""
        return [
            task for task in self.tasks.values()
            if task.status == TaskStatus.RUNNING
        ]
    
    def _on_progress_updated(self, task_id: str, progress: int):
        """Handle progress update from worker"""
        if task_id in self.tasks:
            self.tasks[task_id].progress = progress
            self.task_progress.emit(self.tasks[task_id])
    
    def _on_message_updated(self, task_id: str, message: str):
        """Handle message update from worker"""
        if task_id in self.tasks:
            self.tasks[task_id].message = message
            self.task_progress.emit(self.tasks[task_id])
    
    def _on_task_completed(self, task_id: str, result: Any):
        """Handle task completion"""
        if task_id in self.tasks:
            self.tasks[task_id].status = TaskStatus.COMPLETED
            self.tasks[task_id].progress = 100
            self.tasks[task_id].message = "Completed!"
            self.tasks[task_id].result = result
            self.task_completed.emit(self.tasks[task_id])
    
    def _on_task_failed(self, task_id: str, error: str):
        """Handle task failure"""
        if task_id in self.tasks:
            self.tasks[task_id].status = TaskStatus.FAILED
            self.tasks[task_id].message = f"Error: {error}"
            self.tasks[task_id].error = error
            self.task_failed.emit(self.tasks[task_id])
    
    def _cleanup_worker(self, task_id: str):
        """Cleanup worker after thread finishes"""
        if task_id in self.workers:
            worker = self.workers[task_id]
            worker.deleteLater()
            del self.workers[task_id]
    
    def get_active_tasks(self) -> List[str]:
        """Get list of active (running) task IDs"""
        return [
            task_id for task_id, task_info in self.tasks.items()
            if task_info.status == TaskStatus.RUNNING
        ]
    
    def get_task_info(self, task_id: str) -> Optional[TaskInfo]:
        """Get task information by ID"""
        return self.tasks.get(task_id)
