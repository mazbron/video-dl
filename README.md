# 🎬 Video Downloader

Download videos from YouTube, TikTok, and 1000+ platforms with CLI and Web UI.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

## ✨ Features

- 📹 **Single Video Download** - Paste URL, select quality, download
- 📁 **Channel/Playlist Download** - Mass download with max limit
- 🎚️ **Quality Selection** - Choose from available resolutions
- 🌐 **1000+ Platforms** - YouTube, TikTok, Twitter, Instagram, etc.
- 💻 **CLI & Web UI** - Use terminal or browser
- ⚡ **Real-time Progress** - Live download progress tracking

---

## 📦 Installation

### Prerequisites

1. **Python 3.8+**
   ```bash
   python --version
   ```

2. **FFmpeg** (required for merging video+audio)
   ```bash
   # Check if installed
   ffmpeg -version
   
   # Install via Chocolatey (Windows)
   choco install ffmpeg
   
   # Install via Scoop (Windows)
   scoop install ffmpeg
   
   # Install via apt (Linux)
   sudo apt install ffmpeg
   
   # Install via Homebrew (macOS)
   brew install ffmpeg
   ```

3. **Deno** (optional, removes yt-dlp warnings)
   ```bash
   # Windows PowerShell
   irm https://deno.land/install.ps1 | iex
   
   # Or via Scoop
   scoop install deno
   ```

### Install Dependencies

```bash
cd downloader
pip install -r requirements.txt
```

---

## 🚀 Usage

### CLI Mode

```bash
python cli.py
```

**Menu:**
```
=== Video Downloader ===
1. Download Single Video
2. Download Channel/Playlist
3. Settings
4. Exit
```

### Web UI Mode

```bash
python app.py
```

Open browser: **http://localhost:5000**

---

## 📁 Project Structure

```
downloader/
├── requirements.txt    # Dependencies
├── downloader.py       # Core download module
├── cli.py              # CLI interface
├── app.py              # Flask web server
├── templates/
│   └── index.html      # Web UI template
├── static/
│   ├── style.css       # Styling
│   └── app.js          # Frontend logic
└── downloads/          # Downloaded files
```

---

## 🎯 Supported Platforms

Powered by [yt-dlp](https://github.com/yt-dlp/yt-dlp), supporting:

| Platform | Status |
|----------|--------|
| YouTube | ✅ |
| YouTube Shorts | ✅ |
| TikTok | ✅ |
| Twitter/X | ✅ |
| Instagram | ✅ |
| Facebook | ✅ |
| Vimeo | ✅ |
| Twitch | ✅ |
| [1000+ more...](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md) | ✅ |

---

## ⚙️ Configuration

Default settings (can be changed in CLI Settings menu):

| Setting | Default |
|---------|---------|
| Download Directory | `./downloads` |
| Default Quality | `best` |
| Max Videos (Channel) | `10` |

---

## 🐛 Troubleshooting

### No Audio in Windows Media Player
Videos are re-encoded to AAC audio for compatibility. If still no audio, try VLC player.

### yt-dlp Warnings
```
WARNING: No supported JavaScript runtime could be found
```
Install Deno to fix: `scoop install deno`

### Download Failed
- Check internet connection
- Update yt-dlp: `pip install -U yt-dlp`
- Verify URL is correct

---

## 📄 License

MIT License - feel free to use and modify!
