from path_manager import paths
import pandas as pd
import json
import datetime as dt

class DailyGoalTracker:
    def __init__(self, config_path: str = None):
        config_path = config_path or paths.config_file
        with open(config_path, 'r',encoding="utf-8") as f:
            self.config = json.load(f)
        self.target_hours = self.config['daily_target_hours']
        self.rolling_window = self.config['rolling_window_days']
    
    def calculate_daily_stats(self, df: pd.DataFrame) -> dict:
        """Calculate daily time stats from Toggl data"""
        df['date'] = pd.to_datetime(df['start']).dt.date
        daily_hours = df.groupby('date')['duration_h'].sum()  
        
        # Get last N days
        today = dt.date.today()
        recent_days = [today - dt.timedelta(days=i+1) for i in range(self.rolling_window)]
        
        recent_hours = []
        for day in recent_days:
            hours = daily_hours.get(day, 0) # panda series could be accessed just like a dict.
            recent_hours.append(hours)
        
        rolling_avg = sum(recent_hours) / len(recent_hours)
        
        return {
            'daily_hours': daily_hours.to_dict(),
            'rolling_average': rolling_avg,
            'target_hours': self.target_hours,
            'performance_ratio': rolling_avg / self.target_hours,
            'recent_days_data': list(zip(recent_days, recent_hours))
        }
    
    def get_performance_status(self, performance_ratio: float) -> str:
        """Get performance status text"""
        if performance_ratio >= 1.0:
            return "✅ On track!"
        elif performance_ratio >= 0.8:
            return "⚠️ Slightly behind"
        else:
            return "❌ Significantly behind"
