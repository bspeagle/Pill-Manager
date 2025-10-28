"""
Pill Distribution Calculator

Calculates refill dates, distribution dates, and quantities based on:
- Georgia Schedule II laws (no refills)
- Aetna insurance 85% rule (refill after 26 days for 30-day supply)
- Custody schedule from calendar
"""

from datetime import date, timedelta
from typing import Dict, Optional
from .database import PillDatabase


class PillCalculator:
    """Calculates pill distribution and refill dates"""
    
    # Aetna insurance allows refill after 85% of supply used
    REFILL_THRESHOLD_PERCENTAGE = 0.85
    
    def __init__(self, db: PillDatabase):
        """
        Initialize calculator.
        
        Args:
            db: Database instance
        """
        self.db = db
    
    def calculate_refill_date(
        self,
        fill_date: date,
        supply_days: int = 30
    ) -> date:
        """
        Calculate next eligible refill date (Aetna 85% rule).
        
        Args:
            fill_date: Date of last fill
            supply_days: Supply days (default 30)
        
        Returns:
            Earliest date can refill (85% threshold)
        """
        days_until_refill = int(supply_days * self.REFILL_THRESHOLD_PERCENTAGE)
        return fill_date + timedelta(days=days_until_refill)
    
    def calculate_mother_out_date(
        self,
        distribution_date: date,
        pills_given: int
    ) -> date:
        """
        Calculate when mother runs out of pills.
        
        Args:
            distribution_date: Date pills were given
            pills_given: Number of pills given
        
        Returns:
            Date mother runs out (last pill day + 1)
        """
        return distribution_date + timedelta(days=pills_given)
    
    def get_current_status(self) -> Dict:
        """
        Get current prescription and distribution status.
        
        Returns:
            Dictionary with current status details
        """
        latest_fill = self.db.get_latest_fill()
        latest_dist = self.db.get_latest_distribution()
        
        if not latest_fill:
            return {
                'has_data': False,
                'error': 'No prescription fill data found'
            }
        
        # Parse dates
        from datetime import datetime
        fill_date = datetime.strptime(latest_fill['fill_date'], '%Y-%m-%d').date()
        fill_quantity = latest_fill['quantity']
        
        # Calculate refill date
        refill_date = self.calculate_refill_date(fill_date, fill_quantity)
        days_until_refill = (refill_date - date.today()).days
        can_refill = date.today() >= refill_date
        
        status = {
            'has_data': True,
            'fill': {
                'date': fill_date,
                'quantity': fill_quantity,
                'pharmacy': latest_fill.get('pharmacy'),
                'prescription_number': latest_fill.get('prescription_number'),
                'days_ago': (date.today() - fill_date).days
            },
            'refill': {
                'eligible_date': refill_date,
                'days_until': days_until_refill,
                'can_refill': can_refill
            }
        }
        
        # Add distribution info if exists
        if latest_dist:
            dist_date = datetime.strptime(latest_dist['distribution_date'], '%Y-%m-%d').date()
            dist_quantity = latest_dist['quantity']
            
            mother_out_date = self.calculate_mother_out_date(dist_date, dist_quantity)
            days_until_out = (mother_out_date - date.today()).days
            is_out = date.today() >= mother_out_date
            
            # Sum ALL distributions for this fill, not just the latest
            fill_id = latest_fill['id']
            all_distributions = self.db.get_distribution_history(limit=100)  # Get all
            total_distributed = sum(
                d['quantity'] for d in all_distributions 
                if d.get('fill_id') == fill_id
            )
            
            pills_with_father = fill_quantity - total_distributed
            
            status['distribution'] = {
                'date': dist_date,
                'quantity': dist_quantity,
                'total_distributed': total_distributed,
                'days_ago': (date.today() - dist_date).days,
                'mother_out_date': mother_out_date,
                'days_until_out': days_until_out,
                'is_out': is_out,
                'pills_with_father': pills_with_father
            }
        
        return status
    
    def calculate_next_distribution(
        self,
        mother_out_date: date,
        refill_date: date,
        next_mother_custody_day: date,
        mother_pills_needed: int
    ) -> Dict:
        """
        Calculate when to give mother next batch of pills.
        
        Args:
            mother_out_date: When mother runs out
            refill_date: When can get new prescription
            next_mother_custody_day: Next day mother needs to give a pill
            mother_pills_needed: Number of pills mother needs for period
        
        Returns:
            Dictionary with distribution plan
        """
        # Distribution happens the day BEFORE her next pill day
        # (She picks up kids the evening before, gets pills then)
        distribution_date = next_mother_custody_day - timedelta(days=1)
        
        # Check if we need to refill first
        needs_refill_first = refill_date > mother_out_date
        
        # Warning if she'll be out before we can refill
        gap_days = 0
        if needs_refill_first and distribution_date > refill_date:
            gap_days = (distribution_date - mother_out_date).days
        
        return {
            'distribution_date': distribution_date,
            'pills_to_give': mother_pills_needed,
            'mother_out_date': mother_out_date,
            'refill_date': refill_date,
            'needs_refill_first': needs_refill_first,
            'gap_days': gap_days,
            'action_required': date.today() >= mother_out_date,
            'notes': self._generate_distribution_notes(
                distribution_date,
                mother_pills_needed,
                gap_days,
                needs_refill_first
            )
        }
    
    def _generate_distribution_notes(
        self,
        distribution_date: date,
        pills: int,
        gap_days: int,
        needs_refill: bool
    ) -> str:
        """Generate human-readable notes for distribution"""
        notes = f"Give {pills} pills to mother on {distribution_date.strftime('%m/%d/%Y')}"
        
        if gap_days > 0:
            notes += f"\n⚠️  WARNING: Mother will be without pills for {gap_days} days!"
        
        if needs_refill:
            notes += "\n📋 Refill prescription before distribution"
        
        return notes
