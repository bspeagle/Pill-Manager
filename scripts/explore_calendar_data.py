#!/usr/bin/env python3
"""
Calendar Data Explorer

Mines calendar data to understand:
1. PP schedule format and patterns
2. Existing HCBM pill event structure
3. Data patterns for building proper parsers

Run this before building the core logic!
"""

import sys
import json
from datetime import datetime, timedelta
from pathlib import Path

# Add g-cal-tools to path (two levels up from scripts/, then into g-cal-tools)
gcal_tools_path = Path(__file__).parent.parent.parent / 'g-cal-tools'
sys.path.insert(0, str(gcal_tools_path))

from helpers.auth import get_calendar_service
from helpers.calendar_service import CalendarService
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich import print as rprint

console = Console()


def select_calendar(cal_service):
    """Let user select a calendar"""
    calendars = cal_service.list_calendars()
    
    table = Table(title="📅 Available Calendars")
    table.add_column("#", style="cyan", width=4)
    table.add_column("Calendar Name", style="green")
    table.add_column("Access", style="yellow", width=12)
    table.add_column("Primary", justify="center", width=8)
    
    for idx, cal in enumerate(calendars, 1):
        primary = "✓" if cal.get('primary') else ""
        table.add_row(str(idx), cal['summary'], cal['access_role'], primary)
    
    console.print(table)
    
    while True:
        choice = Prompt.ask(f"\nSelect calendar", default="1")
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(calendars):
                selected = calendars[idx]
                console.print(f"\n[green]✓[/green] Selected: [cyan]{selected['summary']}[/cyan]")
                return selected['id'], selected['summary']
            console.print("[red]Invalid selection. Please try again.[/red]")
        except ValueError:
            console.print("[red]Invalid input. Please enter a number.[/red]")


def explore_custody_schedule(cal_service, calendar_id, days=None):
    """Explore PP schedule events"""
    console.print("\n[bold cyan]═══ Custody Schedule Analysis ═══[/bold cyan]")
    
    # Get date range - full 2025 year
    start_date = datetime(2025, 1, 1, 0, 0, 0)
    end_date = datetime(2025, 12, 31, 23, 59, 59)
    
    time_min = start_date.isoformat() + 'Z'
    time_max = end_date.isoformat() + 'Z'
    
    console.print(f"\n[yellow]Fetching events from {start_date.date()} to {end_date.date()}...[/yellow]")
    
    events = cal_service.list_events(
        calendar_id=calendar_id,
        time_min=time_min,
        time_max=time_max
    )
    
    console.print(f"[green]✓ Found {len(events)} events[/green]\n")
    
    # Analyze event patterns
    event_titles = {}
    for event in events:
        title = event.get('summary', '(No title)')
        event_titles[title] = event_titles.get(title, 0) + 1
    
    # Show title frequency
    table = Table(title="Event Title Frequency")
    table.add_column("Title", style="cyan")
    table.add_column("Count", style="green", justify="right")
    
    for title, count in sorted(event_titles.items(), key=lambda x: x[1], reverse=True)[:10]:
        table.add_row(title, str(count))
    
    console.print(table)
    
    # Show sample events
    console.print("\n[bold]Sample Events (First 10):[/bold]")
    sample_table = Table()
    sample_table.add_column("Date", style="yellow")
    sample_table.add_column("Title", style="cyan")
    sample_table.add_column("Type", style="green")
    sample_table.add_column("Description", style="dim", max_width=40)
    
    for event in events[:10]:
        start = event.get('start', {})
        date_str = start.get('date', start.get('dateTime', 'Unknown'))[:10]
        title = event.get('summary', '(No title)')
        event_type = 'All-day' if 'date' in start else 'Timed'
        description = event.get('description', '')[:40]
        
        sample_table.add_row(date_str, title, event_type, description)
    
    console.print(sample_table)
    
    # Export to JSON
    export_data = {
        'calendar_name': 'Custody Schedule',
        'date_range': {
            'start': start_date.isoformat(),
            'end': end_date.isoformat()
        },
        'total_events': len(events),
        'title_frequency': event_titles,
        'sample_events': [
            {
                'summary': e.get('summary'),
                'start': e.get('start'),
                'end': e.get('end'),
                'description': e.get('description'),
                'id': e.get('id')
            }
            for e in events[:20]
        ]
    }
    
    return export_data, events


def explore_hcbm_events(cal_service, calendar_id):
    """Explore existing HCBM pill events"""
    console.print("\n[bold cyan]═══ HCBM Pill Events Analysis ═══[/bold cyan]")
    
    # Search for last 90 days + future
    start_date = datetime.now() - timedelta(days=90)
    end_date = datetime.now() + timedelta(days=180)
    
    time_min = start_date.isoformat() + 'Z'
    time_max = end_date.isoformat() + 'Z'
    
    console.print(f"\n[yellow]Searching for 'HCBM' events...[/yellow]")
    
    hcbm_events = cal_service.search_events_by_title(
        calendar_id=calendar_id,
        title_query="HCBM",
        time_min=time_min,
        time_max=time_max,
        case_sensitive=False
    )
    
    if not hcbm_events:
        console.print("[yellow]No HCBM events found[/yellow]")
        return None, []
    
    console.print(f"[green]✓ Found {len(hcbm_events)} HCBM events[/green]\n")
    
    # Show all HCBM events
    table = Table(title="HCBM Events")
    table.add_column("Date", style="yellow")
    table.add_column("Title", style="cyan")
    table.add_column("Description", style="green", max_width=50)
    table.add_column("Reminders", style="magenta")
    
    for event in hcbm_events:
        start = event.get('start', {})
        date_str = start.get('date', start.get('dateTime', 'Unknown'))[:10]
        title = event.get('summary', '')
        description = event.get('description', '')[:50]
        reminders = event.get('reminders', {})
        reminder_str = 'Yes' if reminders.get('useDefault') or reminders.get('overrides') else 'No'
        
        table.add_row(date_str, title, description, reminder_str)
    
    console.print(table)
    
    # Show detailed structure of first event
    if hcbm_events:
        console.print("\n[bold]Detailed Structure (First Event):[/bold]")
        first_event = hcbm_events[0]
        
        details = {
            'id': first_event.get('id'),
            'summary': first_event.get('summary'),
            'description': first_event.get('description'),
            'start': first_event.get('start'),
            'end': first_event.get('end'),
            'reminders': first_event.get('reminders'),
            'colorId': first_event.get('colorId'),
            'created': first_event.get('created'),
            'updated': first_event.get('updated')
        }
        
        console.print(Panel(
            json.dumps(details, indent=2, default=str),
            title="Event Structure",
            border_style="cyan"
        ))
    
    # Export to JSON
    export_data = {
        'calendar_name': 'HCBM Events',
        'date_range': {
            'start': start_date.isoformat(),
            'end': end_date.isoformat()
        },
        'total_events': len(hcbm_events),
        'events': [
            {
                'id': e.get('id'),
                'summary': e.get('summary'),
                'description': e.get('description'),
                'start': e.get('start'),
                'end': e.get('end'),
                'reminders': e.get('reminders'),
                'colorId': e.get('colorId')
            }
            for e in hcbm_events
        ]
    }
    
    return export_data, hcbm_events


def main():
    """Main data exploration workflow"""
    console.print("\n[bold magenta]═════════════════════════════════════════[/bold magenta]")
    console.print("[bold magenta]   📊 Calendar Data Explorer 🗓️          [/bold magenta]")
    console.print("[bold magenta]═════════════════════════════════════════[/bold magenta]")
    
    try:
        # Initialize calendar service
        console.print("\n[yellow]Authenticating with Google Calendar...[/yellow]")
        service = get_calendar_service()
        cal_service = CalendarService(service)
        console.print("[green]✓ Authenticated![/green]")
        
        # Select calendar
        calendar_id, calendar_name = select_calendar(cal_service)
        
        # Explore custody schedule (full 2025 year)
        custody_data, custody_events = explore_custody_schedule(cal_service, calendar_id)
        
        # Explore HCBM events
        hcbm_data, hcbm_events = explore_hcbm_events(cal_service, calendar_id)
        
        # Export all data
        if Confirm.ask("\n[bold]Export data to JSON files?[/bold]", default=True):
            # Export custody data
            custody_file = Path('data/custody_schedule_export.json')
            custody_file.parent.mkdir(exist_ok=True)
            custody_file.write_text(json.dumps(custody_data, indent=2, default=str))
            console.print(f"[green]✓ Exported custody data to {custody_file}[/green]")
            
            # Export HCBM data
            if hcbm_data:
                hcbm_file = Path('data/hcbm_events_export.json')
                hcbm_file.write_text(json.dumps(hcbm_data, indent=2, default=str))
                console.print(f"[green]✓ Exported HCBM data to {hcbm_file}[/green]")
        
        console.print("\n[bold green]═════════════════════════════════════════[/bold green]")
        console.print("[bold green]   ✓ Data Mining Complete!               [/bold green]")
        console.print("[bold green]═════════════════════════════════════════[/bold green]\n")
        
        # Summary
        console.print("[bold cyan]Summary:[/bold cyan]")
        console.print(f"  • Custody events: {len(custody_events)}")
        console.print(f"  • HCBM events: {len(hcbm_events) if hcbm_events else 0}")
        console.print(f"  • Calendar: {calendar_name}")
        
    except Exception as e:
        console.print(f"\n[bold red]Error: {e}[/bold red]")
        import traceback
        console.print(traceback.format_exc())


if __name__ == "__main__":
    main()
