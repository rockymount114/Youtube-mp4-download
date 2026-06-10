import os
import copy
import glob
import subprocess
from datetime import datetime
try:
    import yt_dlp
except ImportError:
    yt_dlp = None

# Locate project root (two levels up from this file: app/services/youtube.py -> root)
_ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))


def _find_ffmpeg():
    """Return path to ffmpeg: prefer ffmpeg.exe in project root, else system ffmpeg."""
    local = os.path.join(_ROOT_DIR, 'ffmpeg.exe')
    return local if os.path.exists(local) else 'ffmpeg'


def _validate_cookie_file(path):
    """Return path only if it is a valid Netscape-format cookie file, else None."""
    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            first_line = f.readline()
        if '# Netscape HTTP Cookie File' in first_line or '# HTTP Cookie File' in first_line:
            return path
        print(f"Warning: '{path}' is not Netscape-formatted (got: {first_line[:60]!r}). Skipping cookies.")
    except Exception as e:
        print(f"Warning: Could not read '{path}': {e}")
    return None


def _base_opts(output_path):
    """Build the base yt-dlp options shared by every call."""
    opts = {
        'outtmpl': output_path or os.path.join(_ROOT_DIR, '%(title)s.%(ext)s'),
        'quiet': True,
        'no_warnings': True,
        'ffmpeg_location': _find_ffmpeg(),
    }

    # Cookies file (auto-detect from project root if not set explicitly)
    cookie_file = _validate_cookie_file(os.path.join(_ROOT_DIR, 'cookies.txt'))
    if cookie_file:
        opts['cookiefile'] = cookie_file

    # Optional env-var overrides
    browser = os.getenv('COOKIES_BROWSER')
    if browser:
        opts['cookiesfrombrowser'] = (browser,)

    po_token = os.getenv('PO_TOKEN')
    if po_token:
        opts['extractor_args'] = {'youtube': {'po_token': [po_token]}}

    return opts


def get_ytdlp_opts(output_path, media_type='mp3', cookie_file=None):
    """Public helper kept for backwards-compat. Builds full opts for a given media type."""
    opts = _base_opts(output_path)

    # Allow an explicit cookie_file override
    if cookie_file:
        validated = _validate_cookie_file(cookie_file)
        if validated:
            opts['cookiefile'] = validated

    if media_type == 'mp3':
        opts.update({
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '32',
            }],
        })
    elif media_type == 'mp4':
        opts.update({
            'format': 'bestvideo+bestaudio/best',
            'merge_output_format': 'mp4',
        })

    return opts


def _clean_url(url):
    """Strip playlist parameters from a YouTube URL."""
    for sep in ('&list=', '?list='):
        if sep in url:
            url = url.split(sep)[0]
    return url


def try_download_with_clients(url, ydl_opts, download=True):
    """Try downloading/extracting info with several player clients in sequence."""
    if not yt_dlp:
        raise ImportError("yt-dlp is not installed")

    url = _clean_url(url)

    clients_to_try = [
        ['android'],
        ['web'],
        ['ios'],
        ['mweb'],
        ['web', 'ios'],
    ]

    last_error = ''
    for player_client in clients_to_try:
        # Deep-copy so postprocessors list and nested dicts aren't shared across attempts
        opts = copy.deepcopy(ydl_opts)
        yt_args = opts.setdefault('extractor_args', {}).get('youtube', {})
        yt_args = dict(yt_args)  # copy nested dict
        yt_args['player_client'] = player_client
        opts['extractor_args']['youtube'] = yt_args

        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                return ydl.extract_info(url, download=download)
        except Exception as e:
            last_error = str(e)
            print(f"Client {player_client} failed: {last_error}")
            continue

    # Final attempt with unmodified opts
    try:
        with yt_dlp.YoutubeDL(copy.deepcopy(ydl_opts)) as ydl:
            return ydl.extract_info(url, download=download)
    except Exception as e:
        if download:
            raise Exception(f"YouTube download failed after all attempts: {e}")
        return None


def get_video_info(url):
    """Fetch video metadata (title, upload_date) without downloading."""
    if not yt_dlp:
        return None

    opts = _base_opts('')          # empty outtmpl — no file will be written
    opts['skip_download'] = True   # belt-and-suspenders: skip even if outtmpl is set

    return try_download_with_clients(url, opts, download=False)


def download_youtube_audio(url, output_folder):
    """
    Download a YouTube video as a 32 kbps MP3 into output_folder.
    Returns the filename (not full path) of the saved MP3.

    Strategy:
      1. Ask yt-dlp to extract audio directly to MP3 via FFmpegExtractAudio.
         yt-dlp replaces %(ext)s with the *post-processed* extension, so the
         output file will be <base>.mp3 when FFmpeg is available.
      2. If that produces no .mp3 (FFmpeg missing / yt-dlp left a raw container),
         glob for any file with our base name and convert it with FFmpeg directly.
      3. If all else fails, raise so the caller can mark the meeting as Error with
         a useful message.
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename_base = f"{timestamp}_youtube"
    final_mp3 = os.path.join(output_folder, f"{filename_base}.mp3")

    # --- Attempt 1: yt-dlp MP3 extraction via FFmpegExtractAudio ---
    try:
        output_template = os.path.join(output_folder, f"{filename_base}.%(ext)s")
        ydl_opts = get_ytdlp_opts(output_template, 'mp3')
        try_download_with_clients(url, ydl_opts, download=True)

        if os.path.exists(final_mp3):
            print(f"MP3 download complete: {final_mp3}")
            return f"{filename_base}.mp3"

        # yt-dlp may have saved a raw audio container (webm/m4a/opus) if FFmpeg
        # post-processing was skipped.  Find and convert it.
        raw_files = [
            f for f in glob.glob(os.path.join(output_folder, f"{filename_base}.*"))
            if not f.endswith('.mp3') and not f.endswith('.part') and not f.endswith('.ytdl')
        ]
        if raw_files:
            raw_file = raw_files[0]
            print(f"FFmpeg post-processing was skipped by yt-dlp; converting {raw_file} manually...")
            _ffmpeg_convert(raw_file, final_mp3)
            if os.path.exists(final_mp3):
                _safe_remove(raw_file)
                return f"{filename_base}.mp3"

    except Exception as e:
        print(f"Attempt 1 (direct MP3) failed: {e}. Falling back to MP4 download…")

    # --- Attempt 2: download MP4, then extract audio with FFmpeg ---
    try:
        temp_base = f"{filename_base}_temp"
        output_template = os.path.join(output_folder, f"{temp_base}.%(ext)s")
        ydl_opts = get_ytdlp_opts(output_template, 'mp4')
        info = try_download_with_clients(url, ydl_opts, download=True)

        # Locate the downloaded file
        temp_files = [
            f for f in glob.glob(os.path.join(output_folder, f"{temp_base}.*"))
            if not f.endswith('.part') and not f.endswith('.ytdl')
        ]
        if not temp_files:
            raise Exception("Could not locate downloaded MP4 file")

        temp_file = temp_files[0]
        _ffmpeg_convert(temp_file, final_mp3)

        if os.path.exists(final_mp3):
            _safe_remove(temp_file)
            return f"{filename_base}.mp3"
        else:
            raise Exception("FFmpeg produced no output file")

    except Exception as e:
        raise Exception(f"YouTube download failed (both attempts): {e}")


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _ffmpeg_convert(src, dst_mp3):
    """Convert src audio/video file to a 32 kbps MP3 at dst_mp3 using FFmpeg."""
    ffmpeg = _find_ffmpeg()
    cmd = [ffmpeg, '-i', src, '-b:a', '32k', '-vn', '-y', dst_mp3]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"FFmpeg error: {result.stderr[-500:]}")  # last 500 chars


def _safe_remove(path):
    try:
        os.remove(path)
    except Exception:
        pass