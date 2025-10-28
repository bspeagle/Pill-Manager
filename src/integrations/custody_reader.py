"""
Custody Schedule Reader

Reads custody schedule from Google Calendar and determines pill days
for each parent based on the "golden rule": whoever the child woke up
with that morning gives the pill.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta, date
from typing import List, Dict, Tuple

# Add g-cal-tools to path
gcal_tools_path = Path(__file__).parent.parent.parent.parent / 'g-cal-tools'
sys.path.insert(0, str(gcal_tools_path))

from helpers.auth import get_calendar_service
from helpers.calendar_service import CalendarService


class CustodyReader:
    """Reads custody schedule and calculates pill days"""
    
    FATHER_EVENT_TITLE = "Brian"
    
    def __init__(self, calendar_id: str):
        """
        Initialize custody reader.
        
        Args:
            calendar_id: Google Calendar ID for custody schedule
        """
        self.calendar_id = calendar_id
        service = get_calendar_service()
        self.cal_service = CalendarService(service)
    
    def get_custody_blocks(
        self,
        start_date: date,
        end_date: date
    ) -> List[Dict]:
        """
        Get father's custody blocks from calendar.
        
        Args:
            start_date: Start of date range
            end_date: End of date range
            
        Returns:
            List of custody blocks with start/end dates
        """
        time_min = datetime.combine(start_date, datetime.min.time()).isoformat() + 'Z'
        time_max = datetime.combine(end_date, datetime.max.time()).isoformat() + 'Z'
        
        events = self.cal_service.list_events(
            calendar_id=self.calendar_id,
            time_min=time_min,
            time_max=time_max
        )
        
        custody_blocks = []
        for event in events:
            # Match events with "Brian" in the title (e.g., "Brian", "Brian/Thanksgiving", "Brian - Bday")
            if self.FATHER_EVENT_TITLE in event.get('summary', ''):
                start = event.get('start', {})
                end = event.get('end', {})
                
                # Parse start datetime
                start_dt_str = start.get('dateTime')
                if start_dt_str:
                    start_dt = datetime.fromisoformat(start_dt_str.replace('Z', '+00:00'))
                else:
                    continue  # Skip if no valid start time
                
                # Parse end datetime
                end_dt_str = end.get('dateTime')
                if end_dt_str:
                    end_dt = datetime.fromisoformat(end_dt_str.replace('Z', '+00:00'))
                else:
                    continue  # Skip if no valid end time
                
                custody_blocks.append({
                    'start': start_dt,
                    'end': end_dt,
                    'event_id': event.get('id')
                })
        
        return custody_blocks
    
    def get_pill_days(
        self,
        start_date: date,
        end_date: date
    ) -> Tuple[List[date], List[date]]:
        """
        Calculate pill days for each parent.
        
        Golden Rule: Whoever the child woke up with that morning gives the pill.
        
        Custody Block: Start @ 5pm → End @ 5pm
        Pill Days: Mornings of (Start + 1 day) through (End day) inclusive
        
        Args:
            start_date: Start of calculation period
            end_date: End of calculation period
            
        Returns:
            Tuple of (father_pill_days, mother_pill_days)
        """
        # Get custody blocks
        custody_blocks = self.get_custody_blocks(start_date, end_date)
        
        # Calculate father's pill days from custody blocks
        father_pill_days = set()
        
        for block in custody_blocks:
            # Pill days are from (start + 1 day) through (end day) inclusive
            current_date = block['start'].date() + timedelta(days=1)
            end_date_block = block['end'].date()
            
            while current_date <= end_date_block:
                # Only include if within requested range
                if start_date <= current_date <= end_date:
                    father_pill_days.add(current_date)
                current_date += timedelta(days=1)
        
        # Generate all days in range
        all_days = set()
        current = start_date
        while current <= end_date:
            all_days.add(current)
            current += timedelta(days=1)
        
        # Mother has all days NOT in father's set
        mother_pill_days = all_days - father_pill_days
        
        # Convert to sorted lists
        father_days_sorted = sorted(list(father_pill_days))
        mother_days_sorted = sorted(list(mother_pill_days))
        
        return father_days_sorted, mother_days_sorted
    
    def get_pill_distribution(
        self,
        start_date: date,
        end_date: date
    ) -> Dict:
        """
        Calculate pill distribution between parents.
        
        Args:
            start_date: Start of distribution period
            end_date: End of distribution period
            
        Returns:
            Dictionary with distribution details
        """
        father_days, mother_days = self.get_pill_days(start_date, end_date)
        
        return {
            'start_date': start_date,
            'end_date': end_date,
            'total_days': (end_date - start_date).days + 1,
            'father_days': father_days,
            'father_pills': len(father_days),
            'mother_days': mother_days,
            'mother_pills': len(mother_days),
        }
    
    def get_next_mother_custody_day(self, after_date: date) -> date:
        """
        Find the next day mother has custody (gives pill).
        
        Args:
            after_date: Find custody day AFTER (not including) this date
            
        Returns:
            Next date mother has custody
        """
        # Look ahead 14 days to find next mother custody
        search_end = after_date + timedelta(days=14)
        
        father_days, mother_days = self.get_pill_days(after_date, search_end)
        
        # Find first mother day AFTER after_date (not including after_date itself)
        for day in mother_days:
            if day > after_date:  # Changed from >= to >
                return day
        
        # Shouldn't reach here if pattern is correct
        raise ValueError(f"No mother custody day found after {after_date}")
