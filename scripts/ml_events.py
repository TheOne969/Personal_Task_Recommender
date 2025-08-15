from dataclasses import dataclass
from datetime import datetime

@dataclass
class TaskEvent:
    task_name: str
    category: str
    difficulty: int
    started_at: datetime
    completed: bool
    perf_score_at_start: float
    hour_of_day: int
    category_completion: float
