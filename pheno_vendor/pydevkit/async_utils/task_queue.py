"""Async task queue."""

import asyncio
from typing import Callable, Any, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Task:
    """Task data."""
    id: str
    func: Callable
    args: tuple
    kwargs: dict
    priority: int = 0
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


class TaskQueue:
    """
    Async task queue with concurrency control.

    Example:
        queue = TaskQueue(max_workers=5)
        await queue.start()
        
        await queue.enqueue(my_async_function, arg1, arg2)
        
        await queue.stop()
    """

    def __init__(self, max_workers: int = 5):
        self.max_workers = max_workers
        self._queue: asyncio.Queue = asyncio.Queue()
        self._workers: List[asyncio.Task] = []
        self._running = False

    async def start(self):
        """Start queue workers."""
        self._running = True
        self._workers = [
            asyncio.create_task(self._worker(i))
            for i in range(self.max_workers)
        ]

    async def stop(self):
        """Stop queue workers."""
        self._running = False
        await self._queue.join()
        for worker in self._workers:
            worker.cancel()
        await asyncio.gather(*self._workers, return_exceptions=True)

    async def enqueue(self, func: Callable, *args, **kwargs) -> str:
        """Enqueue task."""
        task = Task(
            id=f"task_{id(func)}_{datetime.now().timestamp()}",
            func=func,
            args=args,
            kwargs=kwargs,
        )
        await self._queue.put(task)
        return task.id

    async def _worker(self, worker_id: int):
        """Worker coroutine."""
        while self._running:
            try:
                task = await asyncio.wait_for(
                    self._queue.get(),
                    timeout=1.0
                )
                
                try:
                    if asyncio.iscoroutinefunction(task.func):
                        await task.func(*task.args, **task.kwargs)
                    else:
                        task.func(*task.args, **task.kwargs)
                except Exception:
                    pass
                finally:
                    self._queue.task_done()
                    
            except asyncio.TimeoutError:
                continue
