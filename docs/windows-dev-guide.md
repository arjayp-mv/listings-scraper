# Windows Development Guide: Python Server & Playwright MCP

## Purpose
This guide teaches Claude Code instances how to properly start Python servers and use Playwright MCP for testing on Windows. It covers common pitfalls with Windows bash commands and provides working patterns.

---

## Table of Contents
1. [Critical Windows Bash Rules](#1-critical-windows-bash-rules)
2. [Starting the Python Server](#2-starting-the-python-server)
3. [Stopping Python Processes](#3-stopping-python-processes)
4. [Playwright MCP Usage](#4-playwright-mcp-usage)
5. [Common Errors and Fixes](#5-common-errors-and-fixes)
6. [Complete Testing Workflow](#6-complete-testing-workflow)
7. [Quick Reference Commands](#7-quick-reference-commands)

---

## 1. Critical Windows Bash Rules

### NEVER Use These Unix Commands on Windows
```bash
# WRONG - These will fail on Windows
pkill python
killall python
kill -9 $(pgrep python)
lsof -i :8004
ps aux | grep python
```

### ALWAYS Use PowerShell Commands
Windows uses PowerShell, not bash. The Bash tool runs PowerShell commands.

```powershell
# CORRECT - Use PowerShell syntax
Get-Process | Where-Object {$_.ProcessName -like "*python*"}
Stop-Process -Name python -Force
netstat -ano | findstr ":8004"
```

### Path Separators
```bash
# WRONG - Unix paths
cd /home/user/project
python ./src/main.py

# CORRECT - Windows paths (use backslashes or forward slashes work too)
cd C:\Users\Arjay\Downloads\listings-workflow
python main.py
```

### Quoting Rules
```bash
# WRONG - Single quotes in PowerShell for variable expansion
Get-Process | Where-Object {$_.ProcessName -like '*python*'}

# CORRECT - Double quotes for patterns with wildcards
Get-Process | Where-Object {$_.ProcessName -like "*python*"}
```

---

## 2. Starting the Python Server

### Prerequisites Check
Before starting the server, verify:
1. Python is installed and in PATH
2. MySQL (XAMPP) is running
3. Virtual environment is activated (if using one)
4. Required packages are installed

### Step 1: Check if Port is Already in Use
```powershell
netstat -ano | findstr ":8004"
```

If output shows a process using port 8004, stop it first (see Section 3).

### Step 2: Navigate to Project Directory
```powershell
cd C:\Users\Arjay\Downloads\listings-workflow
```

### Step 3: Start the Server (Background)
```powershell
# Start server in background - THIS IS THE RECOMMENDED WAY
python main.py
```

**IMPORTANT:** Use `run_in_background: true` parameter when calling the Bash tool:
```json
{
  "command": "cd C:\\Users\\Arjay\\Downloads\\listings-workflow && python main.py",
  "run_in_background": true,
  "description": "Start FastAPI server on port 8004"
}
```

### Step 4: Verify Server is Running
Wait 3-5 seconds, then check:
```powershell
netstat -ano | findstr ":8004"
```

Or use Playwright to navigate:
```
mcp__playwright__browser_navigate to http://localhost:8004
```

### Server Configuration
The server runs on these defaults (from `config/settings.py`):
- **Host:** 0.0.0.0
- **Port:** 8004
- **Debug/Reload:** True (auto-restarts on code changes)

---

## 3. Stopping Python Processes

### Method 1: Stop All Python Processes (Recommended)
```powershell
Get-Process | Where-Object {$_.ProcessName -like "*python*"} | Stop-Process -Force
```

### Method 2: Find and Stop by Port
```powershell
# Step 1: Find the PID using port 8004
netstat -ano | findstr ":8004"

# Output example: TCP 0.0.0.0:8004 0.0.0.0:0 LISTENING 12345
# The last number (12345) is the PID

# Step 2: Stop that specific process
Stop-Process -Id 12345 -Force
```

### Method 3: List Python Processes First
```powershell
# See what's running before stopping
Get-Process | Where-Object {$_.ProcessName -like "*python*"} | Select-Object Id, ProcessName, StartTime
```

### Method 4: Using taskkill (Alternative)
```powershell
taskkill /F /IM python.exe
```

---

## 4. Playwright MCP Usage

### Available Playwright MCP Tools
The Playwright MCP provides these tools for browser automation:

| Tool | Purpose |
|------|---------|
| `mcp__playwright__browser_navigate` | Navigate to a URL |
| `mcp__playwright__browser_snapshot` | Get accessibility snapshot (PREFERRED over screenshot) |
| `mcp__playwright__browser_click` | Click on elements |
| `mcp__playwright__browser_type` | Type text into inputs |
| `mcp__playwright__browser_wait_for` | Wait for text/element/time |
| `mcp__playwright__browser_take_screenshot` | Take screenshot |
| `mcp__playwright__browser_close` | Close the browser |

### Basic Navigation
```json
{
  "tool": "mcp__playwright__browser_navigate",
  "arguments": {
    "url": "http://localhost:8004"
  }
}
```

### Taking Snapshots (Preferred Method)
Snapshots provide an accessibility tree that's better for understanding page structure:
```json
{
  "tool": "mcp__playwright__browser_snapshot",
  "arguments": {}
}
```

### Clicking Elements
After getting a snapshot, use the `ref` from the snapshot to click:
```json
{
  "tool": "mcp__playwright__browser_click",
  "arguments": {
    "element": "Upload CSV button",
    "ref": "button[data-testid='upload-btn']"
  }
}
```

### Typing Text
```json
{
  "tool": "mcp__playwright__browser_type",
  "arguments": {
    "element": "Job name input field",
    "ref": "input#job-name",
    "text": "Test Job 1",
    "submit": false
  }
}
```

### Waiting for Elements
```json
{
  "tool": "mcp__playwright__browser_wait_for",
  "arguments": {
    "text": "Job created successfully"
  }
}
```

### Taking Screenshots
```json
{
  "tool": "mcp__playwright__browser_take_screenshot",
  "arguments": {
    "filename": "test-screenshot.png",
    "fullPage": true
  }
}
```

### Closing Browser
Always close the browser when done:
```json
{
  "tool": "mcp__playwright__browser_close",
  "arguments": {}
}
```

---

## 5. Common Errors and Fixes

### Error: "Address already in use" / Port 8004 in use
**Cause:** Previous Python process still running
**Fix:**
```powershell
# Find and kill the process
Get-Process | Where-Object {$_.ProcessName -like "*python*"} | Stop-Process -Force

# Verify port is free
netstat -ano | findstr ":8004"

# Should return nothing - then start server
```

### Error: "Browser not installed" (Playwright)
**Cause:** Playwright browsers not installed
**Fix:** Use the browser_install tool:
```json
{
  "tool": "mcp__playwright__browser_install",
  "arguments": {}
}
```

### Error: "Connection refused" when navigating
**Cause:** Server not running or not ready yet
**Fix:**
1. Check if server is running: `netstat -ano | findstr ":8004"`
2. Wait 5 seconds after starting server before navigating
3. Check server logs for startup errors

### Error: Command not found (bash commands)
**Cause:** Using Unix commands on Windows
**Fix:** Use PowerShell equivalents (see Section 1)

### Error: "python is not recognized"
**Cause:** Python not in PATH
**Fix:**
```powershell
# Try with full path
C:\Python311\python.exe main.py

# Or check where Python is installed
where python
```

### Error: Module not found
**Cause:** Dependencies not installed
**Fix:**
```powershell
pip install -r requirements.txt
```

### Error: Snapshot returns empty or minimal content
**Cause:** Page not fully loaded
**Fix:** Wait for page load:
```json
{
  "tool": "mcp__playwright__browser_wait_for",
  "arguments": {
    "time": 3
  }
}
```

### Error: Click fails - element not found
**Cause:** Using wrong ref or element not visible
**Fix:**
1. Take a fresh snapshot
2. Use the exact `ref` from the snapshot
3. Ensure element is visible (not hidden by modal, scroll, etc.)

---

## 6. Complete Testing Workflow

### Step-by-Step Testing Process

#### Step 1: Stop Any Existing Servers
```powershell
Get-Process | Where-Object {$_.ProcessName -like "*python*"} | Stop-Process -Force
```

#### Step 2: Start Fresh Server
```json
{
  "tool": "Bash",
  "arguments": {
    "command": "cd C:\\Users\\Arjay\\Downloads\\listings-workflow && python main.py",
    "run_in_background": true,
    "description": "Start FastAPI server"
  }
}
```

#### Step 3: Wait for Server Startup
```json
{
  "tool": "mcp__playwright__browser_wait_for",
  "arguments": {
    "time": 5
  }
}
```

#### Step 4: Navigate to Application
```json
{
  "tool": "mcp__playwright__browser_navigate",
  "arguments": {
    "url": "http://localhost:8004"
  }
}
```

#### Step 5: Take Snapshot to Understand Page
```json
{
  "tool": "mcp__playwright__browser_snapshot",
  "arguments": {}
}
```

#### Step 6: Interact with Page
Based on snapshot, click buttons, fill forms, etc.

#### Step 7: Verify Results
Take another snapshot or screenshot to verify the action worked.

#### Step 8: Clean Up
```json
{
  "tool": "mcp__playwright__browser_close",
  "arguments": {}
}
```

### Example: Test Pipeline Page

```python
# Pseudocode for testing pipeline page

# 1. Start server (background)
Bash("cd C:\\Users\\Arjay\\Downloads\\listings-workflow && python main.py", run_in_background=True)

# 2. Wait for startup
browser_wait_for(time=5)

# 3. Navigate
browser_navigate(url="http://localhost:8004/pipeline")

# 4. Snapshot to see page structure
browser_snapshot()

# 5. Click on a project row to expand
browser_click(element="Expand project row", ref="[from snapshot]")

# 6. Verify subprojects loaded
browser_wait_for(text="Variation:")

# 7. Take screenshot for documentation
browser_take_screenshot(filename="pipeline-test.png")

# 8. Close browser
browser_close()
```

---

## 7. Quick Reference Commands

### Server Management
```powershell
# Start server (run in background)
cd C:\Users\Arjay\Downloads\listings-workflow && python main.py

# Stop all Python processes
Get-Process | Where-Object {$_.ProcessName -like "*python*"} | Stop-Process -Force

# Check if port is in use
netstat -ano | findstr ":8004"

# List Python processes
Get-Process | Where-Object {$_.ProcessName -like "*python*"} | Select-Object Id, ProcessName, StartTime

# Stop specific process by PID
Stop-Process -Id [PID] -Force
```

### Playwright MCP Quick Reference
```
Navigate:     mcp__playwright__browser_navigate     url="http://localhost:8004"
Snapshot:     mcp__playwright__browser_snapshot     (no args)
Click:        mcp__playwright__browser_click        element="...", ref="..."
Type:         mcp__playwright__browser_type         element="...", ref="...", text="..."
Wait:         mcp__playwright__browser_wait_for     text="..." OR time=5
Screenshot:   mcp__playwright__browser_take_screenshot  filename="...", fullPage=true
Close:        mcp__playwright__browser_close        (no args)
Install:      mcp__playwright__browser_install      (no args, if browser missing)
```

### Application URLs
```
Home/Scraper Dashboard:  http://localhost:8004/
Pipeline:                http://localhost:8004/pipeline
Keywords:                http://localhost:8004/keywords/{subproject_id}
Health Check:            http://localhost:8004/health
```

---

## Troubleshooting Checklist

Before reporting issues, verify:

- [ ] MySQL (XAMPP) is running
- [ ] No other process using port 8004
- [ ] Python is in PATH
- [ ] All dependencies installed (`pip install -r requirements.txt`)
- [ ] Using PowerShell commands, not Unix commands
- [ ] Server given 5 seconds to start before testing
- [ ] Using correct `ref` values from fresh snapshots
- [ ] Browser closed properly after previous tests

---

## Key Takeaways

1. **Windows uses PowerShell** - Never use `pkill`, `killall`, `lsof`, or other Unix commands
2. **Start server in background** - Use `run_in_background: true` parameter
3. **Wait before testing** - Give server 5 seconds to fully start
4. **Snapshots over screenshots** - `browser_snapshot` gives structured data for interaction
5. **Always close browser** - Prevents resource leaks and stale state
6. **Fresh snapshot before clicks** - Element refs can change after page updates
