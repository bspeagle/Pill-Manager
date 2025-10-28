"""
Calendar Event Creator

Creates and manages Google Calendar events for pill reminders.
"""

import sys
from pathlib import Path
from datetime import date, datetime
from typing import Dict, List, Optional

# Add g-cal-tools to path
gcal_tools_path = Path(__file__).parent.parent.parent.parent / 'g-cal-tools'
sys.path.insert(0, str(gcal_tools_path))

from helpers.auth import get_calendar_service
from helpers.calendar_service import CalendarService


class PillEventCreator:
    """Creates pill reminder events in Google Calendar"""
    
    # Event templates based on treasure map
    EVENT_TEMPLATES = {
        'mom_out': {
            'summary': '💊 [ADHD-PILLS] Ex Out of Meds',
            'description': 'Ex-wife runs out of ADHD medication today.',
            'colorId': '11',  # Red
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'popup', 'minutes': 1440}  # 1 day before
                ]
            }
        },
        'refill_eligible': {
            'summary': '💊 [ADHD-PILLS] Can Refill Prescription',
            'description': 'Eligible to refill ADHD prescription (85% rule met). Contact pharmacy/doctor.',
            'colorId': '9',  # Blue
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'popup', 'minutes': 0}  # Day of
                ]
            }
        },
        'distribution_due': {
            'summary': '💊 [ADHD-PILLS] Give {quantity} Pills to Ex',
            'description': 'Give {quantity} ADHD pills to ex-wife for her custody days.\n\nFor custody period: {period}',
            'colorId': '10',  # Green
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'popup', 'minutes': 60},    # 1 hour before
                    {'method': 'popup', 'minutes': 1440}   # 1 day before
                ]
            }
        }
    }
    
    def __init__(self, calendar_id: str):
        """
        Initialize event creator.
        
        Args:
            calendar_id: Google Calendar ID where events will be created
        """
        self.calendar_id = calendar_id
        service = get_calendar_service()
        self.cal_service = CalendarService(service)
    
    def create_mom_out_event(self, out_date: date) -> Dict:
        """
        Create event for when mom runs out of pills.
        
        Args:
            out_date: Date mom runs out
            
        Returns:
            Created event data
        """
        template = self.EVENT_TEMPLATES['mom_out'].copy()
        
        event_data = {
            'summary': template['summary'],
            'description': template['description'],
            'start': {
                'date': out_date.isoformat()
            },
            'end': {
                'date': out_date.isoformat()
            },
            'colorId': template['colorId'],
            'reminders': template['reminders']
        }
        
        return self.cal_service.create_event(
            calendar_id=self.calendar_id,
            event_data=event_data
        )
    
    def create_refill_eligible_event(self, refill_date: date) -> Dict:
        """
        Create event for when prescription can be refilled.
        
        Args:
            refill_date: Date eligible to refill
            
        Returns:
            Created event data
        """
        template = self.EVENT_TEMPLATES['refill_eligible'].copy()
        
        event_data = {
            'summary': template['summary'],
            'description': template['description'],
            'start': {
                'date': refill_date.isoformat()
            },
            'end': {
                'date': refill_date.isoformat()
            },
            'colorId': template['colorId'],
            'reminders': template['reminders']
        }
        
        return self.cal_service.create_event(
            calendar_id=self.calendar_id,
            event_data=event_data
        )
    
    def create_distribution_event(
        self,
        distribution_date: date,
        quantity: int,
        period_start: date,
        period_end: date
    ) -> Dict:
        """
        Create event for giving pills to ex-wife.
        
        Args:
            distribution_date: Date to give pills
            quantity: Number of pills to give
            period_start: Start of custody period
            period_end: End of custody period
            
        Returns:
            Created event data
        """
        template = self.EVENT_TEMPLATES['distribution_due'].copy()
        
        period_str = f"{period_start.strftime('%b %d')} - {period_end.strftime('%b %d, %Y')}"
        
        event_data = {
            'summary': template['summary'].format(quantity=quantity),
            'description': template['description'].format(
                quantity=quantity,
                period=period_str
            ),
            'start': {
                'date': distribution_date.isoformat()
            },
            'end': {
                'date': distribution_date.isoformat()
            },
            'colorId': template['colorId'],
            'reminders': template['reminders']
        }
        
        return self.cal_service.create_event(
            calendar_id=self.calendar_id,
            event_data=event_data
        )
    
    def create_all_events(
        self,
        mom_out_date: date,
        refill_date: date,
        distribution_date: date,
        pills_to_give: int,
        period_start: date,
        period_end: date
    ) -> Dict[str, any]:
        """
        Create all three pill reminder events.
        
        Args:
            mom_out_date: When mom runs out
            refill_date: When can refill
            distribution_date: When to give pills
            pills_to_give: How many pills to give
            period_start: Start of distribution period
            period_end: End of distribution period
            
        Returns:
            Dictionary with results for each event type
        """
        results = {
            'created': [],
            'failed': [],
            'errors': []
        }
        
        # Create mom out event
        try:
            event = self.create_mom_out_event(mom_out_date)
            results['created'].append({
                'type': 'mom_out',
                'date': mom_out_date,
                'event_id': event.get('id'),
                'summary': event.get('summary')
            })
        except Exception as e:
            results['failed'].append('mom_out')
            results['errors'].append({
                'type': 'mom_out',
                'error': str(e)
            })
        
        # Create refill eligible event
        try:
            event = self.create_refill_eligible_event(refill_date)
            results['created'].append({
                'type': 'refill_eligible',
                'date': refill_date,
                'event_id': event.get('id'),
                'summary': event.get('summary')
            })
        except Exception as e:
            results['failed'].append('refill_eligible')
            results['errors'].append({
                'type': 'refill_eligible',
                'error': str(e)
            })
        
        # Create distribution event
        try:
            event = self.create_distribution_event(
                distribution_date,
                pills_to_give,
                period_start,
                period_end
            )
            results['created'].append({
                'type': 'distribution_due',
                'date': distribution_date,
                'event_id': event.get('id'),
                'summary': event.get('summary')
            })
        except Exception as e:
            results['failed'].append('distribution_due')
            results['errors'].append({
                'type': 'distribution_due',
                'error': str(e)
            })
        
        return results
    
    def search_existing_pill_events(
        self,
        start_date: date,
        end_date: date
    ) -> List[Dict]:
        """
        Search for existing pill reminder events.
        
        Args:
            start_date: Start of search range
            end_date: End of search range
            
        Returns:
            List of existing pill events
        """
        time_min = datetime.combine(start_date, datetime.min.time()).isoformat() + 'Z'
        time_max = datetime.combine(end_date, datetime.max.time()).isoformat() + 'Z'
        
        all_events = self.cal_service.list_events(
            calendar_id=self.calendar_id,
            time_min=time_min,
            time_max=time_max
        )
        
        # Filter for pill events (containing [ADHD-PILLS] tag)
        pill_events = [
            event for event in all_events
            if '[ADHD-PILLS]' in event.get('summary', '')
        ]
        
        return pill_events
