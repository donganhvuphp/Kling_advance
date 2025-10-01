# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Kling Video Generator is a PyQt6-based desktop application for automated video generation using Kling AI. It uses Playwright for browser automation to upload images, submit prompts, and download generated videos in batch.

## Core Architecture

### Two-Component System

1. **`kling_engine.py`** - Core automation engine
   - Handles browser automation via Playwright
   - Manages video generation queue and state tracking
   - Implements prompt verification before download
   - Position-based video tracking system
   - Session persistence with `state.json`

2. **`gui_app.py`** - PyQt6 GUI application
   - Dark-themed professional UI
   - Multi-folder selection with checkboxes
   - Real-time log display with color coding
   - Progress tracking and control buttons
   - Thread-safe communication via signals (QThread)

### Key Concepts

**Video Queue Management**: The engine uses a position-based tracking system where each queued video is assigned an `article_position` (starting at 1 for newest). When a new video is queued, all existing positions increment by 1. This prevents downloading wrong videos from the feed.

**Prompt Verification**: Before downloading, the system extracts the prompt from the article element and compares it with the expected prompt. Downloads only occur if prompts match (fuzzy matching with first 50 chars).

**Session Management**: User login session is saved to `state.json` using Playwright's storage_state. The GUI provides manual save/delete controls for session management.

**Thread Architecture**: GUI runs worker thread in two phases:
- Phase 1 (BROWSER_ONLY): Launch browser and wait for user interaction (login/session save)
- Phase 2 (PROCESSING): Start video generation after user clicks "Start"

## Common Development Commands

### Setup and Installation

```bash
# Initial setup (creates venv, installs dependencies, downloads Chromium)
./setup.sh

# Manual setup
python3 -m venv venv
source venv/bin/activate
pip install playwright PyQt6
playwright install chromium
```

### Running the Application

```bash
# Using start script
./start.sh

# Manual run
source venv/bin/activate
python gui_app.py
```

### Testing

There are no automated tests in this project. Testing is done manually through the GUI.

## Folder Structure Requirements

The application expects this folder structure:

```
root_folder/
  ├── folder1/
  │   ├── 1.jpg
  │   ├── 2.jpg
  │   └── prompts.txt    # Format: "1: prompt text"
  ├── folder2/
  │   ├── 1.jpg
  │   ├── 2.jpg
  │   └── prompts.txt
```

- Images must be numbered (1.jpg, 2.jpg, etc.)
- `prompts.txt` format: `<number>: <prompt text>` (one per line)
- Generated videos are saved as `<number>.mp4` in the same folder

## Critical Selectors (Kling AI Website)

**Key CSS/XPath selectors in `kling_engine.py`**:
- `UPLOAD_AREA` (line 17): File upload dropzone
- `PROMPT_BOX` (line 18): `#prompt` input field
- `GENERATE_BTN` (line 19): Generate button
- `DOWNLOAD_BTN_TEMPLATE` (line 20): Download button by article position
- `ARTICLE_PROMPT_SELECTOR_TEMPLATE` (line 21): Prompt text in article
- `DELETE_IMG_BTN_XPATH` (line 22): Delete uploaded image button

**⚠️ Important**: These selectors are tightly coupled to the Kling AI website structure. If the website UI changes, these will need updating.

## State Management

### Engine State Fields (`queued` list items)
- `status`: 'pending' | 'generating' | 'downloaded'
- `article_position`: 1-based position in feed (1 = newest)
- `queued_timestamp`: Time when video was queued
- `downloaded`: Boolean flag
- `prompt_norm`: Normalized prompt for matching

### Thread Safety
- `pause_event`, `stop_event`, `save_session_event`: Threading events for control
- Signals in GUI: `log_signal`, `progress_signal`, `browser_ready_signal`, `finished_signal`

## Download Logic Flow

1. Count active generating videos (check StatusBadge elements)
2. Calculate available slots = `max_concurrent - active_generating`
3. Queue new videos if slots available (upload image → fill prompt → generate)
4. Assign `article_position = 1` to new video, increment all others
5. Poll articles by position to check completion (look for download button)
6. Verify prompt matches before downloading
7. Download video and mark as complete

## UI Color Scheme

Dark theme with color coding:
- Primary: `#00D9FF` (cyan)
- Background: `#0A0E27` (dark blue)
- Success: `#00FF88` (green)
- Warning: `#FFA500` (orange)
- Error: `#FF4444` (red)
- Debug: `#888888` (gray)

## Important Gotchas

1. **Windows Python Detection**: The `setup.bat` script checks for both `python` and `py` commands. If you installed Python via the Microsoft Store or with Python Launcher, use `py` command. The script auto-detects which one is available.

2. **Browser must be launched before processing**: The two-phase workflow requires clicking "Open Browser" first, then "Start". This allows manual login if needed.

3. **Prompt format matters**: Image filename numbers must match prompt numbers in `prompts.txt`. E.g., `1.jpg` uses prompt line `1: <text>`.

4. **Article position tracking**: New videos appear at position 1, pushing older videos down. The system tracks this to avoid downloading wrong videos.

5. **Session save timing**: Only save session AFTER successful login. The "Save Session" button is only enabled when browser is running.

6. **Headless mode**: Should only be used after session is saved. First run requires visible browser for login.

7. **Download timeout**: Default `DOWNLOAD_POLL_TIMEOUT = 60 * 20` (20 minutes per folder). Adjust if processing large batches.

8. **Concurrent limit**: Default `max_concurrent = 2`. Higher values may cause rate limiting or UI issues on Kling AI.

## Code Style Notes

- Uses Vietnamese text for user-facing messages in GUI
- English for code, comments, and log levels
- Type hints used in function signatures
- Playwright timeouts generally set to 15-90 seconds
- Human-like delays with `random.uniform()` to avoid detection
