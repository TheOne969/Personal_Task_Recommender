import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from dataclasses import dataclass
from task_manager import TaskManager
from weekly_goals import WeeklyGoalTracker

@dataclass # Basically a template for classes with storing data like this. So, you are kind of calling a function from a library.
class TaskRecommendation:
    task_name: str
    category: str
    difficulty: int
    estimated_duration: float
    priority_score: float
    reasoning: str

class RecommendationEngine:
    def __init__(self, task_manager: TaskManager, goal_tracker: WeeklyGoalTracker):
        self.task_manager = task_manager
        self.goal_tracker = goal_tracker
        
        # Scoring weights (tunable)
        self.weights = {
            'performance': 0.4,     # How well you're hitting daily targets
            'goal_progress': 0.6    # How you're progressing on weekly goals
        }
        
        # Performance targets
        self.daily_target_hours = 6.0  # Configurable daily target
        self.performance_window_days = 3  # Look at last 3 days
    
    def calculate_performance_score(self, df: pd.DataFrame) -> float:
        """
        Calculate performance score based on recent daily hours vs target
        Returns: 0.0 (way behind) to 1.0 (exceeding targets)
        """
        # Get last N days of data
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=self.performance_window_days - 1)
        
        recent_df = df[
            (df['date'] >= start_date) & 
            (df['date'] <= end_date)
        ]
        
        if recent_df.empty:
            return 0.5  # Neutral score if no recent data
        
        # Calculate daily hours for recent days
        daily_hours = recent_df.groupby('date')['duration_h'].sum()
        avg_daily_hours = daily_hours.mean()
        
        # Score based on how close to target (with some bonus for exceeding)
        ratio = avg_daily_hours / self.daily_target_hours
        
        if ratio >= 1.2:
            return 1.0  # Exceeding target significantly
        elif ratio >= 1.0:
            return 0.8 + (ratio - 1.0) * 1.0  # Bonus for exceeding
        elif ratio >= 0.8:
            return 0.6 + (ratio - 0.8) * 1.0  # Good progress
        elif ratio >= 0.5:
            return 0.3 + (ratio - 0.5) * 1.0  # Behind but not terrible
        else:
            return ratio * 0.6  # Significantly behind
    
    def calculate_weekly_goal_score(self, df: pd.DataFrame) -> Dict[str, float]:
        """
        Calculate goal completion scores for each category
        Returns: Dict mapping category -> score (0.0 to 1.0)
        """
        # Get weekly progress
        progress = self.goal_tracker.calculate_weekly_progress(df)
        
        goal_scores = {}
        for category, data in progress.items():
            completion_ratio = data['hours']['completed'] / data['hours']['target']
            
            # Score based on completion ratio and priority
            priority_multiplier = {
                'high': 1.2,
                'medium': 1.0, 
                'low': 0.8
            }.get(data['priority'], 1.0)
            
            # Base score from completion ratio
            if completion_ratio >= 1.0:
                base_score = 0.2  # Low priority if already complete
            elif completion_ratio >= 0.8:
                base_score = 0.4  # Medium priority if almost done
            elif completion_ratio >= 0.5:
                base_score = 0.8  # High priority if halfway
            else:
                base_score = 1.0  # Highest priority if way behind
            
            goal_scores[category] = min(1.0, base_score * priority_multiplier)
        
        return goal_scores
    
    def calculate_task_priority_scores(self, df: pd.DataFrame) -> List[TaskRecommendation]:
        """
        Calculate priority scores for all available tasks
        """
        # Get performance and goal scores
        performance_score = self.calculate_performance_score(df)
        goal_scores = self.calculate_weekly_goal_score(df)
        
        recommendations = []
        
        for task_name, task_info in self.task_manager.get_all_tasks().items():
            category = task_info['category']
            difficulty = int(task_info['difficulty'])
            duration = task_info.get('estimated_duration', 1.0)
            
            # Get goal score for this category (default to 0.5 if no goal)
            goal_score = goal_scores.get(category, 0.5)
            
            # Difficulty adjustment (easier tasks get slight boost when low energy)
            difficulty_adjustment = 1.0
            if performance_score < 0.5:  # Low performance = prefer easier tasks
                difficulty_adjustment = 1.3 - (difficulty * 0.1)
            
            # Calculate weighted priority score
            priority_score = (
                self.weights['performance'] * performance_score +
                self.weights['goal_progress'] * goal_score
            ) * difficulty_adjustment
            
            # Generate reasoning
            reasoning = self._generate_reasoning(
                performance_score, goal_score, category, difficulty, duration
            )
            
            recommendations.append(TaskRecommendation(
                task_name=task_name,
                category=category,
                difficulty=difficulty,
                estimated_duration=duration,
                priority_score=priority_score,
                reasoning=reasoning
            ))
        
        # Sort by priority score (highest first)
        recommendations.sort(key=lambda x: x.priority_score, reverse=True)
        return recommendations
    
    def _generate_reasoning(self, perf_score: float, goal_score: float, 
                          category: str, difficulty: int, duration: float) -> str:
        """Generate human-readable reasoning for the recommendation"""
        reasons = []
        
        # Performance-based reasoning
        if perf_score >= 0.8:
            reasons.append("You're performing well recently")
        elif perf_score >= 0.5:
            reasons.append("Your recent performance is okay")
        else:
            reasons.append("You're behind on recent daily targets")
        
        # Goal-based reasoning
        if goal_score >= 0.8:
            reasons.append(f"{category} is a high priority this week")
        elif goal_score >= 0.5:
            reasons.append(f"{category} needs attention this week")
        else:
            reasons.append(f"{category} goal is on track")
        
        # Difficulty reasoning
        if difficulty <= 2 and perf_score < 0.5:
            reasons.append("Easy task good for low-energy periods")
        elif difficulty >= 4 and perf_score >= 0.8:
            reasons.append("Challenging task while you're on a roll")
        
        return " • ".join(reasons)
    
    def get_top_recommendations(self, df: pd.DataFrame, 
                              limit: int = 3) -> List[TaskRecommendation]:
        """Get top N task recommendations"""
        all_recommendations = self.calculate_task_priority_scores(df)
        return all_recommendations[:limit]
    
    def update_weights(self, performance_weight: float, goal_weight: float):
        """Update scoring weights"""
        total = performance_weight + goal_weight
        self.weights['performance'] = performance_weight / total
        self.weights['goal_progress'] = goal_weight / total
    
    def set_daily_target(self, hours: float):
        """Update daily target hours"""
        self.daily_target_hours = hours
