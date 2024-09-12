import tkinter as tk
from tkinter import filedialog, ttk, messagebox, colorchooser
import cv2
import numpy as np
import pyautogui
import threading
import os
import random
import string

class ScreenRecorderApp:
    def __init__(self, master):
        self.master = master
        self.master.title("PyScreen")
        self.master.geometry("450x500")
        self.is_recording = False
        self.output_path = ""
        self.output_filename = ""
        self.fps = 20
        self.record_audio = False
        self.highlight_mouse = False
        self.highlight_color = (0, 255, 0)
        self.highlight_radius = 20
        self.custom_cursor = np.zeros((16, 16, 4), dtype=np.uint8)
        self.use_custom_cursor = False
        self.create_widgets()

    def create_widgets(self):
        style = ttk.Style()
        style.configure("TButton", padding=5, font=("Arial", 10))
        style.configure("TCheckbutton", font=("Arial", 10))
        style.configure("TLabel", font=("Arial", 10))

        main_frame = ttk.Frame(self.master, padding="20 20 20 20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=10, fill=tk.X)
        self.start_button = ttk.Button(
            button_frame, text="Start Recording", command=self.toggle_recording
        )
        self.start_button.pack(side=tk.LEFT, expand=True, padx=(0, 5))
        self.path_button = ttk.Button(
            button_frame, text="Select Output Path", command=self.select_output_path
        )
        self.path_button.pack(side=tk.LEFT, expand=True, padx=(5, 0))

        options_frame = ttk.LabelFrame(main_frame, text="Options", padding="10 10 10 10")
        options_frame.pack(pady=10, padx=10, fill="x")

        fps_frame = ttk.Frame(options_frame)
        fps_frame.pack(fill=tk.X, pady=5)
        ttk.Label(fps_frame, text="FPS:").pack(side=tk.LEFT, padx=(0, 5))
        self.fps_entry = ttk.Entry(fps_frame, width=5)
        self.fps_entry.insert(0, str(self.fps))
        self.fps_entry.pack(side=tk.LEFT)

        filename_frame = ttk.Frame(options_frame)
        filename_frame.pack(fill=tk.X, pady=5)
        ttk.Label(filename_frame, text="Filename:").pack(side=tk.LEFT, padx=(0, 5))
        self.filename_entry = ttk.Entry(filename_frame)
        self.filename_entry.pack(side=tk.LEFT, expand=True, fill=tk.X)

        self.audio_var = tk.BooleanVar()
        self.audio_checkbox = ttk.Checkbutton(
            options_frame, text="Record Audio", variable=self.audio_var
        )
        self.audio_checkbox.pack(anchor=tk.W, pady=5)

        self.highlight_mouse_var = tk.BooleanVar()
        self.highlight_mouse_checkbox = ttk.Checkbutton(
            options_frame, text="Highlight Mouse", variable=self.highlight_mouse_var
        )
        self.highlight_mouse_checkbox.pack(anchor=tk.W, pady=5)

        self.custom_cursor_var = tk.BooleanVar()
        self.custom_cursor_checkbox = ttk.Checkbutton(
            options_frame, text="Use Custom Cursor", variable=self.custom_cursor_var,
            command=self.toggle_custom_cursor
        )
        self.custom_cursor_checkbox.pack(anchor=tk.W, pady=5)

        self.draw_cursor_button = ttk.Button(
            options_frame, text="Draw Custom Cursor", command=self.open_cursor_drawer
        )
        self.draw_cursor_button.pack(anchor=tk.W, pady=5)

        self.status_label = ttk.Label(main_frame, text="Not Recording")
        self.status_label.pack(pady=10)

        self.progress_bar = ttk.Progressbar(main_frame, mode="indeterminate")
        self.progress_bar.pack(fill="x", padx=10, pady=10)

        self.output_label = ttk.Label(main_frame, text="Output: Not selected", wraplength=400)
        self.output_label.pack(pady=10)

        developer_label = ttk.Label(main_frame, text="Developer: https://daradege.github.io")
        developer_label.pack(pady=10)

    def select_output_path(self):
        self.output_path = filedialog.askdirectory()
        if self.output_path:
            self.output_label.config(text=f"Output Path: {self.output_path}")

    def generate_random_filename(self):
        random_string = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        return f"pyscreen_{random_string}.avi"

    def toggle_recording(self):
        if not self.is_recording:
            if not self.output_path:
                messagebox.showerror("Error", "Please select an output path first")
                return
            try:
                self.fps = int(self.fps_entry.get())
                if self.fps <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Error", "Please enter a valid positive integer for FPS")
                return

            self.output_filename = self.filename_entry.get().strip()
            if not self.output_filename:
                self.output_filename = self.generate_random_filename()
            elif not self.output_filename.endswith('.avi'):
                self.output_filename += '.avi'

            self.output_file = os.path.join(self.output_path, self.output_filename)

            self.is_recording = True
            self.start_button.config(text="Stop Recording")
            self.status_label.config(text="Recording...")
            self.progress_bar.start()
            self.record_audio = self.audio_var.get()
            self.highlight_mouse = self.highlight_mouse_var.get()
            self.use_custom_cursor = self.custom_cursor_var.get()
            threading.Thread(target=self.record_screen, daemon=True).start()
        else:
            self.is_recording = False
            self.start_button.config(text="Start Recording")
            self.status_label.config(text="Recording Stopped")
            self.progress_bar.stop()

    def record_screen(self):
        screen_size = pyautogui.size()
        fourcc = cv2.VideoWriter_fourcc(*"XVID")
        out = cv2.VideoWriter(self.output_file, fourcc, self.fps, screen_size)
        while self.is_recording:
            img = pyautogui.screenshot()
            frame = np.array(img)
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

            mouse_x, mouse_y = pyautogui.position()
            if self.highlight_mouse:
                if self.use_custom_cursor:
                    h, w = self.custom_cursor.shape[:2]
                    cursor_area = frame[mouse_y:mouse_y+h, mouse_x:mouse_x+w]
                    alpha_cursor = self.custom_cursor[:, :, 3] / 255.0
                    alpha_frame = 1.0 - alpha_cursor
                    for c in range(3):
                        cursor_area[:, :, c] = (alpha_cursor * self.custom_cursor[:, :, c] +
                                                alpha_frame * cursor_area[:, :, c])
                    frame[mouse_y:mouse_y+h, mouse_x:mouse_x+w] = cursor_area
                else:
                    cv2.circle(
                        frame,
                        (mouse_x, mouse_y),
                        self.highlight_radius,
                        self.highlight_color,
                        2,
                    )
            else:
                cv2.circle(frame, (mouse_x, mouse_y), 3, (0, 0, 255), -1)

            out.write(frame)
        out.release()
        self.master.after(0, self.show_completion_message)

    def show_completion_message(self):
        messagebox.showinfo("Recording Complete", f"Screen recording saved to:\n{self.output_file}")

    def toggle_custom_cursor(self):
        self.use_custom_cursor = self.custom_cursor_var.get()

    def open_cursor_drawer(self):
        cursor_drawer = CursorDrawer(self.master, self)
        cursor_drawer.grab_set()

class CursorDrawer(tk.Toplevel):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.title("Custom Cursor Drawer")
        self.geometry("320x400")
        self.resizable(False, False)

        self.canvas = tk.Canvas(self, width=256, height=256, bg="white")
        self.canvas.pack(pady=10)

        self.color_button = ttk.Button(self, text="Choose Color", command=self.choose_color)
        self.color_button.pack(pady=5)

        self.clear_button = ttk.Button(self, text="Clear", command=self.clear_canvas)
        self.clear_button.pack(pady=5)

        self.save_button = ttk.Button(self, text="Save", command=self.save_cursor)
        self.save_button.pack(pady=5)

        self.current_color = "black"
        self.setup_canvas()

    def setup_canvas(self):
        self.canvas.delete("all")
        for i in range(17):
            self.canvas.create_line(i*16, 0, i*16, 256, fill="lightgray")
            self.canvas.create_line(0, i*16, 256, i*16, fill="lightgray")
        self.canvas.bind("<B1-Motion>", self.paint)
        self.canvas.bind("<Button-1>", self.paint)

    def paint(self, event):
        x, y = event.x // 16, event.y // 16
        if 0 <= x < 16 and 0 <= y < 16:
            self.canvas.create_rectangle(x*16, y*16, (x+1)*16, (y+1)*16, fill=self.current_color, outline="")
            rgb_color = self.hex_to_rgb(self.current_color)
            self.app.custom_cursor[y, x] = [rgb_color[0], rgb_color[1], rgb_color[2], 255]

    def choose_color(self):
        color = colorchooser.askcolor(title="Choose Color")
        if color[1]:
            self.current_color = color[1]

    def clear_canvas(self):
        self.setup_canvas()
        self.app.custom_cursor.fill(0)

    def save_cursor(self):
        self.app.custom_cursor_var.set(True)
        self.app.use_custom_cursor = True
        self.destroy()

    def hex_to_rgb(self, hex_color):
        hex_color = hex_color.lstrip('#')
        if len(hex_color) == 6:
            return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        else:
            return (0, 0, 0)

if __name__ == "__main__":
    root = tk.Tk()
    app = ScreenRecorderApp(root)
    root.mainloop()
