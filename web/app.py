#!/usr/bin/env python3
"""
🏴‍☠️ PILL TERMINAL 9000 - Flask Web Application
90s Hacker-Themed Pill Manager Dashboard
"""

import sys
import os
from pathlib import Path
from datetime import date, datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.database import PillDatabase
from src.core.calculator import PillCalculator
from src.integrations.custody_reader import CustodyReader
from src.integrations.calendar_events import PillEventCreator

# Load environment
load_dotenv(Path(__file__).parent.parent / '.env')

app = Flask(__name__)
app.config['SECRET_KEY'] = 'pill-terminal-9000-hax0rz'

# Initialize components
db = PillDatabase()
calc = PillCalculator(db)

def get_calendar_id():
    """Get calendar ID from environment"""
    return os.getenv('GOOGLE_CALENDAR_CUSTODY_ID')


@app.route('/')
def index():
    """Dashboard - Main status view"""
    try:
        calendar_id = get_calendar_id()
        custody = CustodyReader(calendar_id)
        
        # Get current status
        status = calc.get_current_status()
        
        if not status['has_data']:
            return render_template('dashboard.html', error="No data found. Please add a prescription fill first.")
        
        # Calculate accurate run-out date using custody schedule
        next_distribution = None
        if 'distribution' in status:
            dist = status['distribution']
            try:
                accurate_out_date = custody.calculate_mother_run_out_date(
                    dist['date'],
                    dist['quantity']
                )
                dist['mother_out_date'] = accurate_out_date
                dist['days_until_out'] = (accurate_out_date - date.today()).days
                dist['is_out'] = date.today() >= accurate_out_date
            except Exception as e:
                # Use simple calculation as fallback
                pass
            
            # Calculate next distribution info
            try:
                from datetime import timedelta
                refill = status['refill']
                fill = status['fill']
                
                after_date = dist['mother_out_date']
                next_mom_day = custody.get_next_mother_custody_day(after_date)
                refill_date = refill['eligible_date']
                
                # Determine distribution period start date (same logic as CLI)
                # If we have pills with father, use current fill date
                # If we're out, use next refill date
                if dist['pills_with_father'] > 0:
                    distribution_start = fill['date']
                else:
                    distribution_start = refill_date
                
                # Calculate 30-day period from fill date - distribute ALL pills based on custody
                distribution_end = distribution_start + timedelta(days=30)
                distribution = custody.get_pill_distribution(distribution_start, distribution_end)
                
                # Calculate next distribution using same logic as CLI
                next_dist = calc.calculate_next_distribution(
                    mother_out_date=dist['mother_out_date'],
                    refill_date=refill_date,
                    next_mother_custody_day=next_mom_day,
                    mother_pills_needed=distribution['mother_pills']
                )
                
                next_distribution = {
                    'date': next_dist['distribution_date'],
                    'quantity': next_dist['pills_to_give'],
                    'days_until': (next_dist['distribution_date'] - date.today()).days
                }
            except:
                pass
        
        return render_template('dashboard.html', status=status, next_distribution=next_distribution)
    
    except Exception as e:
        return render_template('dashboard.html', error=f"System Error: {str(e)}")


@app.route('/fill/new', methods=['GET', 'POST'])
def new_fill():
    """Record a new prescription fill"""
    if request.method == 'POST':
        try:
            fill_date = datetime.strptime(request.form['fill_date'], '%Y-%m-%d').date()
            quantity = int(request.form['quantity'])
            pharmacy = request.form['pharmacy']
            rx_number = request.form['rx_number']
            
            fill_id = db.add_fill(
                fill_date=fill_date,
                quantity=quantity,
                pharmacy=pharmacy,
                prescription_number=rx_number
            )
            
            return redirect(url_for('index'))
        
        except Exception as e:
            default_pharmacy = os.getenv('DEFAULT_PHARMACY', '')
            return render_template('new_fill.html', error=f"Error: {str(e)}", 
                                 today=date.today().isoformat(), 
                                 default_pharmacy=default_pharmacy)
    
    # GET request - show form with defaults
    default_pharmacy = os.getenv('DEFAULT_PHARMACY', '')
    return render_template('new_fill.html', 
                         today=date.today().isoformat(),
                         default_pharmacy=default_pharmacy)


@app.route('/distribution/new', methods=['GET', 'POST'])
def new_distribution():
    """Record a distribution to ex-wife"""
    if request.method == 'POST':
        try:
            dist_date = datetime.strptime(request.form['dist_date'], '%Y-%m-%d').date()
            quantity = int(request.form['quantity'])
            notes = request.form.get('notes', '')
            fill_id = int(request.form['fill_id'])
            
            dist_id = db.add_distribution(
                distribution_date=dist_date,
                quantity=quantity,
                fill_id=fill_id,
                notes=notes
            )
            
            return redirect(url_for('index'))
        
        except Exception as e:
            fills = db.get_fill_history(limit=10)
            return render_template('new_distribution.html', error=f"Error: {str(e)}", 
                                 today=date.today().isoformat(), fills=fills)
    
    # GET request - show form with defaults
    try:
        calendar_id = get_calendar_id()
        custody = CustodyReader(calendar_id)
        fills = db.get_fill_history(limit=10)
        status = calc.get_current_status()
        
        # Calculate suggested quantity for current fill
        suggested_quantity = None
        suggested_notes = None
        
        if status['has_data'] and 'distribution' in status:
            dist = status['distribution']
            refill = status['refill']
            fill = status['fill']
            
            # Calculate next distribution
            from datetime import timedelta
            
            try:
                accurate_out_date = custody.calculate_mother_run_out_date(dist['date'], dist['quantity'])
                after_date = accurate_out_date
            except:
                after_date = dist['mother_out_date']
            
            next_mom_day = custody.get_next_mother_custody_day(after_date)
            refill_date = refill['eligible_date']
            
            # Determine distribution period start date (same logic as CLI)
            # If we have pills with father, use current fill date
            # If we're out, use next refill date
            if dist['pills_with_father'] > 0:
                distribution_start = fill['date']
            else:
                distribution_start = refill_date
            
            # Calculate 30-day period from fill date - distribute ALL pills based on custody
            distribution_end = distribution_start + timedelta(days=30)
            distribution = custody.get_pill_distribution(distribution_start, distribution_end)
            
            # Calculate next distribution
            next_dist = calc.calculate_next_distribution(
                mother_out_date=after_date,
                refill_date=refill_date,
                next_mother_custody_day=next_mom_day,
                mother_pills_needed=distribution['mother_pills']
            )
            
            suggested_quantity = next_dist['pills_to_give']
            
            # Calculate period for notes - from first pill day through when those pills run out
            next_pill_day = custody.get_next_mother_custody_day(next_dist['distribution_date'])
            pills_run_out = custody.calculate_mother_run_out_date(next_pill_day, suggested_quantity)
            suggested_notes = f"Distribution for {next_pill_day.strftime('%b %d')} - {pills_run_out.strftime('%b %d, %Y')} period"
        
        return render_template('new_distribution.html', 
                             today=date.today().isoformat(),
                             fills=fills,
                             suggested_quantity=suggested_quantity,
                             suggested_notes=suggested_notes)
    
    except Exception as e:
        fills = db.get_fill_history(limit=10)
        return render_template('new_distribution.html', 
                             today=date.today().isoformat(),
                             fills=fills,
                             error=f"Error calculating suggestion: {str(e)}")


@app.route('/calendar/sync', methods=['GET', 'POST'])
def sync_calendar():
    """Sync calendar events"""
    if request.method == 'POST':
        try:
            calendar_id = get_calendar_id()
            if not calendar_id:
                return jsonify({'success': False, 'error': 'Calendar ID not configured'})
            
            custody = CustodyReader(calendar_id)
            event_creator = PillEventCreator(calendar_id)
            
            # Get current status
            status = calc.get_current_status()
            
            if not status['has_data'] or 'distribution' not in status:
                return jsonify({'success': False, 'error': 'No distribution data found'})
            
            dist = status['distribution']
            refill = status['refill']
            fill = status['fill']
            
            # Calculate accurate run-out date
            try:
                accurate_out_date = custody.calculate_mother_run_out_date(
                    dist['date'],
                    dist['quantity']
                )
                dist['mother_out_date'] = accurate_out_date
            except:
                pass
            
            # Calculate next distribution
            from datetime import timedelta
            
            after_date = dist['mother_out_date']
            next_mom_day = custody.get_next_mother_custody_day(after_date)
            
            refill_date = refill['eligible_date']
            
            if dist['pills_with_father'] > 0:
                distribution_start = fill['date']
            else:
                distribution_start = refill_date
            
            distribution_end = distribution_start + timedelta(days=30)
            distribution = custody.get_pill_distribution(distribution_start, distribution_end)
            
            next_dist = calc.calculate_next_distribution(
                mother_out_date=dist['mother_out_date'],
                refill_date=refill_date,
                next_mother_custody_day=next_mom_day,
                mother_pills_needed=distribution['mother_pills']
            )
            
            # Calculate period for distribution event
            next_pill_day_after_dist = custody.get_next_mother_custody_day(next_dist['distribution_date'])
            pills_run_out = custody.calculate_mother_run_out_date(
                next_pill_day_after_dist,
                next_dist['pills_to_give']
            )
            
            # Create events
            results = event_creator.create_all_events(
                mom_out_date=dist['mother_out_date'],
                refill_date=refill_date,
                distribution_date=next_dist['distribution_date'],
                pills_to_give=next_dist['pills_to_give'],
                period_start=next_pill_day_after_dist,
                period_end=pills_run_out
            )
            
            return jsonify({
                'success': True,
                'created': [{'summary': e['summary'], 'date': e['date'].isoformat()} for e in results.get('created', [])]
            })
        
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})
    
    # GET request - show confirmation page
    return render_template('sync_calendar.html')


@app.route('/history')
def history():
    """View fill and distribution history"""
    try:
        fills = db.get_fill_history(limit=50)
        distributions = db.get_distribution_history(limit=50)
        
        return render_template('history.html', fills=fills, distributions=distributions)
    
    except Exception as e:
        return render_template('history.html', error=f"Error: {str(e)}")


@app.route('/fill/edit/<int:fill_id>', methods=['GET', 'POST'])
def edit_fill(fill_id):
    """Edit an existing prescription fill"""
    if request.method == 'POST':
        try:
            fill_date = datetime.strptime(request.form['fill_date'], '%Y-%m-%d').date()
            quantity = int(request.form['quantity'])
            pharmacy = request.form['pharmacy']
            rx_number = request.form['rx_number']
            
            db.update_fill(
                fill_id=fill_id,
                fill_date=fill_date,
                quantity=quantity,
                pharmacy=pharmacy,
                prescription_number=rx_number
            )
            
            return redirect(url_for('history'))
        
        except Exception as e:
            fill = db.get_fill_by_id(fill_id)
            default_pharmacy = os.getenv('DEFAULT_PHARMACY', '')
            return render_template('edit_fill.html', fill=fill, error=f"Error: {str(e)}", 
                                 default_pharmacy=default_pharmacy)
    
    # GET request - show form with current data
    try:
        fill = db.get_fill_by_id(fill_id)
        if not fill:
            return redirect(url_for('history'))
        
        default_pharmacy = os.getenv('DEFAULT_PHARMACY', '')
        return render_template('edit_fill.html', fill=fill, default_pharmacy=default_pharmacy)
    
    except Exception as e:
        return redirect(url_for('history'))


@app.route('/distribution/edit/<int:dist_id>', methods=['GET', 'POST'])
def edit_distribution(dist_id):
    """Edit an existing distribution"""
    if request.method == 'POST':
        try:
            dist_date = datetime.strptime(request.form['dist_date'], '%Y-%m-%d').date()
            quantity = int(request.form['quantity'])
            notes = request.form.get('notes', '')
            fill_id = int(request.form['fill_id'])
            
            db.update_distribution(
                distribution_id=dist_id,
                distribution_date=dist_date,
                quantity=quantity,
                fill_id=fill_id,
                notes=notes
            )
            
            return redirect(url_for('history'))
        
        except Exception as e:
            distribution = db.get_distribution_by_id(dist_id)
            fills = db.get_fill_history(limit=10)
            return render_template('edit_distribution.html', distribution=distribution, 
                                 fills=fills, error=f"Error: {str(e)}")
    
    # GET request - show form with current data
    try:
        distribution = db.get_distribution_by_id(dist_id)
        if not distribution:
            return redirect(url_for('history'))
        
        fills = db.get_fill_history(limit=10)
        return render_template('edit_distribution.html', distribution=distribution, fills=fills)
    
    except Exception as e:
        return redirect(url_for('history'))


@app.route('/api/status')
def api_status():
    """API endpoint for current status (for AJAX updates)"""
    try:
        status = calc.get_current_status()
        
        # Convert dates to ISO format for JSON
        if status['has_data']:
            status['fill']['date'] = status['fill']['date'].isoformat()
            status['refill']['eligible_date'] = status['refill']['eligible_date'].isoformat()
            
            if 'distribution' in status:
                status['distribution']['date'] = status['distribution']['date'].isoformat()
                status['distribution']['mother_out_date'] = status['distribution']['mother_out_date'].isoformat()
        
        return jsonify(status)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    print("🏴‍☠️ PILL TERMINAL 9000 BOOTING UP...")
    print("💚 System: ONLINE")
    print("🌐 Access: http://localhost:5001")
    print("⚡ Press CTRL+C to terminate")
    app.run(debug=True, host='0.0.0.0', port=5001)
