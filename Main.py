import threading
import os
import tempfile
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import pdfplumber
from gtts import gTTS
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips
from pdf2image import convert_from_path
from PIL import ImageTk, Image


# ------------------------------------------------------------------

def extract_text(pdf_path):
    """Return the full text of the PDF (pages joined with newlines)."""
    text_pages = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            txt = page.extract_text()
            if txt:
                text_pages.append(txt)
    return "\n".join(text_pages)


def make_mp3(text, output_path, lang="en"):
    """Generate an MP3 file from text using gTTS."""
    tts = gTTS(text=text, lang=lang)
    tts.save(output_path)
    return output_path


def make_page_images(pdf_path, dpi=150):
    """Return a list of file paths to images (one per PDF page)."""
    images = convert_from_path(pdf_path, dpi=dpi)
    out_files = []
    for i, img in enumerate(images, start=1):
        fname = os.path.join(tempfile.gettempdir(), f"page_{i}.png")
        img.save(fname, "PNG")
        out_files.append(fname)
    return out_files


def make_mp4(page_images, audio_path, output_path, fps=24, secs_per_page=3):
    """Combine page images and audio into a simple MP4 slideshow."""
    clips = []
    for img in page_images:
        clip = ImageClip(img).set_duration(secs_per_page)
        clips.append(clip)
    video = concatenate_videoclips(clips).set_audio(AudioFileClip(audio_path))
    video.write_videofile(output_path, fps=fps)
    return output_path

class ConverterApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("PDF to MP3/MP4 Converter")
        self.geometry("450x350")
        self.iconbitmap("Images/face-angry.ico")
        self.iconwindow = ImageTk.PhotoImage(Image.open("Images/face-angry.png"))
        self.pdf_path = tk.StringVar()
        self.make_mp3_var = tk.BooleanVar(value=True)
        self.make_mp4_var = tk.BooleanVar(value=False)

        self._build_widgets()

    def _build_widgets(self):
        ttk.Label(self, text="Select PDF:").pack(anchor="w", padx=10, pady=(10,0))
        frame = ttk.Frame(self)
        frame.pack(fill="x", padx=10)
        ttk.Entry(frame, textvariable=self.pdf_path, width=40).pack(side="left")
        ttk.Button(frame, text="Browse…", command=self.browse).pack(side="left", padx=5)

        ttk.Checkbutton(self, text="Create MP3", variable=self.make_mp3_var).pack(anchor="w", padx=10, pady=(10,0))
        ttk.Checkbutton(self, text="Create MP4", variable=self.make_mp4_var).pack(anchor="w", padx=10)

        ttk.Label(self, text="Voice language code (gTTS):").pack(anchor="w", padx=10, pady=(10,0))
        self.lang_entry = ttk.Entry(self)
        self.lang_entry.insert(0, "en")
        self.lang_entry.pack(padx=10, fill="x")

        self.convert_button = ttk.Button(self, text="Convert", command=self.start_conversion)
        self.convert_button.pack(pady=15)

        self.status = ttk.Label(self, text="", foreground="blue")
        self.status.pack(pady=(5,0))

        self.progress = ttk.Progressbar(self, mode="indeterminate")
        self.progress.pack(fill="x", padx=10, pady=(5,10))

    def browse(self):
        path = filedialog.askopenfilename(filetypes=[("PDF files","*.pdf")],
                                          title="Select PDF")
        if path:
            self.pdf_path.set(path)

    def start_conversion(self):
        pdf = self.pdf_path.get()
        if not pdf:
            messagebox.showwarning("No file", "Please select a PDF first.")
            return
        if not (self.make_mp3_var.get() or self.make_mp4_var.get()):
            messagebox.showwarning("Nothing to do", "Choose at least one output format.")
            return

        self.convert_button.config(state="disabled")
        self.status.config(text="Working…")
        self.progress.start(10)

        thread = threading.Thread(target=self._do_conversion, args=(pdf,))
        thread.start()

    def _do_conversion(self, pdf_path):
        try:
            base = os.path.splitext(os.path.basename(pdf_path))[0]
            outdir = filedialog.askdirectory(title="Select output folder")
            if not outdir:
                raise RuntimeError("No output directory chosen")

            text = extract_text(pdf_path)
            lang = self.lang_entry.get().strip() or "en"
            mp3_path = os.path.join(outdir, f"{base}.mp3")
            mp4_path = os.path.join(outdir, f"{base}.mp4")

            if self.make_mp3_var.get():
                make_mp3(text, mp3_path, lang=lang)

            if self.make_mp4_var.get():
                imgs = make_page_images(pdf_path)
                # use the MP3 we just created (or make a temporary one if mp3 wasn't requested)
                audio_for_video = mp3_path if self.make_mp3_var.get() else make_mp3(text, mp3_path, lang=lang)
                make_mp4(imgs, audio_for_video, mp4_path)

            self._update_status("Done!")
        except Exception as exc:
            self._update_status(f"Error: {exc}")
        finally:
            self.progress.stop()
            self.convert_button.config(state="normal")

    def _update_status(self, msg):
        self.status.config(text=msg)

if __name__ == "__main__":

    ConverterApp().mainloop()

