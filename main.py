import os
import sys

# Try to import yt-dlp first (more reliable), fallback to pytube
try:
    import yt_dlp
    USE_YT_DLP = True
except ImportError:
    try:
        from pytube import YouTube
        USE_YT_DLP = False
        print("Warning: Using pytube fallback. For better reliability, install yt-dlp: pip install yt-dlp")
    except ImportError:
        print("Error: Neither yt-dlp nor pytube is installed.")
        print("Please install one of them:")
        print("  pip install yt-dlp  (recommended)")
        print("  pip install pytube  (fallback)")
        sys.exit(1)

def get_ytdlp_opts(media_type, use_cookies=False, cookie_file=None, cookies_from_browser=None, po_token=None):
    """Get yt-dlp options based on media type and cookie settings"""
    opts = {
        'outtmpl': '%(title)s.%(ext)s',
        'quiet': False,
        'no_warnings': False,
    }

    if cookies_from_browser:
        opts['cookiesfrombrowser'] = (cookies_from_browser,)
        print(f"Using cookies from browser: {cookies_from_browser}")
    elif cookie_file and os.path.exists(cookie_file):
        opts['cookiefile'] = cookie_file
        print(f"Using cookies from: {cookie_file}")
    
    if po_token:
        if 'extractor_args' not in opts:
            opts['extractor_args'] = {'youtube': {}}
        # Some yt-dlp versions expect a list or a single string
        opts['extractor_args']['youtube']['po_token'] = [po_token]
        print(f"Using provided PO Token")

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

def try_download_with_clients(url, ydl_opts):
    """Try downloading with different client configurations to bypass DRM/Bot detection"""
    # Priority order: android is currently most resilient, followed by web and ios
    # We avoid 'tv' as it often triggers DRM protection experiments
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
        yt_args = opts['extractor_args'].get('youtube', {}).copy()
        yt_args.update(client_args)
        opts['extractor_args']['youtube'] = yt_args
        
        client_name = ", ".join(client_args['player_client'])
        print(f"Attempting download with client(s): {client_name}...")
        
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                return ydl.extract_info(url, download=True)
        except Exception as e:
            last_error = str(e)
            print(f"Client {client_name} failed: {last_error.split(':')[-1].strip()}")
            
            # If it's a DRM error or 403, try next client
            if any(msg in last_error.lower() for msg in ["drm", "403", "not available", "po token", "requested format"]):
                continue
            # For other errors, we still try next client as it might be client-specific
            continue
    
    # Final attempt with default settings if all specific clients fail
    print("All specific client attempts failed. Making one final attempt with default settings...")
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            return ydl.extract_info(url, download=True)
    except Exception as e:
        raise Exception(f"Failed to download after multiple attempts. Last error: {e}")

def download_mp4_and_mp3(url, cookie_file=None, cookies_from_browser=None, po_token=None):
    """Download video (MP4), then use FFmpeg to extract MP3 from it"""
    import subprocess

    print("Step 1: Downloading video (MP4)...")
    ydl_opts = get_ytdlp_opts('mp4', cookie_file=cookie_file, cookies_from_browser=cookies_from_browser, po_token=po_token)

    try:
        info = try_download_with_clients(url, ydl_opts)
        video_title = info.get('title', 'video')
        video_ext = info.get('ext', 'mp4')
        print(f"Video download complete: {video_title}")
    except Exception as e:
        print(f"Error downloading video: {e}")
        print("\nTroubleshooting Tips:")
        print("1. Export browser cookies: python main.py --cookies cookies.txt <url>")
        print("2. Provide cookies from browser: python main.py --cookies-from-browser chrome <url>")
        print("3. Use a PO Token: python main.py --po-token <token> <url>")
        print("4. Update yt-dlp: pip install -U yt-dlp")
        return

    # Find the downloaded MP4 file
    mp4_file = f"{video_title}.{video_ext}"
    if not os.path.exists(mp4_file):
        import glob
        # Try to find file by title, removing problematic characters
        safe_title = "".join([c for c in video_title if c.isalnum() or c in " .-_"]).strip()
        mp4_files = glob.glob(f"*{safe_title}*.{video_ext}")
        mp4_files = [f for f in mp4_files if not f.endswith('.part') and not f.endswith('.ytdl')]
        if mp4_files:
            mp4_file = mp4_files[0]
        else:
            print(f"Error: Downloaded file not found as {mp4_file}")
            return

    mp3_file = os.path.splitext(mp4_file)[0] + ".mp3"

    print(f"\nStep 2: Converting {mp4_file} to MP3 using FFmpeg...")
    try:
        ffmpeg_exe = os.path.join(os.path.dirname(__file__), 'ffmpeg.exe')
        if not os.path.exists(ffmpeg_exe):
            ffmpeg_exe = 'ffmpeg' # Fallback to system ffmpeg

        cmd = [
            ffmpeg_exe,
            '-i', mp4_file,
            '-b:a', '32k',
            '-vn',
            '-y',
            mp3_file
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"MP3 created: {mp3_file}")
        else:
            print(f"FFmpeg error: {result.stderr}")
    except Exception as e:
        print(f"Error extracting audio: {e}")

def download_media_ytdlp(url, media_type, cookie_file=None, cookies_from_browser=None, po_token=None):
    """Download using yt-dlp (recommended)"""
    try:
        if media_type == 'mp3':
            ydl_opts = get_ytdlp_opts('mp3', cookie_file=cookie_file, cookies_from_browser=cookies_from_browser, po_token=po_token)
            print("Downloading audio with yt-dlp (32kbps MP3)...")
            try:
                try_download_with_clients(url, ydl_opts)
            except Exception as e:
                if "403" in str(e):
                    print("\nHTTP 403 error - try exporting browser cookies or providing a PO Token")
                raise
            print("Download complete!")

        elif media_type == 'mp4':
            download_mp4_and_mp3(url, cookie_file=cookie_file, cookies_from_browser=cookies_from_browser, po_token=po_token)
            return
        else:
            print("Invalid media type specified.")
            return
            
    except Exception as e:
        print(f"Error with yt-dlp: {e}")
        if "ffmpeg" in str(e).lower():
            print("\nFFmpeg is required for MP3 conversion!")
            print("Please ensure ffmpeg.exe is in the project directory.")

def download_media_pytube(url, media_type):
    """Download using pytube (fallback)"""
    try:
        yt = YouTube(url, use_oauth=False, allow_oauth_cache=True)
        
        if media_type == 'mp3':
            stream = yt.streams.filter(only_audio=True).first()
            if not stream:
                print("No audio stream found!")
                return
            print("Downloading audio with pytube...")
            output_file = stream.download()
            base, ext = os.path.splitext(output_file)
            new_file = base + '.mp3'
            if os.path.exists(new_file):
                os.remove(new_file)
            os.rename(output_file, new_file)
            print(f"Download complete! Saved as {new_file}")
            
        elif media_type == 'mp4':
            stream = yt.streams.filter(progressive=True, file_extension='mp4').first()
            if not stream:
                stream = yt.streams.filter(file_extension='mp4').first()
            if not stream:
                print("No video stream found!")
                return
            print("Downloading video with pytube...")
            stream.download()
            print("Download complete!")
        else:
            print("Invalid media type specified.")
            
    except Exception as e:
        print(f"Error with pytube: {e}")

def download_media(url, media_type, cookie_file=None, cookies_from_browser=None, po_token=None):
    # Remove playlist parameter if present
    if '&list=' in url:
        url = url.split('&list=')[0]
    elif '?list=' in url:
        url = url.split('?list=')[0]

    if USE_YT_DLP:
        try:
            download_media_ytdlp(url, media_type, cookie_file=cookie_file, cookies_from_browser=cookies_from_browser, po_token=po_token)
        except Exception as e:
            if "ffmpeg" in str(e).lower() and media_type == 'mp3':
                print("\nTrying fallback without MP3 conversion (WebM)...")
                ydl_opts = {
                    'format': 'bestaudio[ext=webm]/bestaudio',
                    'outtmpl': '%(title)s.%(ext)s',
                }
                if po_token:
                    ydl_opts['extractor_args'] = {'youtube': {'po_token': [po_token]}}
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
            else:
                raise e
    else:
        download_media_pytube(url, media_type)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='YouTube Video/Audio Downloader')
    parser.add_argument('url', nargs='?', help='YouTube video URL')
    parser.add_argument('format', nargs='?', choices=['mp3', 'mp4'], default=None, help='Output format')
    parser.add_argument('--cookies', help='Path to cookies.txt file (Netscape format)')
    parser.add_argument('--cookies-from-browser', dest='browser', help='Browser name to extract cookies from (e.g., chrome, firefox, edge)')
    parser.add_argument('--po-token', help='Proof of Origin Token (GVS PO Token)')

    args = parser.parse_args()

    if args.url:
        url = args.url
        media_type = args.format if args.format else 'mp3'
    else:
        url = input("Input Youtube url: ")
        choice = input("Choose a format (1 for mp3, 2 for mp4) [default: 1]: ").strip() or "1"
        media_type = 'mp3' if choice == '1' else 'mp4'

    cookie_file = args.cookies
    cookies_from_browser = args.browser
    po_token = args.po_token

    download_media(url, media_type, cookie_file=cookie_file, cookies_from_browser=cookies_from_browser, po_token=po_token)
