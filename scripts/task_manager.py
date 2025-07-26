import json
from typing import Dict, List, Optional
from path_manager import paths
from category_mapping import CategoryMapper

class TaskManager:
    def __init__(self, tasks_path: str = None):
        tasks_path = tasks_path or paths.tasks_file
        
        with open(tasks_path, 'r') as f:
            self.tasks_config = json.load(f)
        
        self.available_tasks = self.tasks_config['available_tasks']
        self.difficulty_levels = self.tasks_config.get('difficulty_levels', {})
        
        # Initialize category mapper for validation
        self.category_mapper = CategoryMapper()
    
    def get_all_tasks(self) -> Dict:
        """Get all available tasks"""
        return self.available_tasks
    
    def get_tasks_by_category(self, category: str) -> Dict:
        """Get all tasks for a specific category"""
        return {
            task_name: task_info 
            for task_name, task_info in self.available_tasks.items()
            if task_info['category'] == category
        }
    
    def get_tasks_by_difficulty(self, difficulty: int) -> Dict:
        """Get tasks by difficulty level (1-5)"""
        return {
            task_name: task_info
            for task_name, task_info in self.available_tasks.items()
            if task_info['difficulty'] == difficulty
        }
    
    def get_tasks_by_duration(self, max_duration: float) -> Dict:
        """Get tasks that fit within a time limit"""
        return {
            task_name: task_info
            for task_name, task_info in self.available_tasks.items()
            if task_info.get('estimated_duration', 0) <= max_duration
        }
    
    def add_task(self, task_name: str, category: str, difficulty: int, 
                 estimated_duration: float = 1.0) -> bool:
        """Add a new task to the list"""
        
        # Validate category exists in CategoryMapper
        if category not in self.category_mapper.get_all_categories():
            print(f"Warning: Category '{category}' not found in category mapping")
        
        # Validate difficulty range
        if not 1 <= difficulty <= 5:
            print("Error: Difficulty must be between 1 and 5")
            return False
        
        self.available_tasks[task_name] = {
            "category": category,
            "difficulty": difficulty,
            "estimated_duration": estimated_duration
        }
        
        return True
    
    def remove_task(self, task_name: str) -> bool:
        """Remove a task from the list"""
        if task_name in self.available_tasks:
            self.available_tasks.pop(task_name)
            return True
        return False
    
    def get_task_info(self, task_name: str) -> Optional[Dict]:
        """Get detailed info for a specific task"""
        return self.available_tasks.get(task_name)
    
    def get_difficulty_description(self, difficulty: int) -> str:
        """Get human-readable difficulty description"""
        return self.difficulty_levels.get(str(difficulty))
    
    def get_categories_summary(self) -> Dict:
        """Get count of tasks per category"""
        summary = {}
        for task_info in self.available_tasks.values():
            category = task_info['category']
            summary[category] = summary.get(category, 0) + 1
        return summary
    
    def filter_tasks(self, category: str = None, max_difficulty: int = None, 
                    max_duration: float = None) -> Dict:
        """Filter tasks by multiple criteria"""
        filtered = self.available_tasks.copy()
        
        if category:
            filtered = {k: v for k, v in filtered.items() if v['category'] == category}
        
        if max_difficulty:
            filtered = {k: v for k, v in filtered.items() if v['difficulty'] <= max_difficulty}
        
        if max_duration:
            filtered = {k: v for k, v in filtered.items() 
                       if v.get('estimated_duration', 0) <= max_duration}
        
        return filtered
    
    def save_tasks(self, tasks_path: str = None) -> None:
        """Save tasks configuration back to file"""
        tasks_path = tasks_path or paths.tasks_file
        
        with open(tasks_path, 'w',encoding="utf-8") as f:
            json.dump(self.tasks_config, f, indent=2)
    
    def validate_task_categories(self) -> List[str]:
        """Check if all task categories exist in CategoryMapper"""
        invalid_categories = []
        valid_categories = self.category_mapper.get_all_categories()
        
        for task_name, task_info in self.available_tasks.items():
            if task_info['category'] not in valid_categories:
                invalid_categories.append(f"{task_name}: {task_info['category']}")
        
        return invalid_categories
