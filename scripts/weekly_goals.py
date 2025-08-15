import pandas as pd
import json
from datetime import datetime, timedelta
from typing import Dict, List
from path_manager import paths
from category_mapping import CategoryMapper

class WeeklyGoalTracker:
    def __init__(self, goals_path: str = None):
        goals_path = goals_path or paths.goals_file
        with open(goals_path, 'r') as f:
            self.goals_config = json.load(f)
        self.weekly_goals = self.goals_config['weekly_goals']
        
        # Initialize category mapper
        self.category_mapper = CategoryMapper()
    
    def get_current_week_range(self) -> tuple:
        """Get start and end of current week"""
        today = datetime.now()
        days_since_monday = today.weekday()
        week_start = today - timedelta(days=days_since_monday)
        week_end = week_start + timedelta(days=6)
        return week_start.date(), week_end.date()
    
    def calculate_weekly_progress(self, df: pd.DataFrame) -> Dict:
        """Calculate progress for each weekly goal"""
        week_start, week_end = self.get_current_week_range()
        
        # Filter data for current week
        week_df = df[(df['date'] >= week_start) & (df['date'] <= week_end)]
        
        # Add category column using mapper
        week_df.loc[:,'category'] = week_df.apply(self.category_mapper.get_category_for_row, axis=1) #.loc tells pandas unambigiously that the original dataframe will change, preventing unnecessary warnings. ':' is basically referring to all rows. 
        # axis = 0 means go column wise and 1 go row wise. 
        
        progress = {}
        
        for category, goal_info in self.weekly_goals.items():
            # Filter by mapped category
            category_df = week_df[week_df['category'] == category]
            
            hours_completed = category_df['duration_h'].sum() 
            
            progress[category] = {
                'hours': {
                    'completed': round(hours_completed, 2),
                    'target': goal_info['target_hours'],
                    'percentage': min(100, (hours_completed / goal_info['target_hours']) * 100)
                },
                'priority': goal_info['priority'],
                'status': self.get_goal_status(hours_completed, goal_info['target_hours'])
            }
        
        return progress
    
    def get_goal_status(self, completed: float, target: float) -> str:
        """Get status emoji and text"""
        ratio = completed / target
        if ratio >= 1.0:
            return "✅ Complete"
        elif ratio >= 0.7:
            return "📈 In Progress"
        else:
            return "❌ Behind"
    
    def get_priority_categories(self) -> List[str]:
        """Get categories sorted by priority"""
        high_priority = [cat for cat, info in self.weekly_goals.items() if info['priority'] == 'high']
        medium_priority = [cat for cat, info in self.weekly_goals.items() if info['priority'] == 'medium']
        low_priority = [cat for cat, info in self.weekly_goals.items() if info['priority'] == 'low']
        
        return high_priority + medium_priority + low_priority
