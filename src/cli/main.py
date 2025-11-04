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
from src.integrations.calendar_events import PillEventCreator
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box
from rich.prompt import Confirm, Prompt
import argparse

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
        
        # Calculate ACCURATE run-out date using custody schedule
        try:
            accurate_out_date = custody.calculate_mother_run_out_date(
                dist['date'],
                dist['quantity']
            )
            dist['mother_out_date'] = accurate_out_date
            dist['days_until_out'] = (accurate_out_date - date.today()).days
            dist['is_out'] = date.today() >= accurate_out_date
        except Exception as e:
            # Fall back to simple calculation if custody lookup fails
            console.print(f"[yellow]⚠️  Using approximate run-out date (custody lookup failed)[/yellow]\n")
        
        console.print("[bold]👤 Ex-Wife Status[/bold]")
        console.print(f"  Last Distribution: {dist['date'].strftime('%B %d, %Y')} ({dist['quantity']} pills)")
        console.print(f"  Total Distributed: {dist['total_distributed']} pills")
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
                
                # Determine distribution period start date
                # If we have pills with father, use current fill date
                # If we're out, use next refill date
                fill = status['fill']
                refill_date = refill['eligible_date']
                
                if dist['pills_with_father'] > 0:
                    # Still have pills from current fill, calculate from fill date
                    distribution_start = fill['date']
                else:
                    # Out of pills, need to refill first
                    distribution_start = refill_date
                
                distribution_end = distribution_start + timedelta(days=30)
                
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


def sync_calendar(calendar_id: str):
    """Sync pill events to Google Calendar"""
    
    console.print("\n[bold cyan]📅 Syncing Events to Calendar[/bold cyan]\n")
    
    # Initialize components
    db = PillDatabase()
    calc = PillCalculator(db)
    custody = CustodyReader(calendar_id)
    event_creator = PillEventCreator(calendar_id)
    
    # Get current status
    status = calc.get_current_status()
    
    if not status['has_data']:
        console.print("[red]❌ No data found. Please seed database first.[/red]\n")
        return
    
    if 'distribution' not in status:
        console.print("[red]❌ No distribution data found.[/red]\n")
        return
    
    dist = status['distribution']
    refill = status['refill']
    fill = status['fill']
    
    # Calculate ACCURATE run-out date using custody schedule
    try:
        accurate_out_date = custody.calculate_mother_run_out_date(
            dist['date'],
            dist['quantity']
        )
        dist['mother_out_date'] = accurate_out_date
    except Exception as e:
        # Fall back to simple calculation if custody lookup fails
        console.print(f"[yellow]⚠️  Using approximate run-out date (custody lookup failed)[/yellow]\n")
    
    # Calculate next distribution
    try:
        after_date = dist['mother_out_date']
        next_mom_day = custody.get_next_mother_custody_day(after_date)
        
        # Determine distribution period start date
        # If we have pills with father, use current fill date
        # If we're out, use next refill date
        refill_date = refill['eligible_date']
        
        if dist['pills_with_father'] > 0:
            # Still have pills from current fill, calculate from fill date
            distribution_start = fill['date']
        else:
            # Out of pills, need to refill first
            distribution_start = refill_date
        
        distribution_end = distribution_start + timedelta(days=30)
        
        distribution = custody.get_pill_distribution(distribution_start, distribution_end)
        
        next_dist = calc.calculate_next_distribution(
            mother_out_date=dist['mother_out_date'],
            refill_date=refill_date,
            next_mother_custody_day=next_mom_day,
            mother_pills_needed=distribution['mother_pills']
        )
        
    except Exception as e:
        console.print(f"[red]Error calculating distribution: {e}[/red]\n")
        return
    
    # Show summary
    console.print("[bold]Events to create:[/bold]")
    console.print(f"  1. 💊 Ex Out of ADHD Meds - {dist['mother_out_date'].strftime('%B %d, %Y')}")
    console.print(f"  2. 💊 Can Refill ADHD Prescription - {refill_date.strftime('%B %d, %Y')}")
    console.print(f"  3. 💊 Give {next_dist['pills_to_give']} Pills to Ex - {next_dist['distribution_date'].strftime('%B %d, %Y')}")
    console.print()
    
    # Confirm
    if not Confirm.ask("[bold]Create these calendar events?[/bold]", default=True):
        console.print("[yellow]Cancelled[/yellow]\n")
        return
    
    # Create events
    console.print("\n[yellow]Creating events...[/yellow]")
    
    # For the distribution event, show when those specific pills will be used
    # Period starts from her next pill day after receiving them
    next_pill_day_after_dist = custody.get_next_mother_custody_day(next_dist['distribution_date'])
    
    # Calculate when she'll run out of those pills
    pills_run_out = custody.calculate_mother_run_out_date(
        next_pill_day_after_dist,
        next_dist['pills_to_give']
    )
    
    results = event_creator.create_all_events(
        mom_out_date=dist['mother_out_date'],
        refill_date=refill_date,
        distribution_date=next_dist['distribution_date'],
        pills_to_give=next_dist['pills_to_give'],
        period_start=next_pill_day_after_dist,
        period_end=pills_run_out
    )
    
    # Show results
    console.print()
    if results['created']:
        console.print("[bold green]✅ Events Created:[/bold green]")
        for event in results['created']:
            console.print(f"  ✓ {event['summary']} - {event['date'].strftime('%b %d')}")
    
    if results['failed']:
        console.print(f"\n[bold red]❌ Failed to create {len(results['failed'])} events:[/bold red]")
        for error in results['errors']:
            console.print(f"  ✗ {error['type']}: {error['error']}")
    
    if not results['failed']:
        console.print("\n[bold green]🎉 All events synced successfully![/bold green]\n")
    else:
        console.print()


def record_distribution(dist_date: date, quantity: int, notes: str = ""):
    """Record pills given to ex-wife"""
    
    console.print("\n[bold cyan]📝 Recording Distribution[/bold cyan]\n")
    
    # Initialize database
    db = PillDatabase()
    
    # Get latest fill
    latest_fill = db.get_latest_fill()
    if not latest_fill:
        console.print("[red]❌ No fill data found. Please record a fill first.[/red]\n")
        return
    
    fill_id = latest_fill['id']
    
    # Show summary
    console.print("[bold]Distribution Details:[/bold]")
    console.print(f"  Date: {dist_date.strftime('%B %d, %Y')}")
    console.print(f"  Quantity: {quantity} pills")
    console.print(f"  Associated Fill: {latest_fill['fill_date']} ({latest_fill['quantity']} pills)")
    if notes:
        console.print(f"  Notes: {notes}")
    console.print()
    
    # Confirm
    if not Confirm.ask("[bold]Record this distribution?[/bold]", default=True):
        console.print("[yellow]Cancelled[/yellow]\n")
        return
    
    # Record in database
    try:
        dist_id = db.add_distribution(
            distribution_date=dist_date,
            quantity=quantity,
            fill_id=fill_id,
            notes=notes
        )
        
        console.print(f"[green]✅ Distribution recorded (ID: {dist_id})[/green]\n")
        
        # Show updated status
        calc = PillCalculator(db)
        status = calc.get_current_status()
        
        if status['has_data'] and 'distribution' in status:
            dist = status['distribution']
            console.print("[bold]Updated Status:[/bold]")
            console.print(f"  Last Distribution: {dist['date'].strftime('%B %d, %Y')} ({dist['quantity']} pills)")
            console.print(f"  Mother Runs Out: {dist['mother_out_date'].strftime('%B %d, %Y')}")
            console.print(f"  Pills with Father: {dist['pills_with_father']}\n")
        
    except Exception as e:
        console.print(f"[red]❌ Failed to record distribution: {e}[/red]\n")


def main():
    """Main CLI entry point"""
    
    # Load calendar ID from environment
    calendar_id = os.getenv('GOOGLE_CALENDAR_CUSTODY_ID')
    
    if not calendar_id:
        console.print("\n[red]❌ Error: GOOGLE_CALENDAR_CUSTODY_ID not configured in .env file[/red]")
        console.print("[yellow]Run: python scripts/list_calendars.py to find your calendar ID[/yellow]\n")
        return
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Pill Manager CLI')
    parser.add_argument('command', nargs='?', default='status',
                       choices=['status', 'sync-calendar', 'record-distribution'],
                       help='Command to run')
    parser.add_argument('--date', type=str, help='Distribution date (YYYY-MM-DD)')
    parser.add_argument('--quantity', type=int, help='Number of pills')
    parser.add_argument('--notes', type=str, default='', help='Optional notes')
    
    args = parser.parse_args()
    
    try:
        if args.command == 'sync-calendar':
            sync_calendar(calendar_id)
        elif args.command == 'record-distribution':
            # Validate required arguments
            if not args.date or not args.quantity:
                console.print("\n[red]❌ Error: --date and --quantity are required for record-distribution[/red]")
                console.print("\n[bold]Usage:[/bold]")
                console.print("  python src/cli/main.py record-distribution --date YYYY-MM-DD --quantity N [--notes 'text']\n")
                console.print("[bold]Example:[/bold]")
                console.print("  python src/cli/main.py record-distribution --date 2025-10-31 --quantity 3 --notes 'Extra pills for weekend'\n")
                return
            
            # Parse date
            try:
                dist_date = datetime.strptime(args.date, '%Y-%m-%d').date()
            except ValueError:
                console.print(f"\n[red]❌ Invalid date format: {args.date}[/red]")
                console.print("[yellow]Use format: YYYY-MM-DD (e.g., 2025-10-31)[/yellow]\n")
                return
            
            record_distribution(dist_date, args.quantity, args.notes)
        elif args.command == 'status':
            show_status(calendar_id)
    except KeyboardInterrupt:
        console.print("\n[yellow]Cancelled[/yellow]\n")
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]\n")
        import traceback
        console.print(traceback.format_exc())


if __name__ == "__main__":
    main()
