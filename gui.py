"""
gui.py
------
Simple GUI for Secure File Transfer System

Provides a graphical interface to run the server and client.
"""

import subprocess
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
import os
import tempfile
import shutil
import zipfile

class SecureFileTransferGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Secure File Transfer - Hacker Mode")
        self.root.geometry("700x500")
        self.root.configure(bg='#000000')  # Black background

        # Custom styles
        self.bg_color = '#000000'  # Black
        self.fg_color = '#00FF00'  # Green
        self.btn_bg = '#333333'    # Dark gray
        self.btn_fg = '#00FF00'    # Green
        self.font = ('Courier New', 10)  # Monospace font
        self.title_font = ('Courier New', 14, 'bold')

        # Server section
        server_frame = tk.Frame(root, bg=self.bg_color)
        server_frame.pack(pady=10)

        tk.Label(server_frame, text=">> SERVER CONTROL <<", font=self.title_font, fg=self.fg_color, bg=self.bg_color).pack()

        self.start_server_btn = tk.Button(server_frame, text="[START SERVER]", command=self.start_server, bg=self.btn_bg, fg=self.btn_fg, font=self.font, relief='raised', bd=2)
        self.start_server_btn.pack(side=tk.LEFT, padx=10)

        self.stop_server_btn = tk.Button(server_frame, text="[STOP SERVER]", command=self.stop_server, state=tk.DISABLED, bg=self.btn_bg, fg=self.btn_fg, font=self.font, relief='raised', bd=2)
        self.stop_server_btn.pack(side=tk.LEFT, padx=10)

        # Client section
        client_frame = tk.Frame(root, bg=self.bg_color)
        client_frame.pack(pady=10)

        tk.Label(client_frame, text=">> CLIENT TRANSFER <<", font=self.title_font, fg=self.fg_color, bg=self.bg_color).pack()

        # Selection mode
        mode_frame = tk.Frame(client_frame, bg=self.bg_color)
        mode_frame.pack(pady=5)

        tk.Label(mode_frame, text="Mode:", fg=self.fg_color, bg=self.bg_color, font=self.font).pack(side=tk.LEFT)
        self.mode_var = tk.StringVar(value="Single File")
        self.mode_combo = ttk.Combobox(mode_frame, textvariable=self.mode_var, values=["Single File", "Multiple Files", "Folder"], state="readonly", font=self.font)
        self.mode_combo.pack(side=tk.LEFT, padx=10)

        self.select_file_btn = tk.Button(client_frame, text="[SELECT]", command=self.select_file, bg=self.btn_bg, fg=self.btn_fg, font=self.font, relief='raised', bd=2)
        self.select_file_btn.pack(side=tk.LEFT, padx=10)

        self.send_file_btn = tk.Button(client_frame, text="[SEND]", command=self.send_file, state=tk.DISABLED, bg=self.btn_bg, fg=self.btn_fg, font=self.font, relief='raised', bd=2)
        self.send_file_btn.pack(side=tk.LEFT, padx=10)

        self.selected_label = tk.Label(client_frame, text="Nothing selected", fg=self.fg_color, bg=self.bg_color, font=self.font)
        self.selected_label.pack(side=tk.LEFT, padx=10)

        # Log area
        log_frame = tk.Frame(root, bg=self.bg_color)
        log_frame.pack(pady=10, fill=tk.BOTH, expand=True)

        tk.Label(log_frame, text=">> SYSTEM LOGS <<", font=self.title_font, fg=self.fg_color, bg=self.bg_color).pack()

        self.log_text = scrolledtext.ScrolledText(log_frame, height=10, bg='#111111', fg=self.fg_color, insertbackground=self.fg_color, font=self.font, relief='sunken', bd=2)
        self.log_text.pack(fill=tk.BOTH, expand=True)

        self.server_process = None
        self.selected_items = None

        # Initial log
        self.log("Initializing secure file transfer system...")
        self.log("Ready for operations.")

    def log(self, message):
        self.log_text.insert(tk.END, f"[LOG] {message}\n")
        self.log_text.see(tk.END)

    def start_server(self):
        if self.server_process and self.server_process.poll() is None:
            messagebox.showerror("ERROR", "Server is already running")
            return

        self.log("Starting server...")
        try:
            self.server_process = subprocess.Popen([sys.executable, "server.py"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            self.start_server_btn.config(state=tk.DISABLED)
            self.stop_server_btn.config(state=tk.NORMAL)
            threading.Thread(target=self.monitor_server, daemon=True).start()
            self.log("Server started successfully.")
        except Exception as e:
            self.log(f"Failed to start server: {e}")
            messagebox.showerror("ERROR", f"Failed to start server: {e}")

    def monitor_server(self):
        if self.server_process:
            for line in iter(self.server_process.stdout.readline, ''):
                self.log(line.strip())
            self.server_process.stdout.close()
            self.server_process.wait()
            self.start_server_btn.config(state=tk.NORMAL)
            self.stop_server_btn.config(state=tk.DISABLED)
            self.log("Server stopped.")

    def stop_server(self):
        if self.server_process and self.server_process.poll() is None:
            self.server_process.terminate()
            self.server_process.wait()
            self.log("Server stopped manually.")
            self.start_server_btn.config(state=tk.NORMAL)
            self.stop_server_btn.config(state=tk.DISABLED)

    def select_file(self):
        mode = self.mode_var.get()
        if mode == "Single File":
            file_path = filedialog.askopenfilename(title="Select file to transfer")
            if file_path:
                self.selected_items = [file_path]
                self.selected_label.config(text=f"Selected: {os.path.basename(file_path)}")
                self.send_file_btn.config(state=tk.NORMAL)
        elif mode == "Multiple Files":
            file_paths = filedialog.askopenfilenames(title="Select files to transfer")
            if file_paths:
                self.selected_items = list(file_paths)
                names = [os.path.basename(p) for p in file_paths]
                self.selected_label.config(text=f"Selected: {len(names)} files")
                self.send_file_btn.config(state=tk.NORMAL)
        elif mode == "Folder":
            folder_path = filedialog.askdirectory(title="Select folder to transfer")
            if folder_path:
                self.selected_items = [folder_path]
                self.selected_label.config(text=f"Selected: {os.path.basename(folder_path)} (folder)")
                self.send_file_btn.config(state=tk.NORMAL)

    def send_file(self):
        if not self.selected_items:
            messagebox.showerror("ERROR", "Nothing selected")
            return

        mode = self.mode_var.get()
        temp_zip = None

        try:
            if mode == "Single File":
                file_to_send = self.selected_items[0]
            else:
                # Create a temp zip
                temp_zip = tempfile.NamedTemporaryFile(suffix='.zip', delete=False)
                temp_zip.close()
                zip_path = temp_zip.name

                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    if mode == "Multiple Files":
                        for file_path in self.selected_items:
                            zipf.write(file_path, os.path.basename(file_path))
                    elif mode == "Folder":
                        folder_path = self.selected_items[0]
                        for root, dirs, files in os.walk(folder_path):
                            for file in files:
                                full_path = os.path.join(root, file)
                                arcname = os.path.relpath(full_path, folder_path)
                                zipf.write(full_path, arcname)

                file_to_send = zip_path

            self.log(f"Sending: {file_to_send}")
            result = subprocess.run([sys.executable, "client.py", "--file", file_to_send], capture_output=True, text=True)
            self.log(result.stdout)
            if result.stderr:
                self.log("Errors: " + result.stderr)
            if result.returncode == 0:
                self.log("Transfer successful!")
                messagebox.showinfo("SUCCESS", "Transfer completed successfully!")
            else:
                self.log("Failed to send.")
                messagebox.showerror("ERROR", "Failed to send")

        except Exception as e:
            self.log(f"Failed: {e}")
            messagebox.showerror("ERROR", f"Failed: {e}")
        finally:
            if temp_zip and os.path.exists(zip_path):
                os.unlink(zip_path)

if __name__ == "__main__":
    root = tk.Tk()
    app = SecureFileTransferGUI(root)
    root.mainloop()