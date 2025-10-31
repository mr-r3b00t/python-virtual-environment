import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import subprocess
import shutil
import sys
from pathlib import Path

class VirtualEnvManager:
    def __init__(self, root):
        self.root = root
        self.root.title("Python Virtual Environment Manager (macOS)")
        self.root.geometry("600x500")
        
        # Default directory for venvs (customizable)
        self.venv_dir = Path.home() / "venvs"
        self.venv_dir.mkdir(exist_ok=True)
        
        # List to hold (name, path) tuples for display and management
        self.venv_list = []
        
        self.setup_ui()
        self.refresh_list()  # Initial load from default dir
    
    def setup_ui(self):
        # Frame for controls
        control_frame = ttk.Frame(self.root, padding="10")
        control_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Create new venv
        ttk.Label(control_frame, text="New Environment Name:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.new_name_var = tk.StringVar()
        ttk.Entry(control_frame, textvariable=self.new_name_var, width=20).grid(row=0, column=1, padx=5)
        ttk.Button(control_frame, text="Create", command=self.create_venv).grid(row=0, column=2, padx=5)
        
        # Directory selection
        ttk.Button(control_frame, text="Change Venv Folder", command=self.change_venv_dir).grid(row=0, column=3, padx=5)
        self.dir_label_var = tk.StringVar(value=str(self.venv_dir))
        ttk.Label(control_frame, textvariable=self.dir_label_var).grid(row=1, column=0, columnspan=4, sticky=tk.W, padx=5)
        
        # Scan button
        ttk.Button(control_frame, text="Scan User Home for Venvs", command=self.scan_home).grid(row=0, column=4, padx=5)
        
        # List of venvs
        list_frame = ttk.LabelFrame(self.root, text="Virtual Environments", padding="10")
        list_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=10, pady=10)
        
        self.venv_listbox = tk.Listbox(list_frame, height=15, selectmode=tk.SINGLE)
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.venv_listbox.yview)
        self.venv_listbox.configure(yscrollcommand=scrollbar.set)
        self.venv_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Buttons for actions
        button_frame = ttk.Frame(list_frame)
        button_frame.grid(row=1, column=0, columnspan=2, pady=10)
        
        ttk.Button(button_frame, text="Activate in Terminal", command=self.activate_venv).grid(row=0, column=0, padx=5)
        ttk.Button(button_frame, text="Delete", command=self.delete_venv).grid(row=0, column=1, padx=5)
        ttk.Button(button_frame, text="Refresh", command=self.refresh_list).grid(row=0, column=2, padx=5)
        
        # Info label
        self.info_var = tk.StringVar(value="Select a virtual environment to manage it.")
        ttk.Label(list_frame, textvariable=self.info_var).grid(row=2, column=0, columnspan=2, pady=5)
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        control_frame.columnconfigure(1, weight=1)
    
    def load_from_dir(self):
        """Load venvs from the current venv_dir."""
        self.venv_list = []
        for venv_path in self.venv_dir.glob("venv-*"):
            if venv_path.is_dir():
                name = venv_path.name.replace("venv-", "")
                self.venv_list.append((name, venv_path))
        self.refresh_list()
    
    def refresh_list(self):
        """Refresh the listbox from self.venv_list."""
        self.venv_listbox.delete(0, tk.END)
        for name, path in self.venv_list:
            self.venv_listbox.insert(tk.END, f"{name} ({path.absolute()})")
        self.info_var.set(f"Loaded {len(self.venv_list)} environments from {self.dir_label_var.get()}.")
    
    def scan_home(self):
        """Scan user's home directory for existing virtual environments (looks for bin/activate)."""
        self.venv_list = []
        found_count = 0
        try:
            for activate_file in Path.home().rglob('**/bin/activate'):
                venv_path = activate_file.parent.parent
                if venv_path.is_dir() and (venv_path / 'bin' / 'python').exists():  # Confirm it's a venv with python
                    name = venv_path.name
                    if name.startswith('venv-'):
                        name = name[5:]
                    elif name == '.venv':
                        name = 'project_dot_venv'
                    # Avoid duplicates by path
                    if all(str(venv_path) != str(p) for _, p in self.venv_list):
                        self.venv_list.append((name, venv_path))
                        found_count += 1
        except (PermissionError, OSError):
            messagebox.showwarning("Scan Warning", "Some directories could not be accessed due to permissions.")
        
        if found_count > 0:
            self.refresh_list()
            self.dir_label_var.set("~ (scanned from home)")
            messagebox.showinfo("Scan Complete", f"Found {found_count} virtual environments in your home directory.")
            self.info_var.set(f"Scanned {found_count} environments from home. Use 'Change Venv Folder' to switch back.")
        else:
            messagebox.showinfo("Scan Complete", "No virtual environments found in your home directory.")
    
    def create_venv(self):
        name = self.new_name_var.get().strip()
        if not name:
            messagebox.showerror("Error", "Please enter a name for the new environment.")
            return
        
        venv_path = self.venv_dir / f"venv-{name}"
        if venv_path.exists():
            messagebox.showerror("Error", f"Environment '{name}' already exists.")
            return
        
        try:
            # Use python -m venv to create
            subprocess.check_call([sys.executable, "-m", "venv", str(venv_path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.venv_list.append((name, venv_path))
            messagebox.showinfo("Success", f"Created virtual environment '{name}' at {venv_path}")
            self.new_name_var.set("")
            self.refresh_list()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create environment: {str(e)}")
    
    def get_selected_venv(self):
        selection = self.venv_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a virtual environment.")
            return None
        item = self.venv_listbox.get(selection[0])
        if ' (' not in item:
            return None
        name_part = item.split(' (')[0]
        path_str = item.split(' (')[1][:-1]  # Remove trailing )
        try:
            return Path(path_str)
        except:
            messagebox.showerror("Error", "Could not parse selected path.")
            return None
    
    def activate_venv(self):
        venv_path = self.get_selected_venv()
        if not venv_path:
            return
        
        try:
            # On macOS, open a new Terminal tab/window with the env activated
            activate_script = f"source {venv_path}/bin/activate && exec bash"
            subprocess.Popen(["osascript", "-e", f'tell application "Terminal" to do script "{activate_script}"'])
            self.info_var.set(f"Opened Terminal with '{venv_path.name}' activated.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open Terminal: {str(e)}")
    
    def delete_venv(self):
        venv_path = self.get_selected_venv()
        if not venv_path:
            return
        
        if messagebox.askyesno("Confirm", f"Delete '{venv_path.name}' at {venv_path}? This cannot be undone."):
            try:
                shutil.rmtree(venv_path)
                # Remove from list
                self.venv_list = [(n, p) for n, p in self.venv_list if p != venv_path]
                messagebox.showinfo("Success", f"Deleted '{venv_path.name}'.")
                self.refresh_list()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete: {str(e)}")
    
    def change_venv_dir(self):
        new_dir = filedialog.askdirectory(initialdir=str(self.venv_dir))
        if new_dir:
            self.venv_dir = Path(new_dir)
            self.dir_label_var.set(str(self.venv_dir))
            self.load_from_dir()  # Reload from new dir

if __name__ == "__main__":
    root = tk.Tk()
    app = VirtualEnvManager(root)
    root.mainloop()
