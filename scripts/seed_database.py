#!/usr/bin/env python3
"""
Seed Database with Current Data

Initialize database with the current prescription fill and distribution.
"""

import sys
from pathlib import Path
from datetime import date

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.database import PillDatabase
from rich.console import Console

console = Console()


def seed_database():
    """Seed database with current prescription data"""
    
    console.print("\n[bold cyan]🗄️  Seeding Database...[/bold cyan]\n")
    
    # Initialize database
    db = PillDatabase()
    
    # Check if already seeded
    latest_fill = db.get_latest_fill()
    if latest_fill:
        console.print("[yellow]⚠️  Database already has data:[/yellow]")
        console.print(f"  Last fill: {latest_fill['fill_date']}")
        console.print(f"  Quantity: {latest_fill['quantity']}")
        
        from rich.prompt import Confirm
        if not Confirm.ask("\nOverwrite and reseed?", default=False):
            console.print("[red]Cancelled[/red]")
            return
    
    # Add October 8 fill
    console.print("[yellow]Adding prescription fill...[/yellow]")
    fill_id = db.add_fill(
        fill_date=date(2025, 10, 8),
        quantity=30,
        prescription_number="#15013721",
        pharmacy="Publix #1250",
        notes="Methylphenidate ER Tabs 27mg, 30-day supply"
    )
    console.print(f"[green]✓ Fill added (ID: {fill_id})[/green]")
    
    # Add October 13 distribution
    console.print("[yellow]Adding distribution to ex-wife...[/yellow]")
    dist_id = db.add_distribution(
        distribution_date=date(2025, 10, 13),
        quantity=16,
        fill_id=fill_id,
        notes="Gave 16 pills to mom"
    )
    console.print(f"[green]✓ Distribution added (ID: {dist_id})[/green]")
    
    # Verify
    console.print("\n[bold green]✅ Database Seeded Successfully![/bold green]\n")
    
    # Show summary
    console.print("[bold]Current Status:[/bold]")
    fill = db.get_latest_fill()
    dist = db.get_latest_distribution()
    
    console.print(f"  Last Fill: {fill['fill_date']} ({fill['quantity']} pills)")
    console.print(f"  Last Distribution: {dist['distribution_date']} ({dist['quantity']} pills)")
    console.print(f"  Pills with Dad: {fill['quantity'] - dist['quantity']} pills")
    
    # Calculate key dates
    from datetime import datetime, timedelta
    fill_date = datetime.strptime(fill['fill_date'], '%Y-%m-%d').date()
    dist_date = datetime.strptime(dist['distribution_date'], '%Y-%m-%d').date()
    
    refill_date = fill_date + timedelta(days=26)
    mom_out_date = dist_date + timedelta(days=dist['quantity'])
    
    console.print(f"\n[bold]Key Dates:[/bold]")
    console.print(f"  Next Refill Eligible: {refill_date}")
    console.print(f"  Mom Runs Out: {mom_out_date}")
    
    if mom_out_date <= datetime.now().date():
        console.print(f"  [red]⚠️  Mom OUT OF PILLS![/red]")
    elif (mom_out_date - datetime.now().date()).days <= 2:
        console.print(f"  [yellow]⚠️  Mom runs out in {(mom_out_date - datetime.now().date()).days} days![/yellow]")
    
    console.print()


if __name__ == "__main__":
    seed_database()
