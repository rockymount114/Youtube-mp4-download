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

def get_ytdlp_opts(media_type, use_cookies=False, cookie_file=None):
    """Get yt-dlp options based on media type and cookie settings"""
    opts = {
        'outtmpl': '%(title)s.%(ext)s',
    }
    
    if cookie_file and os.path.exists(cookie_file):
        opts['cookiefile'] = cookie_file
        print(f"Using cookies from: {cookie_file}")
    
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
    """Try downloading with different client configurations"""
    clients_to_try = [
        {'player_client': ['web']},
        {'player_client': ['web', 'tv', 'ios']},
        {'player_client': ['web'], 'extractor_retries': 3},
    ]
    
    for i, client_args in enumerate(clients_to_try):
        opts = ydl_opts.copy()
        if 'extractor_args' not in opts:
            opts['extractor_args'] = {}
        opts['extractor_args']['youtube'] = client_args
        
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
                return info
        except Exception as e:
            error_msg = str(e)
            if "403" in error_msg or "not available" in error_msg.lower():
                print(f"Client config {i+1} failed, trying next...")
                continue
            raise
    
    # Final attempt without extractor_args
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        return ydl.extract_info(url, download=True)

def download_mp4_and_mp3(url, cookie_file=None):
    """Download video (MP4), then use FFmpeg to extract MP3 from it"""
    import subprocess

    print("Step 1: Downloading video (MP4)...")
    ydl_opts = get_ytdlp_opts('mp4', cookie_file=cookie_file)

    try:
        info = try_download_with_clients(url, ydl_opts)
        video_title = info.get('title', 'video')
        print(f"Video download complete: {video_title}")
    except Exception as e:
        print(f"Error downloading video: {e}")
        print("\nIf you see HTTP 403 errors, you need browser cookies.")
        print("Export cookies from your browser using a browser extension:")
        print("  https://github.com/yt-dlp/yt-dlp#exporting-cookies")
        print("Then run with: python main.py --cookies cookies.txt <url>")
        return

    # Find the downloaded MP4 file
    mp4_file = f"{video_title}.mp4"
    if not os.path.exists(mp4_file):
        import glob
        mp4_files = glob.glob(f"{video_title}*.mp4")
        # Exclude partial downloads
        mp4_files = [f for f in mp4_files if not f.endswith('.part') and not f.endswith('.ytdl')]
        if mp4_files:
            mp4_file = mp4_files[0]
        else:
            print(f"Error: Video file not found")
            return

    mp3_file = f"{video_title}.mp3"

    print("\nStep 2: Converting MP4 to MP3 using FFmpeg...")
    try:
        cmd = [
            os.path.join(os.path.dirname(__file__), 'ffmpeg.exe'),
            '-i', mp4_file,
            '-b:a', '32k',
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
        print(f"\nYou can manually convert using:")
        print(f'  ffmpeg -i "{mp4_file}" -b:a 32k "{mp3_file}"')

def download_media_ytdlp(url, media_type, cookie_file=None):
    """Download using yt-dlp (recommended)"""
    try:
        if media_type == 'mp3':
            ydl_opts = get_ytdlp_opts('mp3', cookie_file=cookie_file)
            print("Downloading audio with yt-dlp (32kbps MP3)...")

            try:
                info = try_download_with_clients(url, ydl_opts)
            except Exception as e:
                if "403" in str(e):
                    print("\nHTTP 403 error - try exporting browser cookies")
                raise
            print("Download complete!")

        elif media_type == 'mp4':
            download_mp4_and_mp3(url, cookie_file=cookie_file)
            return
        else:
            print("Invalid media type specified.")
            return
            
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
            print("Download complete!")
            
    except Exception as e:
        print(f"Error with yt-dlp: {e}")
        if "ffmpeg" in str(e).lower():
            print("\nFFmpeg is required for MP3 conversion!")
            print("Please install FFmpeg:")
            print("- Windows: Download from https://ffmpeg.org/download.html")
            print("- macOS: brew install ffmpeg")
            print("- Linux: sudo apt install ffmpeg")
            print("\nAlternatively, try downloading as WebM (audio only) without conversion.")

def download_media_pytube(url, media_type):
    """Download using pytube (fallback)"""
    try:
        # Add user agent to help with 400 errors
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
                # Try getting the best available stream
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
        print("Possible solutions:")
        print("1. Try updating pytube: pip install --upgrade pytube")
        print("2. Install yt-dlp instead: pip install yt-dlp")
        print("3. Check if the URL is valid and accessible")

def download_media_ytdlp_fallback(url, media_type):
    """Download using yt-dlp without FFmpeg conversion (WebM format)"""
    try:
        if media_type == 'mp3':
            ydl_opts = {
                'format': 'bestaudio[ext=webm]/bestaudio',
                'outtmpl': '%(title)s.%(ext)s',
            }
            print("Downloading audio as WebM (no conversion - FFmpeg not available)...")

        elif media_type == 'mp4':
            ydl_opts = {
                'format': 'best[ext=mp4]/best',
                'outtmpl': '%(title)s.%(ext)s',
            }
            print("Downloading video with yt-dlp (MP4 only - no MP3 conversion)...")
        else:
            print("Invalid media type specified.")
            return
            
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
            print("Download complete! (Note: Audio saved as WebM format)")
            
    except Exception as e:
        print(f"Error with yt-dlp fallback: {e}")

def download_media(url, media_type, cookie_file=None):
    # Remove playlist parameter if present
    if '&list=' in url:
        url = url.split('&list=')[0]
    elif '?list=' in url:
        url = url.split('?list=')[0]

    if USE_YT_DLP:
        try:
            download_media_ytdlp(url, media_type, cookie_file=cookie_file)
        except Exception as e:
            if "ffmpeg" in str(e).lower() and media_type == 'mp3':
                print("\nTrying fallback without MP3 conversion...")
                download_media_ytdlp_fallback(url, media_type)
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

    args = parser.parse_args()

    if args.url:
        url = args.url
        media_type = args.format if args.format else 'mp3'
    else:
        url = input("Input Youtube url: ")
        choice = input("Choose a format (1 for mp3, 2 for mp4) [default: 1]: ").strip() or "1"
        media_type = 'mp3' if choice == '1' else 'mp4'

    cookie_file = args.cookies

    if media_type == 'mp3':
        download_media(url, 'mp3', cookie_file=cookie_file)
    elif media_type == 'mp4':
        download_media(url, 'mp4', cookie_file=cookie_file)
    else:
        print("Invalid choice.")
