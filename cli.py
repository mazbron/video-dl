"""
CLI Video Downloader
Interactive command-line interface for downloading videos
"""
import os
import sys
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeRemainingColumn
from rich.prompt import Prompt, IntPrompt, Confirm
from rich import print as rprint
from downloader import VideoDownloader, DownloadProgress, format_bytes, format_duration


console = Console()


def clear_screen():
    """Clear terminal screen"""
    os.system('cls' if os.name == 'nt' else 'clear')


def print_banner():
    """Print application banner"""
    banner = """
██╗   ██╗██╗██████╗ ███████╗ ██████╗     ██████╗ ██╗     
██║   ██║██║██╔══██╗██╔════╝██╔═══██╗    ██╔══██╗██║     
██║   ██║██║██║  ██║█████╗  ██║   ██║    ██║  ██║██║     
╚██╗ ██╔╝██║██║  ██║██╔══╝  ██║   ██║    ██║  ██║██║     
 ╚████╔╝ ██║██████╔╝███████╗╚██████╔╝    ██████╔╝███████╗
  ╚═══╝  ╚═╝╚═════╝ ╚══════╝ ╚═════╝     ╚═════╝ ╚══════╝
    """
    console.print(Panel(banner, title="[bold cyan]Video Downloader[/]", subtitle="[dim]Powered by yt-dlp[/]"))


def show_main_menu() -> int:
    """Display main menu and get user choice"""
    console.print("\n[bold yellow]📋 Main Menu[/]\n")
    
    menu_items = [
        ("1", "Download Single Video", "📹"),
        ("2", "Download Channel/Playlist", "📁"),
        ("3", "Settings", "⚙️"),
        ("4", "Exit", "🚪"),
    ]
    
    table = Table(show_header=False, box=None, padding=(0, 2))
    for num, text, emoji in menu_items:
        table.add_row(f"[cyan]{num}[/]", f"{emoji} {text}")
    
    console.print(table)
    console.print()
    
    while True:
        try:
            choice = IntPrompt.ask("[bold green]Pilih menu[/]", choices=["1", "2", "3", "4"])
            return choice
        except:
            console.print("[red]Input tidak valid! Masukkan angka 1-4[/]")


def download_single_video(downloader: VideoDownloader, default_quality: str):
    """Download single video flow"""
    console.print("\n[bold cyan]📹 Download Single Video[/]\n")
    
    # Get URL
    url = Prompt.ask("[yellow]Paste URL video[/]")
    
    if not url:
        console.print("[red]URL tidak boleh kosong![/]")
        return
    
    # Get video info
    with console.status("[bold green]Mengambil info video..."):
        info = downloader.get_video_info(url)
    
    if not info:
        console.print("[red]Gagal mengambil info video. Cek URL atau koneksi internet.[/]")
        return
    
    # Display video info
    console.print(Panel(
        f"[bold]{info.title}[/]\n"
        f"[dim]Uploader:[/] {info.uploader}\n"
        f"[dim]Durasi:[/] {format_duration(info.duration)}",
        title="[cyan]Video Info[/]"
    ))
    
    # Get quality options
    with console.status("[bold green]Mengambil opsi kualitas..."):
        qualities = downloader.get_quality_options(url)
    
    if not qualities:
        console.print("[yellow]Tidak bisa mendapatkan opsi kualitas, menggunakan default...[/]")
        quality = default_quality
    else:
        # Show quality options
        console.print("\n[bold yellow]🎬 Pilih Kualitas:[/]\n")
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("No", style="cyan", width=4)
        table.add_column("Kualitas", style="white")
        
        for i, q in enumerate(qualities, 1):
            table.add_row(str(i), q['label'])
        
        console.print(table)
        
        # Get quality choice
        while True:
            try:
                choice = IntPrompt.ask(
                    f"\n[green]Pilih kualitas[/]", 
                    default=1
                )
                if 1 <= choice <= len(qualities):
                    quality = qualities[choice - 1]['id']
                    break
                else:
                    console.print(f"[red]Pilih angka 1-{len(qualities)}[/]")
            except:
                console.print("[red]Input tidak valid![/]")
    
    # Download with progress
    console.print(f"\n[bold green]⬇️ Memulai download...[/]\n")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TextColumn("•"),
        TextColumn("{task.fields[speed]}"),
        TextColumn("•"),
        TimeRemainingColumn(),
        console=console
    ) as progress:
        task = progress.add_task("[cyan]Downloading...", total=100, speed="-- KB/s")
        
        def update_progress(p: DownloadProgress):
            speed_str = format_bytes(p.speed) + "/s" if p.speed else "-- KB/s"
            progress.update(task, completed=p.percent, speed=speed_str)
        
        downloader.set_progress_callback(update_progress)
        result = downloader.download_video(url, quality)
    
    if result:
        console.print(f"\n[bold green]✅ Download selesai![/]")
        console.print(f"[dim]File: {result}[/]")
    else:
        console.print("\n[bold red]❌ Download gagal![/]")
    
    Prompt.ask("\n[dim]Tekan Enter untuk kembali ke menu...[/]")


def download_channel_playlist(downloader: VideoDownloader, default_quality: str, default_max: int):
    """Download channel/playlist flow"""
    console.print("\n[bold cyan]📁 Download Channel/Playlist[/]\n")
    
    # Get URL
    url = Prompt.ask("[yellow]Paste URL channel/playlist[/]")
    
    if not url:
        console.print("[red]URL tidak boleh kosong![/]")
        return
    
    # Get max videos
    max_videos = IntPrompt.ask(
        "[yellow]Maksimal video yang didownload[/]", 
        default=default_max
    )
    
    # Get video list
    console.print()
    with console.status("[bold green]Mengambil daftar video..."):
        videos = downloader.get_channel_videos(url, max_videos)
    
    if not videos:
        console.print("[red]Tidak dapat menemukan video. Cek URL.[/]")
        return
    
    # Display video list
    console.print(f"\n[bold green]Ditemukan {len(videos)} video:[/]\n")
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("No", style="cyan", width=4)
    table.add_column("Title", style="white", max_width=60)
    table.add_column("Duration", style="dim", width=10)
    
    for i, video in enumerate(videos, 1):
        duration = format_duration(video['duration']) if video['duration'] else "--:--"
        title = video['title'][:57] + "..." if len(video['title']) > 60 else video['title']
        table.add_row(str(i), title, duration)
    
    console.print(table)
    
    # Confirm download
    if not Confirm.ask(f"\n[yellow]Download {len(videos)} video?[/]"):
        return
    
    # Get quality
    console.print("\n[bold yellow]🎬 Pilih Kualitas:[/]")
    quality_presets = [
        ('best', 'Best Quality'),
        ('bestvideo[height<=1080]+bestaudio/best[height<=1080]', '1080p'),
        ('bestvideo[height<=720]+bestaudio/best[height<=720]', '720p'),
        ('bestvideo[height<=480]+bestaudio/best[height<=480]', '480p'),
        ('bestaudio', 'Audio Only'),
    ]
    
    for i, (_, label) in enumerate(quality_presets, 1):
        console.print(f"  [cyan]{i}[/]. {label}")
    
    quality_choice = IntPrompt.ask("\n[green]Pilih kualitas[/]", default=1)
    quality = quality_presets[min(quality_choice, len(quality_presets)) - 1][0]
    
    # Download all
    console.print(f"\n[bold green]⬇️ Memulai download {len(videos)} video...[/]\n")
    
    downloaded = 0
    failed = 0
    
    for i, video in enumerate(videos, 1):
        console.print(f"[cyan][{i}/{len(videos)}][/] {video['title'][:50]}...")
        
        with Progress(
            SpinnerColumn(),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TextColumn("{task.fields[speed]}"),
            console=console,
            transient=True
        ) as progress:
            task = progress.add_task("Downloading", total=100, speed="")
            
            def update_progress(p: DownloadProgress):
                speed_str = format_bytes(p.speed) + "/s" if p.speed else ""
                progress.update(task, completed=p.percent, speed=speed_str)
            
            downloader.set_progress_callback(update_progress)
            result = downloader.download_video(video['url'], quality)
        
        if result:
            console.print(f"  [green]✅ Done[/]")
            downloaded += 1
        else:
            console.print(f"  [red]❌ Failed[/]")
            failed += 1
    
    console.print(f"\n[bold]Download selesai![/]")
    console.print(f"  [green]✅ Berhasil: {downloaded}[/]")
    if failed:
        console.print(f"  [red]❌ Gagal: {failed}[/]")
    
    Prompt.ask("\n[dim]Tekan Enter untuk kembali ke menu...[/]")


def settings_menu(current_quality: str, current_max: int, current_dir: str):
    """Settings menu"""
    console.print("\n[bold cyan]⚙️ Settings[/]\n")
    
    table = Table(show_header=False, box=None)
    table.add_column("Setting", style="yellow")
    table.add_column("Value", style="white")
    
    table.add_row("1. Default Quality", current_quality)
    table.add_row("2. Max Videos (Channel)", str(current_max))
    table.add_row("3. Download Directory", current_dir)
    table.add_row("4. Back to Menu", "")
    
    console.print(table)
    
    choice = IntPrompt.ask("\n[green]Pilih setting untuk diubah[/]", default=4)
    
    if choice == 1:
        options = ['best', '1080p', '720p', '480p', 'audio']
        for i, opt in enumerate(options, 1):
            console.print(f"  {i}. {opt}")
        q = IntPrompt.ask("Pilih default quality", default=1)
        return (options[q-1], current_max, current_dir)
    elif choice == 2:
        new_max = IntPrompt.ask("Max videos", default=current_max)
        return (current_quality, new_max, current_dir)
    elif choice == 3:
        new_dir = Prompt.ask("Download directory", default=current_dir)
        return (current_quality, current_max, new_dir)
    
    return (current_quality, current_max, current_dir)


def main():
    """Main entry point"""
    # Default settings
    download_dir = "downloads"
    default_quality = "best"
    default_max = 10
    
    # Create downloader
    downloader = VideoDownloader(download_dir)
    
    while True:
        clear_screen()
        print_banner()
        
        choice = show_main_menu()
        
        if choice == 1:
            download_single_video(downloader, default_quality)
        elif choice == 2:
            download_channel_playlist(downloader, default_quality, default_max)
        elif choice == 3:
            default_quality, default_max, download_dir = settings_menu(
                default_quality, default_max, download_dir
            )
            downloader = VideoDownloader(download_dir)
        elif choice == 4:
            console.print("\n[bold cyan]👋 Goodbye![/]\n")
            sys.exit(0)


if __name__ == "__main__":
    main()
