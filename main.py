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

def download_media_ytdlp(url, media_type):
    """Download using yt-dlp (recommended)"""
    try:
        if media_type == 'mp3':
            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '32',  # Set to 32kbps as requested
                }],
                'outtmpl': '%(title)s.%(ext)s',
                'extractaudio': True,
                'audioformat': 'mp3',
                'audioquality': '32k',
            }
            print("Downloading audio with yt-dlp (32kbps MP3)...")
            
        elif media_type == 'mp4':
            ydl_opts = {
                'format': 'best[ext=mp4]/best',
                'outtmpl': '%(title)s.%(ext)s',
            }
            print("Downloading video with yt-dlp...")
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
            print("Downloading video with yt-dlp...")
        else:
            print("Invalid media type specified.")
            return
            
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
            print("Download complete! (Note: Audio saved as WebM format)")
            
    except Exception as e:
        print(f"Error with yt-dlp fallback: {e}")

def download_media(url, media_type):
    # Remove playlist parameter if present
    if '&list=' in url:
        url = url.split('&list=')[0]
    elif '?list=' in url:
        url = url.split('?list=')[0]
    
    if USE_YT_DLP:
        try:
            download_media_ytdlp(url, media_type)
        except Exception as e:
            if "ffmpeg" in str(e).lower() and media_type == 'mp3':
                print("\nTrying fallback without MP3 conversion...")
                download_media_ytdlp_fallback(url, media_type)
            else:
                raise e
    else:
        download_media_pytube(url, media_type)

if __name__ == "__main__":
    import sys
    
    # Allow URL as command-line argument for non-interactive use
    if len(sys.argv) > 1:
        url = sys.argv[1]
        media_type = sys.argv[2] if len(sys.argv) > 2 else 'mp3'
        download_media(url, media_type)
    else:
        url = input("Input Youtube url: ")
        choice = input("Choose a format (1 for mp3, 2 for mp4) [default: 1]: ").strip() or "1"

        if choice == '1':
            download_media(url, 'mp3')
        elif choice == '2':
            download_media(url, 'mp4')
        else:
            print("Invalid choice. Please run the script again and choose '1' or '2'.")