#!/usr/bin/env python3
"""Debug Oct 29 custody"""

import sys
from pathlib import Path
from datetime import date

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.integrations.custody_reader import CustodyReader
from rich.console import Console
import os
from dotenv import load_dotenv

env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

console = Console()
calendar_id = os.getenv('GOOGLE_CALENDAR_CUSTODY_ID')

custody = CustodyReader(calendar_id)

# Check Oct 29 - Nov 5
start = date(2025, 10, 29)
end = date(2025, 11, 5)

father_days, mother_days = custody.get_pill_days(start, end)

console.print("\n[bold cyan]Who has custody Oct 29 - Nov 5?[/bold cyan]\n")

all_days = {}
for day in father_days:
    all_days[day] = "Father"
for day in mother_days:
    all_days[day] = "Mother"

for day in sorted(all_days.keys()):
    parent = all_days[day]
    console.print(f"{day.strftime('%a, %b %d')}: {parent}")

console.print(f"\n[yellow]Mom runs out: Oct 29[/yellow]")
console.print(f"[yellow]Next mom custody day after Oct 29: {custody.get_next_mother_custody_day(date(2025, 10, 29))}[/yellow]")
