# Contributing to Pill Manager 🏴‍☠️

First off, thank you for considering contributing to Pill Manager! This tool helps families manage complex medication schedules, and your contribution could make a real difference.

## 🎯 Code of Conduct

Be respectful, inclusive, and constructive. We're all here to help families manage medication safely.

## 🚀 How to Contribute

### Reporting Bugs 🐛

**Before submitting:**
- Check if the issue already exists
- Verify you're using the latest version
- Test with a fresh virtual environment

**Bug Report Should Include:**
- Clear description of the issue
- Steps to reproduce
- Expected vs actual behavior
- Python version and OS
- Relevant log output (sanitize any personal info!)

### Suggesting Features ✨

We love new ideas! Open an issue with:
- Clear description of the feature
- Use case / problem it solves
- Example usage (code or CLI commands)
- Potential implementation approach (optional)

### Pull Requests 🔀

**Before Starting:**
1. Open an issue to discuss significant changes
2. Fork the repository
3. Create a feature branch (`feature/amazing-feature`)

**Development Workflow:**

```bash
# Clone your fork
git clone https://github.com/your-username/pill_manager.git
cd pill_manager

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create feature branch
git checkout -b feature/amazing-feature

# Make your changes
# ... code code code ...

# Run tests (when implemented)
pytest tests/

# Commit with clear messages
git commit -m "feat: Add amazing feature"

# Push to your fork
git push origin feature/amazing-feature

# Open Pull Request on GitHub
```

## 📐 Code Standards

### File Size Limits
- **Maximum 300 lines per file** (excluding config files like Terraform)
- If a file exceeds 300 lines, refactor into modules

### Code Style
- Follow PEP 8 guidelines
- Use type hints where appropriate
- Document functions with clear docstrings
- Keep functions focused (single responsibility)

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: Add new command
fix: Correct calculation bug
docs: Update README
chore: Clean up scripts
test: Add calculator tests
refactor: Simplify custody logic
```

**Examples:**
```bash
git commit -m "feat: Add record-fill command for new prescriptions"
git commit -m "fix: Sum all distributions instead of just latest"
git commit -m "docs: Add troubleshooting section to README"
```

### Documentation

- Update README.md for user-facing changes
- Add docstrings for new functions/classes
- Include inline comments for complex logic
- Update PROGRESS.md if adding major features

### Testing

- Add tests for new features
- Ensure existing tests pass
- Test edge cases (holidays, weekend handoffs, etc.)
- Use `freezegun` for date-dependent tests

## 🏗️ Project Structure

```
src/
├── core/           # Business logic (database, calculator)
├── integrations/   # External services (Google Calendar)
└── cli/            # User interface (commands, output)

scripts/            # Utility scripts (setup, helpers)
tests/              # Test suite (coming soon!)
docs/               # Documentation and templates
```

**Guidelines:**
- `core/` = No external dependencies (except database)
- `integrations/` = Interface with external APIs
- `cli/` = User interaction only, delegate logic to core

## 🔒 Security & Privacy

**NEVER commit:**
- Database files (`.db`, `.sqlite`)
- Calendar exports (`.json` with events)
- API credentials (`token.json`, `credentials.json`)
- Personal data (names, dates, addresses)
- `.env` files

**If you accidentally commit sensitive data:**
1. Notify maintainers immediately
2. Follow git history rewrite procedure
3. Rotate any exposed credentials

## 🧪 Testing

### Manual Testing Checklist

Before submitting a PR, test:

- [ ] `status` command with real data
- [ ] `record-distribution` with various dates
- [ ] `sync-calendar` creates events correctly
- [ ] Database calculations sum distributions properly
- [ ] Custody parsing handles variants ("Brian", "Brian/Holiday")
- [ ] Date math handles month boundaries
- [ ] CLI handles invalid input gracefully

### Automated Tests (Coming Soon!)

We plan to add:
- Unit tests for calculator logic
- Integration tests for calendar operations
- Edge case tests (holidays, gaps, etc.)

## 📝 Documentation

### README Updates

Update README.md when adding:
- New commands
- New configuration options
- New dependencies
- Breaking changes

### Code Comments

```python
# Good: Explains WHY
# Distribution date is day before pill day because custody 
# pickup happens evening before morning pill

# Bad: Explains WHAT (code already shows this)
# Subtract 1 from date
```

## 🎯 Priority Areas

**High Priority:**
- `record-fill` command
- `history` command
- Unit tests
- Error handling improvements

**Medium Priority:**
- Database backup/restore
- Event cleanup (delete old events)
- Multi-child support

**Low Priority:**
- Web UI
- Mobile app
- SMS notifications

## 🙏 Recognition

Contributors will be:
- Listed in CONTRIBUTORS.md (coming soon!)
- Credited in release notes
- Appreciated forever! 🏴‍☠️

## 💬 Questions?

- Open an issue for questions
- Tag with `question` label
- We're friendly pirates, don't be shy! ⚓

---

**Thank you for helping families manage medication safely!** 💊

*"Many hands make light work!" - Pirate Proverb* 🏴‍☠️
