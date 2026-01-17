"""
Core Video Downloader Module
Wrapper around yt-dlp for multi-platform video downloading
"""
import os
import yt_dlp
from typing import Callable, Optional, List, Dict, Any
from dataclasses import dataclass
from pathlib import Path


@dataclass
class VideoInfo:
    """Video metadata"""
    url: str
    title: str
    duration: int
    thumbnail: str
    uploader: str
    formats: List[Dict[str, Any]]
    

@dataclass
class DownloadProgress:
    """Download progress data"""
    status: str  # 'downloading', 'finished', 'error'
    downloaded_bytes: int
    total_bytes: int
    speed: float
    eta: int
    filename: str
    percent: float


class VideoDownloader:
    """Main video downloader class using yt-dlp"""
    
    def __init__(self, download_dir: str = "downloads"):
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(exist_ok=True)
        self._progress_callback: Optional[Callable[[DownloadProgress], None]] = None
        
    def set_progress_callback(self, callback: Callable[[DownloadProgress], None]):
        """Set callback function for progress updates"""
        self._progress_callback = callback
        
    def _progress_hook(self, d: dict):
        """Internal progress hook for yt-dlp"""
        if self._progress_callback:
            total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
            downloaded = d.get('downloaded_bytes', 0)
            percent = (downloaded / total * 100) if total > 0 else 0
            
            progress = DownloadProgress(
                status=d.get('status', 'unknown'),
                downloaded_bytes=downloaded,
                total_bytes=total,
                speed=d.get('speed', 0) or 0,
                eta=d.get('eta', 0) or 0,
                filename=d.get('filename', ''),
                percent=percent
            )
            self._progress_callback(progress)
    
    def get_video_info(self, url: str) -> Optional[VideoInfo]:
        """Get video metadata without downloading"""
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                if not info:
                    return None
                
                # Extract available formats with quality info
                formats = []
                for f in info.get('formats', []):
                    format_info = {
                        'format_id': f.get('format_id', ''),
                        'ext': f.get('ext', ''),
                        'resolution': f.get('resolution', 'audio only'),
                        'filesize': f.get('filesize', 0),
                        'vcodec': f.get('vcodec', 'none'),
                        'acodec': f.get('acodec', 'none'),
                        'quality': f.get('quality', 0),
                        'height': f.get('height', 0),
                        'fps': f.get('fps', 0),
                    }
                    # Only include formats with video or audio
                    if f.get('vcodec') != 'none' or f.get('acodec') != 'none':
                        formats.append(format_info)
                
                return VideoInfo(
                    url=url,
                    title=info.get('title', 'Unknown'),
                    duration=info.get('duration', 0) or 0,
                    thumbnail=info.get('thumbnail', ''),
                    uploader=info.get('uploader', 'Unknown'),
                    formats=formats
                )
        except Exception as e:
            print(f"Error getting video info: {e}")
            return None
    
    def get_quality_options(self, url: str) -> List[Dict[str, str]]:
        """Get simplified quality options for user selection"""
        info = self.get_video_info(url)
        if not info:
            return []
        
        # Common quality presets - all include audio
        quality_options = [
            {'id': 'bestvideo+bestaudio/best', 'label': 'Best Quality (Video + Audio)'},
        ]
        
        # Standard YouTube resolutions
        standard_heights = [2160, 1440, 1080, 720, 480, 360, 240, 144]
        
        # Find available resolutions from formats
        available_heights = set()
        for f in info.formats:
            height = f.get('height', 0)
            if height and height in standard_heights:
                available_heights.add(height)
        
        # Add available resolutions (sorted highest first)
        for height in sorted(available_heights, reverse=True):
            quality_options.append({
                'id': f'bestvideo[height<={height}]+bestaudio/best[height<={height}]',
                'label': f'{height}p (Video + Audio)'
            })
        
        # Add audio only options
        quality_options.append({'id': 'bestaudio/best', 'label': 'Audio Only (Best Quality)'})
        quality_options.append({'id': 'bestaudio[ext=m4a]/bestaudio', 'label': 'Audio Only (M4A)'})
        
        return quality_options
    
    def download_video(
        self, 
        url: str, 
        quality: str = 'best',
        filename_template: Optional[str] = None
    ) -> Optional[str]:
        """Download a single video"""
        output_template = filename_template or '%(title)s.%(ext)s'
        output_path = str(self.download_dir / output_template)
        
        ydl_opts = {
            'format': quality,
            'outtmpl': output_path,
            'progress_hooks': [self._progress_hook],
            'quiet': False,
            'no_warnings': False,
            'merge_output_format': 'mp4',
            # Re-encode audio to AAC for compatibility with Windows Media Player
            'postprocessors': [{
                'key': 'FFmpegVideoRemuxer',
                'preferedformat': 'mp4',
            }],
            # FFmpeg args to convert audio to AAC
            'postprocessor_args': {
                'ffmpeg': ['-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k']
            },
            # Embed metadata
            'writethumbnail': False,
            'embedthumbnail': False,
            # Force merge if separate streams
            'keepvideo': False,
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                if info:
                    # Return the actual filename
                    return ydl.prepare_filename(info)
        except Exception as e:
            print(f"Error downloading video: {e}")
            return None
        
        return None
    
    def get_channel_videos(
        self, 
        channel_url: str, 
        max_videos: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get list of videos from a channel or playlist"""
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
            'playlist_items': f'1:{max_videos}' if max_videos else None,
        }
        
        videos = []
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(channel_url, download=False)
                
                if not info:
                    return []
                
                entries = info.get('entries', [])
                for i, entry in enumerate(entries):
                    if max_videos and i >= max_videos:
                        break
                    if entry:
                        videos.append({
                            'url': entry.get('url') or entry.get('webpage_url', ''),
                            'title': entry.get('title', 'Unknown'),
                            'duration': entry.get('duration', 0),
                            'thumbnail': entry.get('thumbnail', ''),
                        })
        except Exception as e:
            print(f"Error getting channel videos: {e}")
        
        return videos
    
    def download_channel(
        self,
        channel_url: str,
        quality: str = 'best',
        max_videos: Optional[int] = None,
        video_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> List[str]:
        """Download multiple videos from channel/playlist"""
        videos = self.get_channel_videos(channel_url, max_videos)
        downloaded_files = []
        
        for i, video in enumerate(videos):
            if video_callback:
                video_callback(i + 1, len(videos), video['title'])
            
            result = self.download_video(video['url'], quality)
            if result:
                downloaded_files.append(result)
        
        return downloaded_files


def format_bytes(bytes_val: float) -> str:
    """Format bytes to human readable string"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_val < 1024:
            return f"{bytes_val:.2f} {unit}"
        bytes_val /= 1024
    return f"{bytes_val:.2f} TB"


def format_duration(seconds: int) -> str:
    """Format seconds to HH:MM:SS"""
    seconds = int(seconds)  # Ensure integer
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"
