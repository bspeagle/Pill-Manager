# 🏴‍☠️ PILL TERMINAL 9000 - Web Dashboard

90s hacker-themed web interface for the Pill Manager system.

## 🎮 Features

- **Dashboard**: Real-time status of pills, refills, and distributions
- **Record Fill**: Add new prescription fills
- **Record Distribution**: Log pills given to ex-wife
- **Sync Calendar**: Create Google Calendar events
- **History**: View all past fills and distributions

## 🚀 Quick Start

### 1. Install Flask (if not already installed)

```bash
cd /Users/bspeagle/GIT/pill_manager
source venv/bin/activate
pip install Flask>=3.0.0
```

### 2. Run the Web App

```bash
cd web
python app.py
```

### 3. Access in Browser

Open: **http://localhost:5000**

## 🎨 Design

- **Theme**: 90s terminal hacker aesthetic
- **Colors**: Green phosphor on black (`#00ff00` on `#000000`)
- **Font**: VT323 monospace
- **Effects**: CRT scanlines, screen glow, terminal animations
- **Style**: ASCII art, blinking cursor, matrix vibes

## 📁 Structure

```
web/
├── app.py                  # Flask application
├── static/
│   └── css/
│       └── terminal.css    # 90s hacker theme
└── templates/
    ├── base.html           # Base template with header/nav
    ├── dashboard.html      # Main status dashboard
    ├── new_fill.html       # Record fill form
    ├── new_distribution.html  # Record distribution form
    ├── sync_calendar.html  # Calendar sync page
    └── history.html        # View history
```

## 🛠️ Technical Details

- **Backend**: Flask (Python)
- **Frontend**: HTML/CSS/JavaScript
- **Integration**: Uses existing `src/` modules
- **Database**: Same SQLite database as CLI
- **API**: Google Calendar API for event sync

## ⚓ Beepboop Systems

*A treasure well tracked is never lost!* 🏴‍☠️
