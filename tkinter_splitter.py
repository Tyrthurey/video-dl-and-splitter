import tkinter as tk
from tkinter import filedialog, scrolledtext, simpledialog, ttk
from moviepy.editor import VideoFileClip
from pytube import YouTube
from pytube.cli import on_progress
import os
import re

# Function to handle mousewheel scrolling
def _on_mousewheel(event):
    canvas.yview_scroll(int(-1*(event.delta/120)), "units")

def time_to_seconds(hours, minutes, seconds):
    return int(hours) * 3600 + int(minutes) * 60 + int(seconds)

def select_video():
    global video_path
    video_path = filedialog.askopenfilename(filetypes=[("Video files", "*.mp4 *.mkv")])
    if video_path:
        video_label.config(text=os.path.basename(video_path))

def download_youtube_video():
    youtube_link = simpledialog.askstring("YouTube Link", "Enter YouTube video link:")
    if youtube_link:
        yt = YouTube(youtube_link, on_progress_callback=on_progress)
        video_stream = yt.streams.filter(file_extension='mp4').first()
        global video_path
        video_path = video_stream.download()
        video_label.config(text=os.path.basename(video_path))

        # If time frames are set, start processing immediately
        if any(entry.get() for frame in time_frame_entries for entry in frame):
            start_processing()
        
def start_processing():
    if not video_path:
        return

    video = VideoFileClip(video_path)
    video_duration = video.duration

    for i, (start_h, start_m, start_s, end_h, end_m, end_s) in enumerate(time_frame_entries):
        # Ensure all parts of the time frame are filled
        if all(part.get().isdigit() for part in [start_h, start_m, start_s, end_h, end_m, end_s]):
            start_time = time_to_seconds(start_h.get(), start_m.get(), start_s.get())
            end_time = time_to_seconds(end_h.get(), end_m.get(), end_s.get())

            # Validate time frames
            if start_time >= video_duration or end_time > video_duration or start_time >= end_time:
                print(f"Skipping invalid time frame: Clip-{i+1}")
                continue

            clip = video.subclip(start_time, end_time)
            clip.write_videofile(f'Clip-{i+1}.mp4', codec="libx264", audio_codec="aac")
        else:
            print(f"Skipping incomplete time frame: Clip-{i+1}")

    video.close()



def detect_times():
    text = detect_field.get("1.0", tk.END)
    pattern = r'\)\s*(\d+[:.]\d+)[-–](\d+[:.]\d+)'
    matches = re.findall(pattern, text)

    for i, (start, end) in enumerate(matches):
        if i < len(time_frame_entries):
            # Replacing dots with colons and splitting
            start_parts = start.replace('.', ':').split(':')
            end_parts = end.replace('.', ':').split(':')

            # Adjusting for MM:SS format
            if len(start_parts) == 2:
                start_parts.insert(0, '0')  # Inserting '0' for hours if missing
            if len(end_parts) == 2:
                end_parts.insert(0, '0')    # Inserting '0' for hours if missing

            start_h, start_m, start_s = start_parts
            end_h, end_m, end_s = end_parts

            start_h_entry, start_m_entry, start_s_entry, end_h_entry, end_m_entry, end_s_entry = time_frame_entries[i]
            start_h_entry.delete(0, tk.END)
            start_h_entry.insert(0, start_h)
            start_m_entry.delete(0, tk.END)
            start_m_entry.insert(0, start_m)
            start_s_entry.delete(0, tk.END)
            start_s_entry.insert(0, start_s)
            end_h_entry.delete(0, tk.END)
            end_h_entry.insert(0, end_h)
            end_m_entry.delete(0, tk.END)
            end_m_entry.insert(0, end_m)
            end_s_entry.delete(0, tk.END)
            end_s_entry.insert(0, end_s)



def create_time_frame_entry(parent, number):
    frame = tk.Frame(parent)
    tk.Label(frame, text=f"Clip {number} - Start:").pack(side=tk.LEFT)
    start_h = tk.Entry(frame, width=3)
    start_h.insert(0, "0")
    start_h.pack(side=tk.LEFT)
    tk.Label(frame, text=":").pack(side=tk.LEFT)
    start_m = tk.Entry(frame, width=3)
    start_m.pack(side=tk.LEFT)
    tk.Label(frame, text=":").pack(side=tk.LEFT)
    start_s = tk.Entry(frame, width=3)
    start_s.pack(side=tk.LEFT)

    tk.Label(frame, text=" - End:").pack(side=tk.LEFT)
    end_h = tk.Entry(frame, width=3)
    end_h.insert(0, "0")
    end_h.pack(side=tk.LEFT)
    tk.Label(frame, text=":").pack(side=tk.LEFT)
    end_m = tk.Entry(frame, width=3)
    end_m.pack(side=tk.LEFT)
    tk.Label(frame, text=":").pack(side=tk.LEFT)
    end_s = tk.Entry(frame, width=3)
    end_s.pack(side=tk.LEFT)

    return frame, (start_h, start_m, start_s, end_h, end_m, end_s)

app = tk.Tk()
app.title("Video Clipper")
app.geometry("600x500")
app.iconbitmap('youtube.ico')

# Style configuration for buttons
style = ttk.Style()
style.configure('TButton', padding=6, relief="flat", background="#ccc")

# Scrollable frame setup
canvas = tk.Canvas(app)
scrollbar = ttk.Scrollbar(app, orient="vertical", command=canvas.yview)
scrollable_frame = ttk.Frame(canvas)

# Bind mousewheel scrolling
scrollable_frame.bind("<Enter>", lambda _: canvas.bind_all("<MouseWheel>", _on_mousewheel))
scrollable_frame.bind("<Leave>", lambda _: canvas.unbind_all("<MouseWheel>"))

scrollable_frame.bind(
    "<Configure>",
    lambda e: canvas.configure(
        scrollregion=canvas.bbox("all")
    )
)

canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
canvas.configure(yscrollcommand=scrollbar.set)

canvas.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")

# Time frame entries
time_frame_entries = []
for i in range(30):  # Change this number to show more/less initial entries
    frame, entries = create_time_frame_entry(scrollable_frame, i+1)
    frame.pack(pady=2)  # Add padding for space between time entries
    time_frame_entries.append(entries)

# Detect Field
detect_label = tk.Label(app, text="Paste Times Here:")
detect_label.pack()
detect_field = scrolledtext.ScrolledText(app, height=10, width=50)
detect_field.pack()


video_path = ''
video_label = tk.Label(app, text="No video selected")
video_label.pack()


# Configuring and packing buttons with style and padding
detect_button = ttk.Button(app, text="Detect", command=detect_times, style='TButton')
detect_button.pack(pady=10)

youtube_button = ttk.Button(app, text="Download from YouTube", command=download_youtube_video, style='TButton')
youtube_button.pack(pady=10)

select_button = ttk.Button(app, text="Select Video", command=select_video, style='TButton')
select_button.pack(pady=10)

start_button = ttk.Button(app, text="Start", command=start_processing, style='TButton')
start_button.pack(pady=10)

app.mainloop()
