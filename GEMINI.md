# GEMINI.md

## Project Overview

This is a **YouTube Video and Audio Downloader** written in Python. It allows users to download YouTube videos in MP4 format or extract audio in MP3 format. The project is designed with robustness in mind, featuring fallback mechanisms for both downloading libraries and audio conversion.

**Core Technologies:**
- **Python 3.8+**
- **yt-dlp**: Primary library for downloading (more reliable).
- **pytube**: Fallback library for downloading.
- **FFmpeg**: Bundled binaries (`ffmpeg.exe`, `ffprobe.exe`, `ffplay.exe`) used for audio extraction and format conversion.
- **uv**: Modern Python package manager used for dependency management.

## Development Commands

### Environment Setup
The project uses `uv` for dependency management.
```powershell
# Install dependencies using uv
uv sync

# Or using pip
pip install -r requirements.txt
```

### Running the Downloader
The main entry point is `main.py`. It can be run interactively or with command-line arguments.
```powershell
# Interactive mode
python main.py

# CLI mode with arguments
python main.py <URL> <format: mp3|mp4>

# Using cookies to avoid 403 Forbidden errors
python main.py <URL> mp3 --cookies cookies.txt
python main.py <URL> mp3 --cookies-from-browser chrome

# Using a PO Token (Proof of Origin) for high-protection videos
python main.py <URL> mp3 --po-token <YOUR_TOKEN_HERE>
```

### Audio Conversion
If you have `.webm` files (often downloaded when FFmpeg is missing during the main download), use the conversion utility:
```powershell
python convert_to_mp3.py
```

## Project Structure

- `main.py`: The primary script handling URL parsing, library selection (`yt-dlp` vs `pytube`), and the download/conversion workflow.
- `convert_to_mp3.py`: A utility script to convert existing WebM audio files to MP3 format.
- `ffmpeg.exe`, `ffprobe.exe`, `ffplay.exe`: Bundled FFmpeg binaries for Windows to ensure audio conversion works out-of-the-box.
- `cookies.txt`: (Optional) A Netscape-formatted cookies file to bypass YouTube's bot detection.
- `pyproject.toml` & `uv.lock`: Dependency configuration for `uv`.
- `.venv/`: Local virtual environment.

## Business Logic & Technical Details

### Download Logic
1. **Library Selection**: The system attempts to use `yt_dlp` first. If unavailable, it falls back to `pytube`.
2. **Client Spoofing**: `main.py` rotates through multiple client identities (`android`, `web`, `ios`, `mweb`) to bypass bot detection. The `android` client is prioritized as it currently offers the best success rate against DRM-related false positives.
3. **PO Token Support**: Allows passing a `po_token` to satisfy YouTube's newer "Proof of Origin" requirements.
4. **Format Handling**:
   - **MP3**: Downloads the best audio stream and uses FFmpeg to convert it to a 32kbps MP3.
   - **MP4**: Downloads the best video and audio streams and merges them into an MP4.

### Anti-Bot Measures
YouTube frequently blocks automated downloads. This project handles this via:
- **Cookies**: Support for loading cookies from a file or directly from a local browser.
- **Client Rotation**: Automatically tries different clients (Android, Web, iOS) if the initial attempt fails with 403 or DRM errors.
- **Fallbacks**: If FFmpeg is missing, the script attempts to save the raw audio (usually WebM) instead of failing.

### Audio Quality
The project defaults to **32kbps** for MP3 extraction to prioritize small file sizes while maintaining acceptable speech quality.

## Development Guidelines

1. **Dependency Management**: Always use `uv` to add or update packages.
   - `uv add <package>`
2. **Error Handling**: Maintain the fallback logic. If a feature (like FFmpeg) is missing, provide clear instructions to the user on how to resolve it or offer a degraded but functional alternative.
3. **FFmpeg Pathing**: The project expects `ffmpeg.exe` to be in the root directory for Windows compatibility. Use `os.path.dirname(__file__)` to locate it reliably.
4. **Security**: Never commit `cookies.txt` if it contains sensitive session data. It is currently used for local execution.
