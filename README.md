# 🎬 Kling Video Generator - Advanced UI

Professional dark-themed GUI application for automated Kling AI video generation.

## ✨ Features

- **Dark Professional UI**: Modern, eye-friendly dark theme interface
- **Folder Selection**: Easy folder browser for selecting root directory
- **Real-time Logs**: Color-coded log display with timestamps
- **Progress Tracking**: Visual progress bar showing download status
- **Control Buttons**:
  - ▶ Start: Begin processing
  - ⏸ Pause/Resume: Pause and resume anytime
  - ⏹ Stop: Stop processing completely
- **Configurable Settings**:
  - Headless mode toggle
  - Max concurrent videos (1-10)
  - Polling interval (5-60 seconds)
- **Log Export**: Export logs to text file for review

## 📦 Installation

### Quick Setup (Recommended)
```bash
cd Kling_advance
./setup.sh
```

The setup script will automatically:
- Create virtual environment
- Install all dependencies (Playwright, PyQt6)
- Install Chromium browser
- Verify installation

### Manual Setup
```bash
cd Kling_advance
python3 -m venv venv
source venv/bin/activate
pip install playwright PyQt6
playwright install chromium
```

### Run the Application
```bash
./start.sh
```

Or manually:
```bash
source venv/bin/activate
python gui_app.py
```

## 🎯 Usage

1. **Select Folder**: Click "Browse..." to select root folder containing subfolders with images
2. **Configure Settings**:
   - Enable/disable headless mode
   - Set max concurrent videos (recommended: 2)
   - Set polling interval (recommended: 10s)
3. **Start Process**: Click "▶ Start" button
4. **Monitor Progress**: Watch real-time logs and progress bar
5. **Control**:
   - Click "⏸ Pause" to pause (click again to resume)
   - Click "⏹ Stop" to stop completely

## 📁 Folder Structure

Your root folder should contain subfolders like:
```
root_folder/
  ├── folder1/
  │   ├── 1.jpg
  │   ├── 2.jpg
  │   ├── prompts.txt
  ├── folder2/
  │   ├── 1.jpg
  │   ├── 2.jpg
  │   ├── prompts.txt
```

Each subfolder must have:
- Images (.jpg, .png, .jpeg, .webp)
- `prompts.txt` file with prompts (one per line)

## 🎨 UI Features

- **Color-coded Logs**:
  - 🔵 INFO: General information (cyan)
  - 🟡 WARNING: Warnings (orange)
  - 🔴 ERROR: Errors (red)
  - 🟢 SUCCESS: Success messages (green)
  - ⚪ DEBUG: Debug information (gray)

- **Progress Bar**: Shows percentage and count of downloaded videos

- **Export Logs**: Save all logs to timestamped text file

## ⚙️ Technical Details

- Built with PyQt6 for modern UI
- Uses Playwright for browser automation
- Thread-safe logging and progress updates
- Non-blocking UI during processing
- Persistent session storage (state.json)

## 🚀 First Run

On first run, you'll need to login:
1. Browser window will open automatically
2. Login to your Kling account
3. Session will be saved automatically after 30 seconds
4. Subsequent runs will use saved session

## 📝 Tips

- Use headless mode only after successful login
- Recommended: 2 concurrent videos for stability
- Monitor logs for any errors or warnings
- Pause anytime without losing progress
- Export logs if you encounter issues

## 🐛 Troubleshooting

**UI not showing?**
- Ensure PyQt6 is installed correctly
- Try running with `python3 gui_app.py`

**Browser automation failing?**
- Ensure Playwright is installed: `playwright install chromium`
- Check if state.json exists and is valid
- Try deleting state.json and re-login

**Videos not downloading?**
- Check folder structure matches requirements
- Ensure prompts.txt exists in each subfolder
- Monitor debug logs for selector issues

## 📄 License

This tool is for educational purposes. Use responsibly.
