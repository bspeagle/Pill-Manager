#!/usr/bin/env python3
"""
Pill Manager CLI

Main command-line interface for managing ADHD medication distribution.
"""

import sys
import os
from pathlib import Path
from datetime import datetime, date, timedelta
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(env_path)

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.core.database import PillDatabase
from src.core.calculator import PillCalculator
from src.integrations.custody_reader import CustodyReader
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

console = Console()


def show_status(calendar_id: str):
    """Show current pill management status"""
    
    console.print("\n[bold cyan]💊 Pill Manager Status[/bold cyan]\n")
    
    # Initialize components
    db = PillDatabase()
    calc = PillCalculator(db)
    custody = CustodyReader(calendar_id)
    
    # Get current status
    status = calc.get_current_status()
    
    if not status['has_data']:
        console.print("[red]❌ No data found. Please run setup first.[/red]\n")
        return
    
    # Display last fill
    fill = status['fill']
    console.print("[bold]📋 Last Prescription Fill[/bold]")
    console.print(f"  Date: {fill['date'].strftime('%B %d, %Y')} ({fill['days_ago']} days ago)")
    console.print(f"  Quantity: {fill['quantity']} pills")
    console.print(f"  Pharmacy: {fill['pharmacy']}")
    console.print(f"  Rx #: {fill['prescription_number']}\n")
    
    # Display refill status
    refill = status['refill']
    console.print("[bold]🔄 Next Refill Eligible[/bold]")
    console.print(f"  Date: {refill['eligible_date'].strftime('%B %d, %Y')}")
    
    if refill['can_refill']:
        console.print(f"  Status: [green]✅ Can refill NOW![/green]")
    elif refill['days_until'] <= 3:
        console.print(f"  Status: [yellow]⏰ {refill['days_until']} days until eligible[/yellow]")
    else:
        console.print(f"  Status: [dim]⏳ {refill['days_until']} days until eligible[/dim]")
    console.print()
    
    # Display distribution status if exists
    if 'distribution' in status:
        dist = status['distribution']
        console.print("[bold]👤 Ex-Wife Status[/bold]")
        console.print(f"  Last Distribution: {dist['date'].strftime('%B %d, %Y')} ({dist['quantity']} pills)")
        console.print(f"  Runs Out: {dist['mother_out_date'].strftime('%B %d, %Y')}")
        
        if dist['is_out']:
            console.print(f"  Status: [red]🚨 OUT OF PILLS![/red]")
        elif dist['days_until_out'] == 0:
            console.print(f"  Status: [red]⚠️  RUNS OUT TODAY![/red]")
        elif dist['days_until_out'] == 1:
            console.print(f"  Status: [yellow]⚠️  Runs out TOMORROW![/yellow]")
        elif dist['days_until_out'] <= 3:
            console.print(f"  Status: [yellow]⏰ Runs out in {dist['days_until_out']} days[/yellow]")
        else:
            console.print(f"  Status: [green]✓ {dist['days_until_out']} days remaining[/green]")
        
        console.print(f"  Pills with Father: {dist['pills_with_father']}\n")
        
        # Calculate next actions if mother is out or running out soon
        if dist['is_out'] or dist['days_until_out'] <= 2:
            console.print("[bold red]🎯 ACTION REQUIRED[/bold red]\n")
            
            # Calculate next distribution
            try:
                # Find next mother custody day AFTER she runs out
                # Use mother_out_date, not today, because she doesn't need pills until her next custody day
                after_date = dist['mother_out_date']
                next_mom_day = custody.get_next_mother_custody_day(after_date)
                
                # Calculate distribution for next 30 days from refill
                refill_date = refill['eligible_date']
                distribution_start = refill_date
                distribution_end = refill_date + timedelta(days=30)
                
                distribution = custody.get_pill_distribution(distribution_start, distribution_end)
                
                # Calculate next distribution plan
                next_dist = calc.calculate_next_distribution(
                    mother_out_date=dist['mother_out_date'],
                    refill_date=refill_date,
                    next_mother_custody_day=next_mom_day,
                    mother_pills_needed=distribution['mother_pills']
                )
                
                console.print(f"[bold]📅 Next Distribution Plan:[/bold]")
                console.print(f"  Give Pills On: {next_dist['distribution_date'].strftime('%B %d, %Y')}")
                console.print(f"  Quantity: {next_dist['pills_to_give']} pills")
                
                if next_dist['needs_refill_first']:
                    console.print(f"  [yellow]⚠️  Must refill on {refill_date.strftime('%B %d, %Y')} first![/yellow]")
                
                if next_dist['gap_days'] > 0:
                    console.print(f"  [red]🚨 Mother will be out for {next_dist['gap_days']} days![/red]")
                
                console.print(f"\n[dim]{next_dist['notes']}[/dim]\n")
                
                # Show distribution breakdown
                console.print(f"[bold]Distribution Breakdown ({distribution_start.strftime('%b %d')} - {distribution_end.strftime('%b %d')}):[/bold]")
                console.print(f"  Mother: {distribution['mother_pills']} pills")
                console.print(f"  Father: {distribution['father_pills']} pills")
                console.print(f"  Total: {distribution['mother_pills'] + distribution['father_pills']} pills\n")
                
            except Exception as e:
                console.print(f"[red]Error calculating next distribution: {e}[/red]\n")
    else:
        console.print("[yellow]⚠️  No distribution data found[/yellow]\n")


def main():
    """Main CLI entry point"""
    
    # Load calendar ID from environment
    calendar_id = os.getenv('GOOGLE_CALENDAR_CUSTODY_ID')
    
    if not calendar_id:
        console.print("\n[red]❌ Error: GOOGLE_CALENDAR_CUSTODY_ID not configured in .env file[/red]")
        console.print("[yellow]Run: python scripts/list_calendars.py to find your calendar ID[/yellow]\n")
        return
    
    try:
        show_status(calendar_id)
    except KeyboardInterrupt:
        console.print("\n[yellow]Cancelled[/yellow]\n")
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]\n")
        import traceback
        console.print(traceback.format_exc())


if __name__ == "__main__":
    main()
