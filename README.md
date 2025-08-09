# YouTube Video Downloader

This project is a simple YouTube video downloader. It uses the `pytube` library to download videos from YouTube. The main script is `main.py`.

## Running the code

To run the code, execute the following command in your terminal:

```bash
python main.py
```

The script will then prompt you to enter a YouTube video URL.

## Dependencies

This project has the following dependency:

*   `pytube`

This is listed in the `pyproject.toml` file.

## Converting to MP3

The following commands can be used to convert the downloaded video files to MP3 format using `ffmpeg`:

```
.\ffmpeg -i "三国1-12集.mp4" -vn -c:a libmp3lame -b:a 32k "三国1-12集.mp3" 
.\ffmpeg -i "三国13-23集.mp4" -vn -c:a libmp3lame -b:a 32k "三国13-23集.mp3" 
.\ffmpeg -i "三国24-36集.mp4" -vn -c:a libmp3lame -b:a 32k "三国24-36集.mp3" 
.\ffmpeg -i "三国37-45集.mp4" -vn -c:a libmp3lame -b:a 32k "三国37-45集.mp3" 
.\ffmpeg -i "三国46-52集.mp4" -vn -c:a libmp3lame -b:a 32k "三国46-52集.mp3" 
```