"""
Web UI Video Downloader
Flask backend with SocketIO for realtime progress
"""
import eventlet
eventlet.monkey_patch()

import os
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
from downloader import VideoDownloader, DownloadProgress, format_bytes, format_duration


app = Flask(__name__)
app.config['SECRET_KEY'] = 'video-downloader-secret'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# Global downloader instance
downloader = VideoDownloader("downloads")


@app.route('/')
def index():
    """Serve main page"""
    return render_template('index.html')


@app.route('/api/info', methods=['POST'])
def get_video_info():
    """Get video information"""
    data = request.json
    url = data.get('url', '')
    
    if not url:
        return jsonify({'error': 'URL is required'}), 400
    
    info = downloader.get_video_info(url)
    
    if not info:
        return jsonify({'error': 'Could not fetch video info'}), 400
    
    qualities = downloader.get_quality_options(url)
    
    return jsonify({
        'title': info.title,
        'uploader': info.uploader,
        'duration': format_duration(info.duration),
        'thumbnail': info.thumbnail,
        'qualities': qualities
    })


@app.route('/api/channel', methods=['POST'])
def get_channel_videos():
    """Get videos from channel/playlist"""
    data = request.json
    url = data.get('url', '')
    max_videos = data.get('max_videos', 10)
    
    if not url:
        return jsonify({'error': 'URL is required'}), 400
    
    videos = downloader.get_channel_videos(url, max_videos)
    
    if not videos:
        return jsonify({'error': 'Could not fetch videos'}), 400
    
    return jsonify({
        'videos': [{
            'url': v['url'],
            'title': v['title'],
            'duration': format_duration(v['duration']) if v['duration'] else '--:--',
            'thumbnail': v['thumbnail']
        } for v in videos],
        'count': len(videos)
    })


@socketio.on('start_download')
def handle_download(data):
    """Handle download request via WebSocket"""
    url = data.get('url', '')
    quality = data.get('quality', 'best')
    download_id = data.get('id', url)
    
    if not url:
        emit('download_error', {'id': download_id, 'error': 'URL is required'})
        return
    
    # Emit starting status
    socketio.emit('download_started', {'id': download_id})
    
    def progress_callback(p: DownloadProgress):
        socketio.emit('download_progress', {
            'id': download_id,
            'status': p.status,
            'percent': round(p.percent, 1),
            'speed': format_bytes(p.speed) + '/s' if p.speed else '',
            'eta': p.eta,
            'downloaded': format_bytes(p.downloaded_bytes),
            'total': format_bytes(p.total_bytes)
        })
        # Allow other greenlets to run
        eventlet.sleep(0)
    
    def do_download():
        try:
            local_downloader = VideoDownloader("downloads")
            local_downloader.set_progress_callback(progress_callback)
            
            result = local_downloader.download_video(url, quality)
            
            if result:
                socketio.emit('download_complete', {
                    'id': download_id,
                    'filename': os.path.basename(result)
                })
            else:
                socketio.emit('download_error', {
                    'id': download_id,
                    'error': 'Download failed'
                })
        except Exception as e:
            socketio.emit('download_error', {
                'id': download_id,
                'error': str(e)
            })
    
    # Spawn as eventlet greenlet instead of thread
    eventlet.spawn(do_download)


@socketio.on('start_batch_download')
def handle_batch_download(data):
    """Handle batch download from channel/playlist"""
    videos = data.get('videos', [])
    quality = data.get('quality', 'best')
    batch_id = data.get('batch_id', 'batch')
    
    def do_batch_download():
        for i, video in enumerate(videos):
            url = video.get('url', '')
            video_id = f"{batch_id}_{i}"
            
            socketio.emit('batch_progress', {
                'batch_id': batch_id,
                'current': i + 1,
                'total': len(videos),
                'title': video.get('title', 'Unknown')
            })
            
            def make_progress_callback(vid):
                def progress_callback(p: DownloadProgress):
                    socketio.emit('download_progress', {
                        'id': vid,
                        'batch_id': batch_id,
                        'status': p.status,
                        'percent': round(p.percent, 1),
                        'speed': format_bytes(p.speed) + '/s' if p.speed else ''
                    })
                    eventlet.sleep(0)
                return progress_callback
            
            local_downloader = VideoDownloader("downloads")
            local_downloader.set_progress_callback(make_progress_callback(video_id))
            
            result = local_downloader.download_video(url, quality)
            
            socketio.emit('video_complete', {
                'batch_id': batch_id,
                'video_id': video_id,
                'success': result is not None
            })
            
            eventlet.sleep(0)
        
        socketio.emit('batch_complete', {'batch_id': batch_id})
    
    eventlet.spawn(do_batch_download)


if __name__ == '__main__':
    print("🎬 Video Downloader Web UI")
    print("📍 Open http://localhost:5000 in your browser")
    print("-" * 40)
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
