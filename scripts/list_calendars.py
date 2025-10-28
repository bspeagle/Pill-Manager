#!/usr/bin/env python3
"""
List Google Calendars and Their IDs

Shows all accessible calendars with their IDs for configuration.
"""

import sys
from pathlib import Path

# Add g-cal-tools to path
gcal_tools_path = Path(__file__).parent.parent.parent / 'g-cal-tools'
sys.path.insert(0, str(gcal_tools_path))

from helpers.auth import get_calendar_service
from helpers.calendar_service import CalendarService
from rich.console import Console
from rich.table import Table

console = Console()


def list_calendars():
    """List all calendars with their IDs"""
    
    console.print("\n[bold cyan]📅 Your Google Calendars[/bold cyan]\n")
    
    # Initialize calendar service
    console.print("[yellow]Authenticating...[/yellow]")
    service = get_calendar_service()
    cal_service = CalendarService(service)
    console.print("[green]✓ Authenticated![/green]\n")
    
    # Get calendars
    calendars = cal_service.list_calendars()
    
    # Display in table
    table = Table(title="Available Calendars")
    table.add_column("Calendar Name", style="cyan")
    table.add_column("Calendar ID", style="green", no_wrap=False)
    table.add_column("Access", style="yellow", justify="center")
    table.add_column("Primary", justify="center")
    
    for cal in calendars:
        name = cal['summary']
        cal_id = cal['id']
        access = cal['access_role']
        primary = "✓" if cal.get('primary') else ""
        
        table.add_row(name, cal_id, access, primary)
    
    console.print(table)
    
    console.print("\n[bold]💡 To configure:[/bold]")
    console.print("1. Copy the Calendar ID for 'Kid's Schedule' (or your custody calendar)")
    console.print("2. Create a .env file in the project root")
    console.print("3. Add: GOOGLE_CALENDAR_CUSTODY_ID=<calendar_id>")
    console.print("\n[dim]Example: GOOGLE_CALENDAR_CUSTODY_ID=abc123@group.calendar.google.com[/dim]\n")


if __name__ == "__main__":
    list_calendars()
