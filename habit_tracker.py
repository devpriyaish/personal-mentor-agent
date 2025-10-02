"""
Habit tracking and analytics system
Implements Observer Pattern for habit notifications
"""
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod
from collections import defaultdict

import pandas as pd
import numpy as np

from models import Habit, HabitLog, HabitFrequency
from database import DatabaseManager


class HabitObserver(ABC):
    """Observer interface for habit events"""
    
    @abstractmethod
    def update(self, habit: Habit, event: str, data: Dict[str, Any]):
        """Receive habit event notifications"""
        pass


class HabitStreakObserver(HabitObserver):
    """Observer that tracks habit streaks"""
    
    def update(self, habit: Habit, event: str, data: Dict[str, Any]):
        """Handle habit log events"""
        if event == "habit_logged":
            streak = data.get("streak", 0)
            if streak > 0 and streak % 7 == 0:
                print(f"🎉 Milestone! {streak} day streak for {habit.name}!")


class HabitTracker:
    """Main habit tracking system - Subject in Observer Pattern"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.observers: List[HabitObserver] = []
    
    def attach_observer(self, observer: HabitObserver):
        """Attach an observer"""
        self.observers.append(observer)
    
    def detach_observer(self, observer: HabitObserver):
        """Detach an observer"""
        self.observers.remove(observer)
    
    def notify_observers(self, habit: Habit, event: str, data: Dict[str, Any]):
        """Notify all observers of an event"""
        for observer in self.observers:
            observer.update(habit, event, data)
    
    def create_habit(
        self,
        user_id: str,
        name: str,
        description: Optional[str] = None,
        frequency: HabitFrequency = HabitFrequency.DAILY,
        target_value: Optional[float] = None,
        unit: Optional[str] = None
    ) -> Habit:
        """Create a new habit"""
        habit = Habit(
            habit_id=str(uuid.uuid4()),
            user_id=user_id,
            name=name,
            description=description,
            frequency=frequency,
            target_value=target_value,
            unit=unit,
            created_at=datetime.now(),
            is_active=True
        )
        
        return self.db_manager.create_habit(habit)
    
    def log_habit(
        self,
        user_id: str,
        habit_id: str,
        value: float,
        notes: Optional[str] = None
    ) -> HabitLog:
        """Log a habit entry"""
        habit_log = HabitLog(
            log_id=str(uuid.uuid4()),
            habit_id=habit_id,
            user_id=user_id,
            value=value,
            notes=notes,
            logged_at=datetime.now()
        )
        
        result = self.db_manager.log_habit(habit_log)
        
        # Calculate streak and notify observers
        habits = self.db_manager.get_user_habits(user_id, active_only=False)
        habit = next((h for h in habits if h.habit_id == habit_id), None)
        
        if habit:
            streak = self.calculate_streak(user_id, habit_id)
            self.notify_observers(
                habit, 
                "habit_logged", 
                {"streak": streak, "value": value}
            )
        
        return result
    
    def get_user_habits(self, user_id: str) -> List[Habit]:
        """Get all active habits for a user"""
        return self.db_manager.get_user_habits(user_id, active_only=True)
    
    def calculate_streak(self, user_id: str, habit_id: str) -> int:
        """Calculate current streak for a habit"""
        logs = self.db_manager.get_habit_logs(user_id, habit_id=habit_id, days=365)
        
        if not logs:
            return 0
        
        # Sort by date (most recent first)
        logs.sort(key=lambda x: x.logged_at, reverse=True)
        
        # Get unique dates
        log_dates = set()
        for log in logs:
            log_dates.add(log.logged_at.date())
        
        # Calculate streak
        streak = 0
        current_date = datetime.now().date()
        
        while current_date in log_dates:
            streak += 1
            current_date -= timedelta(days=1)
        
        return streak
    
    def get_habit_statistics(
        self, 
        user_id: str, 
        habit_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get statistics for a habit"""
        logs = self.db_manager.get_habit_logs(user_id, habit_id=habit_id, days=days)
        
        if not logs:
            return {
                "total_logs": 0,
                "average_value": 0,
                "streak": 0,
                "completion_rate": 0,
                "trend": "neutral"
            }
        
        values = [log.value for log in logs]
        streak = self.calculate_streak(user_id, habit_id)
        
        # Calculate completion rate (assuming daily habit)
        unique_dates = set(log.logged_at.date() for log in logs)
        completion_rate = len(unique_dates) / days * 100
        
        # Calculate trend (simple: compare first half vs second half)
        mid = len(values) // 2
        if mid > 0:
            first_half_avg = np.mean(values[:mid])
            second_half_avg = np.mean(values[mid:])
            if second_half_avg > first_half_avg * 1.1:
                trend = "improving"
            elif second_half_avg < first_half_avg * 0.9:
                trend = "declining"
            else:
                trend = "stable"
        else:
            trend = "neutral"
        
        return {
            "total_logs": len(logs),
            "average_value": np.mean(values),
            "min_value": min(values),
            "max_value": max(values),
            "streak": streak,
            "completion_rate": completion_rate,
            "trend": trend,
            "recent_values": values[-7:]  # Last 7 entries
        }


class HabitAnalytics:
    """Advanced analytics for habit tracking"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def get_weekly_summary(self, user_id: str) -> Dict[str, Any]:
        """Get weekly habit summary"""
        logs = self.db_manager.get_habit_logs(user_id, days=7)
        habits = self.db_manager.get_user_habits(user_id)
        
        habit_map = {h.habit_id: h for h in habits}
        
        # Group logs by habit
        habit_logs = defaultdict(list)
        for log in logs:
            habit_logs[log.habit_id].append(log)
        
        summaries = []
        for habit_id, logs_list in habit_logs.items():
            habit = habit_map.get(habit_id)
            if habit:
                summaries.append({
                    "habit_name": habit.name,
                    "logs_count": len(logs_list),
                    "average_value": np.mean([l.value for l in logs_list]),
                    "unit": habit.unit
                })
        
        total_logs = len(logs)
        active_habits = len([h for h in habits if h.is_active])
        
        return {
            "total_logs": total_logs,
            "active_habits": active_habits,
            "habit_summaries": summaries,
            "week_start": (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d"),
            "week_end": datetime.now().strftime("%Y-%m-%d")
        }
    
    def prepare_habit_chart_data(
        self,
        user_id: str,
        habit_id: str,
        days: int = 30
    ) -> pd.DataFrame:
        """Prepare data for habit visualization"""
        logs = self.db_manager.get_habit_logs(user_id, habit_id=habit_id, days=days)
        
        if not logs:
            return pd.DataFrame(columns=["date", "value"])
        
        # Convert to DataFrame
        data = [{
            "date": log.logged_at.date(),
            "value": log.value
        } for log in logs]
        
        df = pd.DataFrame(data)
        
        # Fill missing dates with 0
        date_range = pd.date_range(
            start=datetime.now() - timedelta(days=days),
            end=datetime.now(),
            freq='D'
        )
        
        df_complete = pd.DataFrame({"date": date_range.date})
        df = df_complete.merge(df, on="date", how="left")
        df["value"] = df["value"].fillna(0)
        
        return df
    
    def get_habit_correlation(self, user_id: str) -> Dict[str, Any]:
        """Analyze correlations between habits"""
        habits = self.db_manager.get_user_habits(user_id)
        
        if len(habits) < 2:
            return {"message": "Need at least 2 habits to analyze correlations"}
        
        # Get logs for all habits
        all_logs = self.db_manager.get_habit_logs(user_id, days=30)
        
        # Create habit-date matrix
        habit_data = defaultdict(dict)
        for log in all_logs:
            date = log.logged_at.date()
            habit_data[log.habit_id][date] = log.value
        
        # Convert to DataFrame for correlation analysis
        dates = set()
        for habit_logs in habit_data.values():
            dates.update(habit_logs.keys())
        
        correlation_data = {}
        habit_names = {}
        
        for habit in habits:
            habit_names[habit.habit_id] = habit.name
            values = []
            for date in sorted(dates):
                values.append(habit_data[habit.habit_id].get(date, 0))
            correlation_data[habit.habit_id] = values
        
        if not correlation_data:
            return {"message": "No correlation data available"}
        
        df = pd.DataFrame(correlation_data)
        correlation_matrix = df.corr()
        
        # Find strong correlations
        strong_correlations = []
        for i in range(len(correlation_matrix)):
            for j in range(i+1, len(correlation_matrix)):
                corr_value = correlation_matrix.iloc[i, j]
                if abs(corr_value) > 0.5:  # Threshold for "strong"
                    habit1 = correlation_matrix.index[i]
                    habit2 = correlation_matrix.columns[j]
                    strong_correlations.append({
                        "habit1": habit_names.get(habit1, habit1),
                        "habit2": habit_names.get(habit2, habit2),
                        "correlation": float(corr_value)
                    })
        
        return {
            "correlations": strong_correlations,
            "message": "Habits with correlation > 0.5 shown" if strong_correlations else "No strong correlations found"
        }