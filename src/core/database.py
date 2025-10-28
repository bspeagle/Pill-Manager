"""
Database Operations for Pill Manager

Handles SQLite database operations for tracking prescription fills,
distributions to ex-wife, and calendar event synchronization.
"""

import sqlite3
from pathlib import Path
from datetime import datetime, date
from typing import Optional, Dict, List, Any
from contextlib import contextmanager


class DatabaseError(Exception):
    """Custom exception for database errors"""
    pass


class PillDatabase:
    """SQLite database manager for pill tracking"""
    
    def __init__(self, db_path: str = "data/pill_manager.db"):
        """
        Initialize database connection.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize_database()
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise DatabaseError(f"Database operation failed: {e}")
        finally:
            conn.close()
    
    def _initialize_database(self):
        """Create database tables if they don't exist"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Prescription fills table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS prescription_fills (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fill_date DATE NOT NULL,
                    quantity INTEGER NOT NULL,
                    prescription_number TEXT,
                    pharmacy TEXT,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Distributions to ex-wife table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS distributions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    distribution_date DATE NOT NULL,
                    quantity INTEGER NOT NULL,
                    fill_id INTEGER,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (fill_id) REFERENCES prescription_fills(id)
                )
            """)
            
            # Settings table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Calendar events tracking (to avoid duplicates)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS calendar_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    event_date DATE NOT NULL,
                    gcal_event_id TEXT,
                    related_fill_id INTEGER,
                    related_distribution_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (related_fill_id) REFERENCES prescription_fills(id),
                    FOREIGN KEY (related_distribution_id) REFERENCES distributions(id)
                )
            """)
            
            conn.commit()
    
    # ============================================
    # Prescription Fill Operations
    # ============================================
    
    def add_fill(
        self,
        fill_date: date,
        quantity: int,
        prescription_number: Optional[str] = None,
        pharmacy: Optional[str] = None,
        notes: Optional[str] = None
    ) -> int:
        """
        Record a new prescription fill.
        
        Args:
            fill_date: Date prescription was filled
            quantity: Number of pills
            prescription_number: Prescription/Rx number
            pharmacy: Pharmacy name
            notes: Additional notes
            
        Returns:
            ID of inserted fill record
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO prescription_fills 
                (fill_date, quantity, prescription_number, pharmacy, notes)
                VALUES (?, ?, ?, ?, ?)
            """, (fill_date, quantity, prescription_number, pharmacy, notes))
            return cursor.lastrowid
    
    def get_latest_fill(self) -> Optional[Dict[str, Any]]:
        """
        Get the most recent prescription fill.
        
        Returns:
            Dictionary with fill data or None if no fills exist
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM prescription_fills
                ORDER BY fill_date DESC, id DESC
                LIMIT 1
            """)
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_fill_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get prescription fill history.
        
        Args:
            limit: Maximum number of records to return
            
        Returns:
            List of fill records
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM prescription_fills
                ORDER BY fill_date DESC, id DESC
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]
    
    # ============================================
    # Distribution Operations
    # ============================================
    
    def add_distribution(
        self,
        distribution_date: date,
        quantity: int,
        fill_id: Optional[int] = None,
        notes: Optional[str] = None
    ) -> int:
        """
        Record pills given to ex-wife.
        
        Args:
            distribution_date: Date pills were given
            quantity: Number of pills given
            fill_id: Associated fill record ID
            notes: Additional notes
            
        Returns:
            ID of inserted distribution record
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO distributions 
                (distribution_date, quantity, fill_id, notes)
                VALUES (?, ?, ?, ?)
            """, (distribution_date, quantity, fill_id, notes))
            return cursor.lastrowid
    
    def get_latest_distribution(self) -> Optional[Dict[str, Any]]:
        """
        Get the most recent distribution to ex-wife.
        
        Returns:
            Dictionary with distribution data or None if no distributions exist
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM distributions
                ORDER BY distribution_date DESC, id DESC
                LIMIT 1
            """)
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_distribution_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get distribution history.
        
        Args:
            limit: Maximum number of records to return
            
        Returns:
            List of distribution records
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT d.*, pf.fill_date, pf.pharmacy
                FROM distributions d
                LEFT JOIN prescription_fills pf ON d.fill_id = pf.id
                ORDER BY d.distribution_date DESC, d.id DESC
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]
    
    # ============================================
    # Calendar Event Tracking
    # ============================================
    
    def add_calendar_event(
        self,
        event_type: str,
        event_date: date,
        gcal_event_id: Optional[str] = None,
        related_fill_id: Optional[int] = None,
        related_distribution_id: Optional[int] = None
    ) -> int:
        """
        Track a calendar event to avoid duplicates.
        
        Args:
            event_type: Type of event ('ex_out', 'refill_eligible', 'distribution_due')
            event_date: Date of the event
            gcal_event_id: Google Calendar event ID
            related_fill_id: Associated fill record
            related_distribution_id: Associated distribution record
            
        Returns:
            ID of inserted calendar event record
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO calendar_events 
                (event_type, event_date, gcal_event_id, related_fill_id, related_distribution_id)
                VALUES (?, ?, ?, ?, ?)
            """, (event_type, event_date, gcal_event_id, related_fill_id, related_distribution_id))
            return cursor.lastrowid
    
    def get_calendar_events(
        self,
        event_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get tracked calendar events.
        
        Args:
            event_type: Filter by event type (optional)
            
        Returns:
            List of calendar event records
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if event_type:
                cursor.execute("""
                    SELECT * FROM calendar_events
                    WHERE event_type = ?
                    ORDER BY event_date DESC
                """, (event_type,))
            else:
                cursor.execute("""
                    SELECT * FROM calendar_events
                    ORDER BY event_date DESC
                """)
            return [dict(row) for row in cursor.fetchall()]
    
    # ============================================
    # Settings Operations
    # ============================================
    
    def set_setting(self, key: str, value: str):
        """
        Set a configuration setting.
        
        Args:
            key: Setting key
            value: Setting value
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO settings (key, value, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            """, (key, value))
    
    def get_setting(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get a configuration setting.
        
        Args:
            key: Setting key
            default: Default value if not found
            
        Returns:
            Setting value or default
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT value FROM settings WHERE key = ?
            """, (key,))
            row = cursor.fetchone()
            return row['value'] if row else default
