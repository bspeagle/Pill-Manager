#!/usr/bin/env python3
"""Check raw calendar events"""

import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'g-cal-tools'))
sys.path.insert(0, str(Path(__file__).parent.parent))

from helpers.auth import get_calendar_service
from helpers.calendar_service import CalendarService
from rich.console import Console
import os
from dotenv import load_dotenv

env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

console = Console()
calendar_id = os.getenv('GOOGLE_CALENDAR_CUSTODY_ID')

service = get_calendar_service()
cal_service = CalendarService(service)

# Get November events
console.print("\n[bold cyan]November 2025 Calendar Events:[/bold cyan]\n")

events = cal_service.list_events(
    calendar_id=calendar_id,
    time_min='2025-11-01T00:00:00Z',
    time_max='2025-11-30T23:59:59Z'
)

console.print(f"[yellow]Found {len(events)} total events[/yellow]\n")

brian_events = []
for event in events:
    title = event.get('summary', '')
    if 'Brian' in title:
        brian_events.append(event)
        start = event.get('start', {})
        end = event.get('end', {})
        start_str = start.get('dateTime', start.get('date', 'Unknown'))[:16]
        end_str = end.get('dateTime', end.get('date', 'Unknown'))[:16]
        console.print(f"✓ {title}")
        console.print(f"   {start_str} → {end_str}\n")

console.print(f"\n[bold]Total Brian events: {len(brian_events)}[/bold]")
