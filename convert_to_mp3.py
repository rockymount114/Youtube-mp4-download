#!/usr/bin/env python3
"""
Convert WebM audio files to MP3 using FFmpeg
"""
import os
import subprocess
import sys
import glob

def check_ffmpeg():
    """Check if FFmpeg is installed"""
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def convert_webm_to_mp3(input_file, output_file=None, bitrate='32k'):
    """Convert a WebM file to MP3"""
    if not output_file:
        base_name = os.path.splitext(input_file)[0]
        output_file = f"{base_name}.mp3"
    
    try:
        cmd = [
            'ffmpeg', '-i', input_file,
            '-vn',  # No video
            '-acodec', 'mp3',
            '-ab', bitrate,
            '-y',  # Overwrite output file
            output_file
        ]
        
        print(f"Converting {input_file} to {output_file} at {bitrate}...")
        subprocess.run(cmd, check=True)
        print(f"✓ Conversion complete: {output_file}")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"✗ Conversion failed: {e}")
        return False

def main():
    if not check_ffmpeg():
        print("FFmpeg is not installed or not in PATH!")
        print("Please install FFmpeg:")
        print("- Windows: Download from https://ffmpeg.org/download.html")
        print("- macOS: brew install ffmpeg")
        print("- Linux: sudo apt install ffmpeg")
        return
    
    print("FFmpeg found! Looking for WebM files to convert...")
    
    # Find all WebM files in current directory
    webm_files = glob.glob("*.webm")
    
    if not webm_files:
        print("No WebM files found in current directory.")
        print("Usage: python convert_to_mp3.py [filename.webm]")
        return
    
    # If command line argument provided, use that file
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
        if os.path.exists(input_file):
            convert_webm_to_mp3(input_file, bitrate='32k')
        else:
            print(f"File not found: {input_file}")
        return
    
    # Convert all WebM files found
    print(f"Found {len(webm_files)} WebM file(s):")
    for webm_file in webm_files:
        print(f"  - {webm_file}")
    
    response = input("\nConvert all to MP3 at 32kbps? (y/n): ").lower()
    if response == 'y':
        for webm_file in webm_files:
            convert_webm_to_mp3(webm_file, bitrate='32k')
            
        print(f"\n✓ Converted {len(webm_files)} file(s) to MP3!")
    else:
        print("Conversion cancelled.")

if __name__ == "__main__":
    main()