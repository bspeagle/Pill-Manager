#!/usr/bin/env python3
"""Debug custody schedule parsing"""

import sys
from pathlib import Path
from datetime import date, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.integrations.custody_reader import CustodyReader
from rich.console import Console
from rich.table import Table
import os
from dotenv import load_dotenv

# Load env
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

console = Console()

calendar_id = os.getenv('GOOGLE_CALENDAR_CUSTODY_ID')

console.print("\n[bold cyan]🔍 Debugging Custody Schedule[/bold cyan]\n")

custody = CustodyReader(calendar_id)

# Test for November 2025
start = date(2025, 11, 2)
end = date(2025, 12, 2)

console.print(f"[yellow]Period: {start} to {end}[/yellow]\n")

# Get custody blocks
blocks = custody.get_custody_blocks(start, end)

console.print(f"[bold]Found {len(blocks)} custody blocks:[/bold]")
for block in blocks:
    console.print(f"  {block['start'].date()} @ {block['start'].strftime('%I:%M %p')} → {block['end'].date()} @ {block['end'].strftime('%I:%M %p')}")

console.print()

# Get pill days
father_days, mother_days = custody.get_pill_days(start, end)

console.print(f"[bold]Father's Pill Days ({len(father_days)}):[/bold]")
for day in father_days:
    console.print(f"  {day.strftime('%a, %b %d')}")

console.print(f"\n[bold]Mother's Pill Days ({len(mother_days)}):[/bold]")
for day in mother_days[:10]:  # Show first 10
    console.print(f"  {day.strftime('%a, %b %d')}")
if len(mother_days) > 10:
    console.print(f"  ... and {len(mother_days) - 10} more")

console.print(f"\n[bold cyan]Summary:[/bold cyan]")
console.print(f"  Total days: {(end - start).days + 1}")
console.print(f"  Father pills: {len(father_days)}")
console.print(f"  Mother pills: {len(mother_days)}")
console.print(f"  Sum: {len(father_days) + len(mother_days)}")
