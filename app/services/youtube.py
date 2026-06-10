import os
import sys
import subprocess
from datetime import datetime
try:
    import yt_dlp
except ImportError:
    yt_dlp = None

def get_ytdlp_opts(output_path, media_type='mp3', cookie_file=None):
    """Get yt-dlp options based on media type and cookie settings"""
    opts = {
        'outtmpl': output_path,
        'quiet': True,
        'no_warnings': True,
    }

    # Check for cookies.txt in project root if not provided
    if not cookie_file:
        root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        potential_cookies = os.path.join(root_dir, 'cookies.txt')
        if os.path.exists(potential_cookies):
            cookie_file = potential_cookies

    if cookie_file and os.path.exists(cookie_file):
        # Validate cookie file format (Netscape format required)
        try:
            with open(cookie_file, 'r', encoding='utf-8', errors='ignore') as f:
                first_line = f.readline()
                if '# Netscape HTTP Cookie File' in first_line or first_line.startswith('\t') or (first_line.strip() and not first_line.strip().startswith('{')):
                    opts['cookiefile'] = cookie_file
                else:
                    print(f"Warning: {cookie_file} is not Netscape formatted. Skipping.")
        except Exception as e:
            print(f"Warning: Could not read {cookie_file}: {e}")
        
    # Support cookies from browser via environment variable
    cookies_browser = os.getenv('COOKIES_BROWSER')
    if cookies_browser:
        opts['cookiesfrombrowser'] = (cookies_browser,)

    po_token = os.getenv('PO_TOKEN')
    if po_token:
        opts['extractor_args'] = {'youtube': {'po_token': [po_token]}}

    # Try to find ffmpeg in project directory
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    ffmpeg_exe = os.path.join(root_dir, 'ffmpeg.exe')
    if os.path.exists(ffmpeg_exe):
        opts['ffmpeg_location'] = ffmpeg_exe

    if media_type == 'mp3':
        opts.update({
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '32',
            }],
            'extractaudio': True,
            'audioformat': 'mp3',
            'audioquality': '32k',
        })
    elif media_type == 'mp4':
        opts.update({
            'format': 'bestvideo+bestaudio/best',
            'merge_output_format': 'mp4',
        })
    
    return opts

def try_download_with_clients(url, ydl_opts, download=True):
    """Try downloading with different client configurations to bypass DRM/Bot detection"""
    if not yt_dlp:
        raise ImportError("yt-dlp is not installed")

    # Clean URL (remove playlist params)
    if '&list=' in url:
        url = url.split('&list=')[0]
    elif '?list=' in url:
        url = url.split('?list=')[0]

    # Priority order: android is currently most resilient, followed by web and ios
    clients_to_try = [
        {'player_client': ['android']},
        {'player_client': ['web']},
        {'player_client': ['ios']},
        {'player_client': ['mweb']},
        {'player_client': ['web', 'ios']},
    ]
    
    last_error = ""
    for i, client_args in enumerate(clients_to_try):
        opts = ydl_opts.copy()
        if 'extractor_args' not in opts:
            opts['extractor_args'] = {}
        
        # Ensure we don't overwrite existing youtube extractor args like po_token
        yt_args = opts['extractor_args'].get('youtube', {})
        if not isinstance(yt_args, dict):
            yt_args = {}
        else:
            yt_args = yt_args.copy()
            
        yt_args.update(client_args)
        opts['extractor_args']['youtube'] = yt_args
        
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                return ydl.extract_info(url, download=download)
        except Exception as e:
            last_error = str(e)
            print(f"Client {client_args} failed: {last_error}")
            # If it's a common bypassable error, try next client
            if any(msg in last_error.lower() for msg in ["drm", "403", "not available", "po token", "requested format", "sign in"]):
                continue
            # For other errors, we still try next client as it might be client-specific
            continue
    
    # Final attempt with default settings if all specific clients fail
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            return ydl.extract_info(url, download=download)
    except Exception as e:
        if download:
            raise Exception(f"YouTube download failed after multiple bypass attempts: {e}")
        else:
            # For metadata fetching, return None instead of raising if it fails
            return None

def get_video_info(url):
    """Fetch video title and upload date using robust clients"""
    if not yt_dlp:
        return None

    # Get standard options which include cookies and PO_TOKEN
    ydl_opts = get_ytdlp_opts('', 'mp3')
    ydl_opts.update({
        'skip_download': True,
        'quiet': True,
        'no_warnings': True,
    })
    
    return try_download_with_clients(url, ydl_opts, download=False)

def download_youtube_audio(url, output_folder):
    """Main entry point for downloading YouTube audio with robust logic"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename_base = f"{timestamp}_youtube"
    
    # Try direct MP3 download first
    try:
        output_template = os.path.join(output_folder, f"{filename_base}.%(ext)s")
        ydl_opts = get_ytdlp_opts(output_template, 'mp3')
        try_download_with_clients(url, ydl_opts, download=True)
        
        # Check if the file was created
        mp3_file = os.path.join(output_folder, f"{filename_base}.mp3")
        if os.path.exists(mp3_file):
            return f"{filename_base}.mp3"
    except Exception as e:
        print(f"Direct MP3 download failed: {e}. Trying MP4 fallback...")

    # Fallback: Download MP4 and convert to MP3 manually
    try:
        output_template = os.path.join(output_folder, f"{filename_base}_temp.%(ext)s")
        ydl_opts = get_ytdlp_opts(output_template, 'mp4')
        info = try_download_with_clients(url, ydl_opts, download=True)
        
        # Find the downloaded file (it might have a different extension than mp4 depending on merge)
        ext = info.get('ext', 'mp4')
        temp_file = os.path.join(output_folder, f"{filename_base}_temp.{ext}")
        final_mp3 = os.path.join(output_folder, f"{filename_base}.mp3")

        if not os.path.exists(temp_file):
            # Try to find it by glob if template didn't match exactly for some reason
            import glob
            matches = glob.glob(os.path.join(output_folder, f"{filename_base}_temp.*"))
            if matches:
                temp_file = matches[0]
            else:
                raise Exception("Could not find downloaded video file for conversion")

        # Convert to MP3
        root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        ffmpeg_exe = os.path.join(root_dir, 'ffmpeg.exe')
        if not os.path.exists(ffmpeg_exe):
            ffmpeg_exe = 'ffmpeg'

        cmd = [
            ffmpeg_exe,
            '-i', temp_file,
            '-b:a', '32k',
            '-vn',
            '-y',
            final_mp3
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Cleanup temp file
        if os.path.exists(temp_file):
            try: os.remove(temp_file)
            except: pass
            
        if result.returncode == 0 and os.path.exists(final_mp3):
            return f"{filename_base}.mp3"
        else:
            raise Exception(f"FFmpeg conversion failed: {result.stderr}")
            
    except Exception as e:
        raise Exception(f"YouTube download and fallback failed: {e}")


