/**
 * Video Downloader - Frontend Application
 * Handles UI interactions, API calls, and WebSocket communication
 */

// Initialize Socket.IO
const socket = io();

// DOM Elements
const elements = {
    // Tabs
    tabs: document.querySelectorAll('.tab'),
    tabContents: document.querySelectorAll('.tab-content'),
    
    // Single Video
    videoUrl: document.getElementById('video-url'),
    fetchBtn: document.getElementById('fetch-btn'),
    videoPreview: document.getElementById('video-preview'),
    previewThumb: document.getElementById('preview-thumb'),
    previewTitle: document.getElementById('preview-title'),
    previewUploader: document.getElementById('preview-uploader'),
    previewDuration: document.getElementById('preview-duration'),
    qualitySection: document.getElementById('quality-section'),
    qualitySelect: document.getElementById('quality-select'),
    downloadBtn: document.getElementById('download-btn'),
    
    // Channel
    channelUrl: document.getElementById('channel-url'),
    maxVideos: document.getElementById('max-videos'),
    fetchChannelBtn: document.getElementById('fetch-channel-btn'),
    videoList: document.getElementById('video-list'),
    videoCount: document.getElementById('video-count'),
    videosContainer: document.getElementById('videos-container'),
    batchQuality: document.getElementById('batch-quality'),
    downloadAllBtn: document.getElementById('download-all-btn'),
    
    // Queue
    downloadQueue: document.getElementById('download-queue'),
    queueContainer: document.getElementById('queue-container'),
    
    // Toast
    toastContainer: document.getElementById('toast-container')
};

// State
let currentVideoInfo = null;
let channelVideos = [];

// Tab Switching
elements.tabs.forEach(tab => {
    tab.addEventListener('click', () => {
        const tabId = tab.dataset.tab;
        
        elements.tabs.forEach(t => t.classList.remove('active'));
        elements.tabContents.forEach(c => c.classList.remove('active'));
        
        tab.classList.add('active');
        document.getElementById(`${tabId}-tab`).classList.add('active');
    });
});

// Fetch Video Info
elements.fetchBtn.addEventListener('click', async () => {
    const url = elements.videoUrl.value.trim();
    if (!url) {
        showToast('Please enter a video URL', 'error');
        return;
    }
    
    setButtonLoading(elements.fetchBtn, true);
    hideElement(elements.videoPreview);
    hideElement(elements.qualitySection);
    
    try {
        const response = await fetch('/api/info', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Failed to fetch video info');
        }
        
        currentVideoInfo = data;
        displayVideoPreview(data);
        showToast('Video info loaded!', 'success');
        
    } catch (error) {
        showToast(error.message, 'error');
    } finally {
        setButtonLoading(elements.fetchBtn, false);
    }
});

function displayVideoPreview(info) {
    elements.previewThumb.src = info.thumbnail || 'https://via.placeholder.com/200x112?text=No+Thumbnail';
    elements.previewTitle.textContent = info.title;
    elements.previewUploader.textContent = `By: ${info.uploader}`;
    elements.previewDuration.textContent = `Duration: ${info.duration}`;
    
    // Populate quality options
    elements.qualitySelect.innerHTML = '';
    info.qualities.forEach(q => {
        const option = document.createElement('option');
        option.value = q.id;
        option.textContent = q.label;
        elements.qualitySelect.appendChild(option);
    });
    
    showElement(elements.videoPreview);
    showElement(elements.qualitySection);
}

// Download Single Video
elements.downloadBtn.addEventListener('click', () => {
    const url = elements.videoUrl.value.trim();
    const quality = elements.qualitySelect.value;
    
    if (!url) {
        showToast('No video URL', 'error');
        return;
    }
    
    const downloadId = `single_${Date.now()}`;
    addToQueue(downloadId, currentVideoInfo?.title || 'Downloading...');
    
    socket.emit('start_download', {
        url,
        quality,
        id: downloadId
    });
    
    showToast('Download started!', 'info');
});

// Fetch Channel Videos
elements.fetchChannelBtn.addEventListener('click', async () => {
    const url = elements.channelUrl.value.trim();
    const maxVideos = parseInt(elements.maxVideos.value) || 10;
    
    if (!url) {
        showToast('Please enter a channel/playlist URL', 'error');
        return;
    }
    
    setButtonLoading(elements.fetchChannelBtn, true);
    hideElement(elements.videoList);
    
    try {
        const response = await fetch('/api/channel', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url, max_videos: maxVideos })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Failed to fetch videos');
        }
        
        channelVideos = data.videos;
        displayVideoList(data.videos);
        showToast(`Found ${data.count} videos!`, 'success');
        
    } catch (error) {
        showToast(error.message, 'error');
    } finally {
        setButtonLoading(elements.fetchChannelBtn, false);
    }
});

function displayVideoList(videos) {
    elements.videoCount.textContent = videos.length;
    elements.videosContainer.innerHTML = '';
    
    videos.forEach((video, index) => {
        const item = document.createElement('div');
        item.className = 'video-item';
        item.id = `video-item-${index}`;
        item.innerHTML = `
            <div class="video-item-thumb">
                <img src="${video.thumbnail || 'https://via.placeholder.com/120x68?text=No+Thumb'}" alt="${video.title}">
            </div>
            <div class="video-item-info">
                <div class="video-item-title" title="${video.title}">${video.title}</div>
                <div class="video-item-duration">${video.duration}</div>
            </div>
            <div class="video-item-status">⏳</div>
        `;
        elements.videosContainer.appendChild(item);
    });
    
    showElement(elements.videoList);
}

// Download All Videos
elements.downloadAllBtn.addEventListener('click', () => {
    if (channelVideos.length === 0) {
        showToast('No videos to download', 'error');
        return;
    }
    
    const quality = elements.batchQuality.value;
    const batchId = `batch_${Date.now()}`;
    
    addToQueue(batchId, `Batch Download (${channelVideos.length} videos)`);
    
    socket.emit('start_batch_download', {
        videos: channelVideos,
        quality,
        batch_id: batchId
    });
    
    showToast(`Starting batch download of ${channelVideos.length} videos`, 'info');
});

// Socket Event Handlers
socket.on('download_progress', (data) => {
    updateQueueItem(data.id || data.batch_id, {
        percent: data.percent,
        speed: data.speed,
        status: 'downloading'
    });
});

socket.on('download_complete', (data) => {
    updateQueueItem(data.id, {
        percent: 100,
        status: 'complete',
        filename: data.filename
    });
    showToast(`Downloaded: ${data.filename}`, 'success');
});

socket.on('download_error', (data) => {
    updateQueueItem(data.id, {
        status: 'error',
        error: data.error
    });
    showToast(`Download failed: ${data.error}`, 'error');
});

socket.on('batch_progress', (data) => {
    updateQueueItem(data.batch_id, {
        status: 'downloading',
        currentTitle: data.title,
        current: data.current,
        total: data.total
    });
    
    // Update video list item status
    const index = data.current - 1;
    const itemStatus = document.querySelector(`#video-item-${index} .video-item-status`);
    if (itemStatus) {
        itemStatus.textContent = '⬇️';
    }
});

socket.on('video_complete', (data) => {
    const match = data.video_id.match(/_(\d+)$/);
    if (match) {
        const index = parseInt(match[1]);
        const itemStatus = document.querySelector(`#video-item-${index} .video-item-status`);
        if (itemStatus) {
            itemStatus.textContent = data.success ? '✅' : '❌';
        }
    }
});

socket.on('batch_complete', (data) => {
    updateQueueItem(data.batch_id, {
        percent: 100,
        status: 'complete'
    });
    showToast('Batch download complete!', 'success');
});

// Queue Management
function addToQueue(id, title) {
    showElement(elements.downloadQueue);
    
    const item = document.createElement('div');
    item.className = 'queue-item';
    item.id = `queue-${id}`;
    item.innerHTML = `
        <div class="queue-item-header">
            <div class="queue-item-title">${title}</div>
            <div class="queue-item-status">Starting...</div>
        </div>
        <div class="progress-bar">
            <div class="progress-fill" style="width: 0%"></div>
        </div>
        <div class="queue-item-details">
            <span class="queue-speed"></span>
            <span class="queue-percent">0%</span>
        </div>
    `;
    elements.queueContainer.prepend(item);
}

function updateQueueItem(id, data) {
    const item = document.getElementById(`queue-${id}`);
    if (!item) return;
    
    const statusEl = item.querySelector('.queue-item-status');
    const progressFill = item.querySelector('.progress-fill');
    const speedEl = item.querySelector('.queue-speed');
    const percentEl = item.querySelector('.queue-percent');
    
    if (data.percent !== undefined) {
        progressFill.style.width = `${data.percent}%`;
        percentEl.textContent = `${Math.round(data.percent)}%`;
    }
    
    if (data.speed) {
        speedEl.textContent = data.speed;
    }
    
    if (data.status) {
        statusEl.className = `queue-item-status ${data.status}`;
        switch (data.status) {
            case 'downloading':
                if (data.current && data.total) {
                    statusEl.textContent = `Downloading ${data.current}/${data.total}`;
                } else {
                    statusEl.textContent = 'Downloading...';
                }
                break;
            case 'complete':
                statusEl.textContent = '✅ Complete';
                break;
            case 'error':
                statusEl.textContent = '❌ Error';
                break;
        }
    }
    
    if (data.filename) {
        item.querySelector('.queue-item-title').textContent = data.filename;
    }
}

// Utility Functions
function showElement(el) {
    el.classList.remove('hidden');
}

function hideElement(el) {
    el.classList.add('hidden');
}

function setButtonLoading(btn, loading) {
    if (loading) {
        btn.disabled = true;
        btn.dataset.originalText = btn.innerHTML;
        btn.innerHTML = '<div class="spinner"></div> Loading...';
    } else {
        btn.disabled = false;
        btn.innerHTML = btn.dataset.originalText;
    }
}

function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    const icons = {
        success: '✅',
        error: '❌',
        info: 'ℹ️'
    };
    
    toast.innerHTML = `
        <span>${icons[type] || 'ℹ️'}</span>
        <span>${message}</span>
    `;
    
    elements.toastContainer.appendChild(toast);
    
    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

// Enter key support for inputs
elements.videoUrl.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') elements.fetchBtn.click();
});

elements.channelUrl.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') elements.fetchChannelBtn.click();
});

// Log socket connection
socket.on('connect', () => {
    console.log('🔌 Connected to server');
});

socket.on('disconnect', () => {
    console.log('🔌 Disconnected from server');
    showToast('Connection lost. Reconnecting...', 'error');
});
