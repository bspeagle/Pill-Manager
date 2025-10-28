#!/usr/bin/env python3
"""Check winter holiday handling"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'g-cal-tools'))

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

console.print("\n[bold cyan]🎄 Winter Holiday Events[/bold cyan]\n")

# Check Dec 2025 - Jan 2026
events = cal_service.list_events(
    calendar_id=calendar_id,
    time_min='2025-12-01T00:00:00Z',
    time_max='2026-01-31T23:59:59Z'
)

console.print(f"Found {len(events)} events\n")

for event in events:
    title = event.get('summary', '')
    if 'Winter' in title or 'Holiday' in title or 'Brian' in title:
        console.print(f"[bold]{title}[/bold]")
        start = event.get('start', {})
        end = event.get('end', {})
        desc = event.get('description', 'No description')
        
        start_str = start.get('date') or start.get('dateTime', 'Unknown')[:10]
        end_str = end.get('date') or end.get('dateTime', 'Unknown')[:10]
        
        console.print(f"  Date: {start_str} → {end_str}")
        console.print(f"  Description: {desc[:100]}")
        console.print()

console.print("\n[yellow]⚠️  2025 is an ODD year[/yellow]")
console.print("[dim]F(E)/M(O) means: Father=Even Years, Mother=Odd Years[/dim]")
console.print("[dim]So in 2025 (odd), events marked F(E)/M(O) go to MOTHER[/dim]\n")
