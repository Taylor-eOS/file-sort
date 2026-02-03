import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
import os
import shutil
from zipfile import ZipFile
from io import BytesIO
from PIL import Image, ImageTk

class FileSorterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Quick File Bucketer")
        self.root.geometry("820x720")
        self.source_dir = ""
        self.files = []
        self.current_idx = 0
        self.num_buckets = 5
        self.target_dirs = {}
        self.photo = None
        self.label_info = tk.Label(root, text="Source folder not selected yet", font=("Segoe UI", 11))
        self.label_info.pack(pady=12)
        self.btn_choose = tk.Label(root, text="Click to choose folder to sort", fg="blue", cursor="hand2", font=("Segoe UI", 12))
        self.btn_choose.pack(pady=6)
        self.btn_choose.bind("<Button-1>", self.choose_folder)
        self.label_status = tk.Label(root, text="", font=("Consolas", 10), fg="#555")
        self.label_status.pack(pady=10)
        self.img_frame = tk.Frame(root, bg="#f8f8f8", width=780, height=560)
        self.img_frame.pack(pady=8, fill="both", expand=False)
        self.img_frame.pack_propagate(False)
        self.img_label = tk.Label(self.img_frame, bg="#f8f8f8")
        self.img_label.pack(expand=True)
        self.label_filename = tk.Label(root, text="", font=("Segoe UI", 11), wraplength=780)
        self.label_filename.pack(pady=6)
        self.label_progress = tk.Label(root, text="", font=("Segoe UI", 10))
        self.label_progress.pack(pady=4)
        self.root.bind("<KeyPress>", self.on_key)
        self.show_start_screen()

    def show_start_screen(self):
        self.img_label.config(image="")
        self.img_label.config(text="")
        self.label_filename.config(text="")
        self.label_progress.config(text="")
        self.label_status.config(text="Press any key or click above to start →")

    def choose_folder(self, event=None):
        folder = filedialog.askdirectory(title="Select folder with files to sort")
        if not folder:
            return
        self.source_dir = folder
        self.label_info.config(text=f"Folder: {folder}")
        try:
            self.files = [f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))]
            self.files.sort()
        except Exception as e:
            messagebox.showerror("Error", f"Cannot read folder\n{e}")
            return
        if not self.files:
            messagebox.showinfo("Info", "No files found in selected folder")
            return
        self.ask_number_of_buckets()

    def ask_number_of_buckets(self):
        while True:
            answer = simpledialog.askstring("Number of buckets", "How many buckets do you want? (2–9 recommended)", initialvalue="5", parent=self.root)
            if answer is None:
                self.root.quit()
                return
            try:
                n = int(answer.strip())
                if 2 <= n <= 9:
                    self.num_buckets = n
                    self.prepare_buckets()
                    self.next_file()
                    return
                else:
                    messagebox.showwarning("Invalid", "Please choose a number between 2 and 9")
            except ValueError:
                messagebox.showwarning("Invalid", "Please enter a valid number")

    def prepare_buckets(self):
        base = self.source_dir.rstrip(os.sep) + "_sorted"
        os.makedirs(base, exist_ok=True)
        self.target_dirs = {}
        for i in range(1, self.num_buckets + 1):
            d = os.path.join(base, str(i))
            os.makedirs(d, exist_ok=True)
            self.target_dirs[str(i)] = d
        if self.num_buckets < 10:
            self.label_status.config(text=f"Press 1–{self.num_buckets} to move file • Esc = quit")
        else:
            self.label_status.config(text="Press 1–9 to move file • Esc = quit")

    def on_key(self, event):
        if event.keysym == "Escape":
            self.root.quit()
            return
        if not self.files or self.current_idx >= len(self.files):
            return
        key = event.char
        if key in self.target_dirs:
            self.move_current_file(key)

    def move_current_file(self, bucket_key):
        current_path = os.path.join(self.source_dir, self.files[self.current_idx])
        target_folder = self.target_dirs[bucket_key]
        target_path = os.path.join(target_folder, self.files[self.current_idx])
        try:
            shutil.copy2(current_path, target_path)
        except Exception as e:
            messagebox.showerror("Error", f"Cannot copy file\n{e}")
            return
        self.current_idx += 1
        self.label_progress.config(text=f"{self.current_idx}/{len(self.files)} files processed")
        self.next_file()

    def next_file(self):
        if self.current_idx >= len(self.files):
            self.label_filename.config(text="All files processed.")
            self.img_label.config(image="", text="")
            self.label_status.config(text="Done. You can close the window.")
            return
        fname = self.files[self.current_idx]
        fullpath = os.path.join(self.source_dir, fname)
        self.label_filename.config(text=fname)
        self.photo = None
        loaded = False
        if fname.lower().endswith(".epub"):
            loaded = self.try_load_epub_cover(fullpath)
        else:
            loaded = self.try_load_image(fullpath)
        if loaded:
            self.img_label.config(image=self.photo, text="")
        else:
            self.img_label.config(image="", text=fname, font=("Segoe UI", 28, "bold"), fg="#444")

    def try_load_image(self, path):
        try:
            img = Image.open(path)
            img.thumbnail((760, 560))
            self.photo = ImageTk.PhotoImage(img)
            return True
        except:
            return False

    def try_load_epub_cover(self, epub_path):
        try:
            with ZipFile(epub_path) as zf:
                for name in zf.namelist():
                    low = name.lower()
                    if "cover" in low and (low.endswith(".jpg") or low.endswith(".jpeg") or low.endswith(".png")):
                        data = zf.read(name)
                        img = Image.open(BytesIO(data))
                        img.thumbnail((760, 560))
                        self.photo = ImageTk.PhotoImage(img)
                        return True
                for name in zf.namelist():
                    low = name.lower()
                    if low.endswith(".jpg") or low.endswith(".jpeg") or low.endswith(".png"):
                        data = zf.read(name)
                        img = Image.open(BytesIO(data))
                        img.thumbnail((760, 560))
                        self.photo = ImageTk.PhotoImage(img)
                        return True
        except:
            pass
        return False

if __name__ == "__main__":
    root = tk.Tk()
    app = FileSorterApp(root)
    root.mainloop()

