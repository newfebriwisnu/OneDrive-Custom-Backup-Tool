"""
Main GUI window for OneDrive Custom Backup Tool
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import sys
from pathlib import Path
import logging

from gui.validators import PathValidator
from core.backup import BackupManager
from core.junction_manager import JunctionManager
from utils.config import get_config
from utils.paths import PathUtils


class MainWindow:
    """Main application window"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.config = get_config()
        self.backup_manager = BackupManager()
        self.junction_manager = JunctionManager()
        self.path_utils = PathUtils()
        self.path_validator = PathValidator()

        # Initialize GUI
        self.root = tk.Tk()
        self.root.configure(bg='#2b2b2b')  # Dark background

        # Variables
        self.source_var = tk.StringVar()
        self.target_var = tk.StringVar()
        self.status_var = tk.StringVar()
        self.progress_var = tk.DoubleVar()

        # UI elements
        self.progress_bar = None
        self.execute_button = None
        self.source_entry = None
        self.target_entry = None
        self.status_label = None

        # State
        self.is_executing = False

        self._setup_window()
        self._create_widgets()
        self._setup_events()
        self._load_saved_paths()

        self.logger.info("Main window initialized")

    def _setup_window(self):
        """Setup main window properties"""
        self.root.title("OneDrive Custom Backup Tool")
        self.root.geometry("650x450")  # Increased height for new features
        self.root.resizable(False, False)

        # Center window on screen
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')

        # Set window icon (if available)
        try:
            icon_path = Path(__file__).parent.parent.parent / \
                "assets" / "icon.ico"
            if icon_path.exists():
                self.root.iconbitmap(str(icon_path))
        except Exception:
            pass

    def _create_widgets(self):
        """Create main window widgets with simple, compact design"""
        # Main frame with dark background
        main_frame = tk.Frame(self.root, bg='#2b2b2b', padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title_label = tk.Label(
            main_frame,
            text="OneDrive Backup Tool",
            font=('Segoe UI', 14, 'bold'),
            bg='#2b2b2b',
            fg='#00ffff'
        )
        title_label.pack(pady=(0, 20))

        # Source path section
        source_label = tk.Label(
            main_frame,
            text="Source Folder:",
            font=('Segoe UI', 10, 'bold'),
            bg='#2b2b2b',
            fg='#ffffff'
        )
        source_label.pack(anchor=tk.W, pady=(0, 5))

        source_frame = tk.Frame(main_frame, bg='#2b2b2b')
        source_frame.pack(fill=tk.X, pady=(0, 15))

        self.source_entry = tk.Entry(
            source_frame,
            textvariable=self.source_var,
            font=('Segoe UI', 10),
            width=50,
            bg='#404040',
            fg='#ffffff',
            insertbackground='#00ffff',
            relief='flat',
            bd=2
        )
        self.source_entry.pack(side=tk.LEFT, fill=tk.X,
                               expand=True, padx=(0, 10))

        source_browse_btn = tk.Button(
            source_frame,
            text="Browse",
            command=self._browse_source,
            font=('Segoe UI', 9),
            bg='#404040',
            fg='#00ffff',
            activebackground='#505050',
            activeforeground='#ffffff',
            relief='flat',
            bd=1,
            width=8
        )
        source_browse_btn.pack(side=tk.RIGHT)

        # Target path section
        target_label = tk.Label(
            main_frame,
            text="Target OneDrive Folder:",
            font=('Segoe UI', 10, 'bold'),
            bg='#2b2b2b',
            fg='#ffffff'
        )
        target_label.pack(anchor=tk.W, pady=(0, 5))

        target_frame = tk.Frame(main_frame, bg='#2b2b2b')
        target_frame.pack(fill=tk.X, pady=(0, 20))

        self.target_entry = tk.Entry(
            target_frame,
            textvariable=self.target_var,
            font=('Segoe UI', 10),
            width=50,
            bg='#404040',
            fg='#ffffff',
            insertbackground='#00ffff',
            relief='flat',
            bd=2
        )
        self.target_entry.pack(side=tk.LEFT, fill=tk.X,
                               expand=True, padx=(0, 10))

        target_browse_btn = tk.Button(
            target_frame,
            text="Browse",
            command=self._browse_target,
            font=('Segoe UI', 9),
            bg='#404040',
            fg='#00ffff',
            activebackground='#505050',
            activeforeground='#ffffff',
            relief='flat',
            bd=1,
            width=8
        )
        target_browse_btn.pack(side=tk.RIGHT)

        # Execute button
        self.execute_button = tk.Button(
            main_frame,
            text="Execute Backup",
            command=self._execute_backup,
            font=('Segoe UI', 12, 'bold'),
            bg='#0078d4',
            fg='#ffffff',
            activebackground='#106ebe',
            activeforeground='#ffffff',
            relief='flat',
            bd=2,
            width=20,
            pady=8
        )
        self.execute_button.pack(pady=(0, 15))

        # Progress bar
        self.progress_bar = ttk.Progressbar(
            main_frame,
            variable=self.progress_var,
            maximum=100,
            length=400
        )
        self.progress_bar.pack(pady=(0, 10))

        # Status label
        self.status_label = tk.Label(
            main_frame,
            textvariable=self.status_var,
            font=('Segoe UI', 9),
            bg='#2b2b2b',
            fg='#00ff00',
            anchor=tk.W
        )
        self.status_label.pack(fill=tk.X, pady=(0, 15))

        # Junction Management Section
        junction_frame = tk.Frame(main_frame, bg='#2b2b2b')
        junction_frame.pack(fill=tk.X, pady=(0, 15))

        junction_label = tk.Label(
            junction_frame,
            text="Junction Links Management:",
            font=('Segoe UI', 10, 'bold'),
            bg='#2b2b2b',
            fg='#ffffff'
        )
        junction_label.pack(anchor=tk.W, pady=(0, 5))

        # Junction buttons frame
        junction_buttons_frame = tk.Frame(junction_frame, bg='#2b2b2b')
        junction_buttons_frame.pack(fill=tk.X, pady=(0, 5))

        list_junctions_btn = tk.Button(
            junction_buttons_frame,
            text="List Junctions",
            command=self._show_junction_list,
            font=('Segoe UI', 9),
            bg='#404040',
            fg='#00ffff',
            activebackground='#505050',
            activeforeground='#ffffff',
            relief='flat',
            bd=1,
            width=12
        )
        list_junctions_btn.pack(side=tk.LEFT, padx=(0, 10))

        refresh_btn = tk.Button(
            junction_buttons_frame,
            text="Refresh",
            command=self._refresh_junction_list,
            font=('Segoe UI', 9),
            bg='#404040',
            fg='#00ffff',
            activebackground='#505050',
            activeforeground='#ffffff',
            relief='flat',
            bd=1,
            width=8
        )
        refresh_btn.pack(side=tk.LEFT)

        # Junction list frame (initially hidden)
        self.junction_list_frame = tk.Frame(junction_frame, bg='#2b2b2b')

        # How To section
        how_to_frame = tk.Frame(main_frame, bg='#2b2b2b')
        how_to_frame.pack(fill=tk.X, pady=(0, 15))

        how_to_btn = tk.Button(
            how_to_frame,
            text="How To Use",
            command=self._show_how_to,
            font=('Segoe UI', 9),
            bg='#404040',
            fg='#ffff00',
            activebackground='#505050',
            activeforeground='#ffffff',
            relief='flat',
            bd=1,
            width=12
        )
        how_to_btn.pack(anchor=tk.W)

        # Bottom buttons
        bottom_frame = tk.Frame(main_frame, bg='#2b2b2b')
        bottom_frame.pack(fill=tk.X)

        about_btn = tk.Button(
            bottom_frame,
            text="About",
            command=self._show_about,
            font=('Segoe UI', 9),
            bg='#404040',
            fg='#ffffff',
            activebackground='#505050',
            activeforeground='#ffffff',
            relief='flat',
            bd=1,
            width=10
        )
        about_btn.pack(side=tk.LEFT, padx=(0, 10))

        exit_btn = tk.Button(
            bottom_frame,
            text="Exit",
            command=self._exit_application,
            font=('Segoe UI', 9),
            bg='#404040',
            fg='#ffffff',
            activebackground='#505050',
            activeforeground='#ffffff',
            relief='flat',
            bd=1,
            width=10
        )
        exit_btn.pack(side=tk.LEFT)

        # Set initial status
        self.status_var.set("Ready - Select source and target folders")

    def _setup_events(self):
        """Setup event bindings"""
        # Path validation on key release
        self.source_entry.bind(
            '<KeyRelease>', lambda e: self._validate_source())
        self.target_entry.bind(
            '<KeyRelease>', lambda e: self._validate_target())

        # Window close event
        self.root.protocol("WM_DELETE_WINDOW", self._exit_application)

        # Auto-suggest OneDrive path
        self.target_entry.bind('<FocusIn>', self._suggest_onedrive_path)

        # Entry focus styling
        self.source_entry.bind(
            '<FocusIn>', lambda e: self._on_entry_focus(self.source_entry))
        self.source_entry.bind(
            '<FocusOut>', lambda e: self._on_entry_blur(self.source_entry))
        self.target_entry.bind(
            '<FocusIn>', lambda e: self._on_entry_focus(self.target_entry))
        self.target_entry.bind(
            '<FocusOut>', lambda e: self._on_entry_blur(self.target_entry))

    def _on_entry_focus(self, entry):
        """Handle entry focus styling"""
        entry.config(bg='#505050', highlightbackground='#00ffff',
                     highlightcolor='#00ffff')

    def _on_entry_blur(self, entry):
        """Handle entry blur styling"""
        entry.config(bg='#404040', highlightbackground='#404040',
                     highlightcolor='#404040')

    def _load_saved_paths(self):
        """Load saved paths from configuration"""
        if self.config.get_remember_paths():
            last_source = self.config.get_last_source()
            last_target = self.config.get_last_target()

            if last_source:
                self.source_var.set(last_source)
            if last_target:
                self.target_var.set(last_target)

    def _browse_source(self):
        """Browse for source folder"""
        try:
            initial_dir = self.source_var.get() or str(Path.home())
            folder = filedialog.askdirectory(
                title="Select Source Folder",
                initialdir=initial_dir
            )

            if folder:
                self.source_var.set(folder)
                self._validate_source()
        except Exception as e:
            self.logger.error(f"Error browsing source: {e}")

    def _browse_target(self):
        """Browse for target folder"""
        try:
            # Auto-suggest OneDrive path
            initial_dir = self.target_var.get()
            if not initial_dir:
                onedrive_path = self.path_utils.get_onedrive_path()
                if onedrive_path:
                    initial_dir = onedrive_path
                else:
                    initial_dir = str(Path.home())

            folder = filedialog.askdirectory(
                title="Select Target Folder (OneDrive)",
                initialdir=initial_dir
            )

            if folder:
                self.target_var.set(folder)
                self._validate_target()
        except Exception as e:
            self.logger.error(f"Error browsing target: {e}")

    def _validate_source(self):
        """Validate source path"""
        path = self.source_var.get()
        if path:
            is_valid = self.path_validator.validate_source_realtime(
                self.source_entry, path)
            return is_valid
        return False

    def _validate_target(self):
        """Validate target path"""
        path = self.target_var.get()
        if path:
            is_valid = self.path_validator.validate_target_realtime(
                self.target_entry, path)
            return is_valid
        return False

    def _suggest_onedrive_path(self, event=None):
        """Auto-suggest OneDrive path"""
        try:
            if not self.target_var.get():
                onedrive_path = self.path_utils.get_onedrive_path()
                if onedrive_path:
                    backup_path = Path(onedrive_path) / "Backup"
                    self.target_var.set(str(backup_path))
        except Exception as e:
            self.logger.error(f"Error suggesting OneDrive path: {e}")

    def _execute_backup(self):
        """Execute backup operation"""
        if self.is_executing:
            return

        try:
            source = self.source_var.get().strip()
            target = self.target_var.get().strip()

            if not source or not target:
                messagebox.showerror(
                    "Error", "Please select both source and target folders")
                return

            # Validate paths
            source_valid = self._validate_source()
            target_valid = self._validate_target()

            if not source_valid or not target_valid:
                messagebox.showerror(
                    "Error", "Please fix path validation errors")
                return

            # Final validation
            is_valid, error_msg = self.backup_manager.validate_paths(
                source, target)
            if not is_valid:
                messagebox.showerror("Validation Error", error_msg)
                return

            # Confirm with user
            if not messagebox.askyesno("Confirm Backup",
                                       f"Create backup:\n\nSource: {source}\nTarget: {target}\n\n"
                                       f"This will move the folder to OneDrive and create a junction link.\n\n"
                                       f"Continue?"):
                return

            # Save paths
            if self.config.get_remember_paths():
                self.config.set_last_source(source)
                self.config.set_last_target(target)
                self.config.save_config()

            # Start backup in separate thread
            self.is_executing = True
            self.execute_button.config(state='disabled', text="EXECUTING...")
            self.progress_var.set(0)
            self.status_var.set("INITIALIZING BACKUP SEQUENCE...")

            backup_thread = threading.Thread(
                target=self._backup_worker,
                args=(source, target),
                daemon=True
            )
            backup_thread.start()

        except Exception as e:
            self.logger.error(f"Error executing backup: {e}")
            messagebox.showerror(
                "Error", f"Failed to execute backup: {str(e)}")

    def _backup_worker(self, source: str, target: str):
        """Backup worker thread"""
        try:
            success = self.backup_manager.execute_backup(
                source, target, self._progress_callback
            )

            # Update UI on main thread
            self.root.after(0, self._backup_completed, success)

        except Exception as e:
            self.logger.error(f"Backup worker error: {e}")
            self.root.after(0, self._backup_completed, False, str(e))

    def _progress_callback(self, message: str, progress: int):
        """Progress callback from backup operation"""
        # Make messages more cyberpunk-style
        cyber_messages = {
            "Validating paths...": "SCANNING TARGET COORDINATES...",
            "Preparing rollback...": "PREPARING RECOVERY PROTOCOL...",
            "Moving files to OneDrive...": "INITIATING DATA TRANSFER...",
            "Creating junction link...": "ESTABLISHING QUANTUM LINK...",
            "Verifying backup...": "VERIFYING SYSTEM INTEGRITY...",
            "Backup completed successfully!": "MISSION ACCOMPLISHED!"
        }

        cyber_message = cyber_messages.get(message, message.upper())
        self.root.after(0, self._update_progress, cyber_message, progress)

    def _update_progress(self, message: str, progress: int):
        """Update progress on main thread"""
        self.status_var.set(message)
        self.progress_var.set(progress)
        self.root.update_idletasks()

    def _backup_completed(self, success: bool, error_msg: str = None):
        """Handle backup completion"""
        self.is_executing = False
        self.execute_button.config(state='normal', text="EXECUTE BACKUP")

        if success:
            self.status_var.set("BACKUP SEQUENCE COMPLETED SUCCESSFULLY!")
            self.progress_var.set(100)
            messagebox.showinfo("Success", "Backup completed successfully!")
        else:
            self.status_var.set("BACKUP SEQUENCE FAILED!")
            self.progress_var.set(0)
            error_text = f"Backup failed!"
            if error_msg:
                error_text += f"\n\nError: {error_msg}"
            messagebox.showerror("Error", error_text)

    def _show_about(self):
        """Show about dialog"""
        about_text = """OneDrive Custom Backup Folder Tool

A modern Windows GUI application that creates OneDrive backups using junction links.

Version: 1.0.0
Author: GitHub Community
License: MIT

Features:
• Simple, clean GUI interface
• Safe backup operations with rollback
• PowerShell integration for junction links
• Real-time path validation
• Junction link management
• Windows 10/11 optimized

Visit: https://github.com/newfebriwisnu/OneDrive-Custom-Backup-Tool"""

        messagebox.showinfo("About", about_text)

    def _exit_application(self):
        """Exit application"""
        try:
            if self.is_executing:
                if not messagebox.askyesno("Exit", "Backup operation is in progress. Are you sure you want to exit?"):
                    return

            self.logger.info("Application exiting")
            self.root.quit()
            self.root.destroy()
        except Exception as e:
            self.logger.error(f"Error exiting application: {e}")
            sys.exit(1)

    def _show_junction_list(self):
        """Show junction list window"""
        self._create_junction_window()

    def _refresh_junction_list(self):
        """Refresh junction list"""
        if hasattr(self, 'junction_window') and self.junction_window.winfo_exists():
            self._update_junction_list()

    def _create_junction_window(self):
        """Create junction management window"""
        # Create junction window
        self.junction_window = tk.Toplevel(self.root)
        self.junction_window.title("Junction Links Management")
        self.junction_window.geometry("800x500")
        self.junction_window.configure(bg='#2b2b2b')

        # Center window
        self.junction_window.transient(self.root)
        self.junction_window.grab_set()

        # Main frame
        main_frame = tk.Frame(self.junction_window,
                              bg='#2b2b2b', padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title_label = tk.Label(
            main_frame,
            text="Junction Links Management",
            font=('Segoe UI', 14, 'bold'),
            bg='#2b2b2b',
            fg='#00ffff'
        )
        title_label.pack(pady=(0, 20))

        # Buttons frame
        buttons_frame = tk.Frame(main_frame, bg='#2b2b2b')
        buttons_frame.pack(fill=tk.X, pady=(0, 15))

        refresh_btn = tk.Button(
            buttons_frame,
            text="Refresh List",
            command=self._update_junction_list,
            font=('Segoe UI', 9),
            bg='#0078d4',
            fg='#ffffff',
            activebackground='#106ebe',
            activeforeground='#ffffff',
            relief='flat',
            bd=1,
            width=12
        )
        refresh_btn.pack(side=tk.LEFT, padx=(0, 10))

        # Junction list frame with scrollbar
        list_frame = tk.Frame(main_frame, bg='#2b2b2b')
        list_frame.pack(fill=tk.BOTH, expand=True)

        # Create scrollable listbox
        self.junction_listbox = tk.Listbox(
            list_frame,
            font=('Consolas', 9),
            bg='#404040',
            fg='#ffffff',
            selectbackground='#0078d4',
            selectforeground='#ffffff',
            relief='flat',
            bd=1
        )

        scrollbar = tk.Scrollbar(
            list_frame, orient=tk.VERTICAL, command=self.junction_listbox.yview)
        self.junction_listbox.configure(yscrollcommand=scrollbar.set)

        self.junction_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Action buttons
        action_frame = tk.Frame(main_frame, bg='#2b2b2b')
        action_frame.pack(fill=tk.X, pady=(15, 0))

        remove_btn = tk.Button(
            action_frame,
            text="Remove Selected",
            command=self._remove_selected_junction,
            font=('Segoe UI', 9),
            bg='#d83b01',
            fg='#ffffff',
            activebackground='#b22a00',
            activeforeground='#ffffff',
            relief='flat',
            bd=1,
            width=15
        )
        remove_btn.pack(side=tk.LEFT, padx=(0, 10))

        verify_btn = tk.Button(
            action_frame,
            text="Verify Selected",
            command=self._verify_selected_junction,
            font=('Segoe UI', 9),
            bg='#107c10',
            fg='#ffffff',
            activebackground='#0e6b0e',
            activeforeground='#ffffff',
            relief='flat',
            bd=1,
            width=15
        )
        verify_btn.pack(side=tk.LEFT, padx=(0, 10))

        close_btn = tk.Button(
            action_frame,
            text="Close",
            command=self.junction_window.destroy,
            font=('Segoe UI', 9),
            bg='#404040',
            fg='#ffffff',
            activebackground='#505050',
            activeforeground='#ffffff',
            relief='flat',
            bd=1,
            width=10
        )
        close_btn.pack(side=tk.RIGHT)

        # Load initial junction list
        self._update_junction_list()

    def _update_junction_list(self):
        """Update junction list display"""
        try:
            self.junction_listbox.delete(0, tk.END)
            self.junction_listbox.insert(0, "Loading junction links...")
            self.junction_window.update_idletasks()

            # Get junction list in a separate thread to avoid blocking UI
            def load_junctions():
                try:
                    junctions = self.junction_manager.list_junctions()
                    self.root.after(0, self._populate_junction_list, junctions)
                except Exception as e:
                    self.root.after(0, self._junction_load_error, str(e))

            import threading
            threading.Thread(target=load_junctions, daemon=True).start()

        except Exception as e:
            self.logger.error(f"Error updating junction list: {e}")
            messagebox.showerror(
                "Error", f"Failed to update junction list: {str(e)}")

    def _populate_junction_list(self, junctions):
        """Populate junction list with data"""
        try:
            self.junction_listbox.delete(0, tk.END)

            if not junctions:
                self.junction_listbox.insert(0, "No junction links found")
                return

            self.junction_data = junctions  # Store for later use

            for i, junction in enumerate(junctions):
                source = junction.get('source', '')
                target = junction.get('target', '')

                # Format display text
                display_text = f"{i+1:2d}. {source} → {target}"
                self.junction_listbox.insert(tk.END, display_text)

        except Exception as e:
            self.logger.error(f"Error populating junction list: {e}")
            self.junction_listbox.delete(0, tk.END)
            self.junction_listbox.insert(
                0, f"Error loading junctions: {str(e)}")

    def _junction_load_error(self, error_msg):
        """Handle junction loading error"""
        self.junction_listbox.delete(0, tk.END)
        self.junction_listbox.insert(
            0, f"Error loading junctions: {error_msg}")

    def _remove_selected_junction(self):
        """Remove selected junction link"""
        try:
            selection = self.junction_listbox.curselection()
            if not selection:
                messagebox.showwarning(
                    "No Selection", "Please select a junction to remove")
                return

            index = selection[0]
            if not hasattr(self, 'junction_data') or index >= len(self.junction_data):
                messagebox.showerror("Error", "Invalid selection")
                return

            junction = self.junction_data[index]
            source = junction.get('source', '')

            # Confirm removal
            if not messagebox.askyesno("Confirm Removal",
                                       f"Are you sure you want to remove this junction link?\n\n"
                                       f"Source: {source}\n"
                                       f"Target: {junction.get('target', '')}\n\n"
                                       f"This will remove the junction link only, not the target folder."):
                return

            # Remove junction
            success, message = self.junction_manager.remove_junction(source)

            if success:
                messagebox.showinfo("Success", message)
                self._update_junction_list()  # Refresh list
            else:
                messagebox.showerror("Error", message)

        except Exception as e:
            self.logger.error(f"Error removing junction: {e}")
            messagebox.showerror(
                "Error", f"Failed to remove junction: {str(e)}")

    def _verify_selected_junction(self):
        """Verify selected junction link"""
        try:
            selection = self.junction_listbox.curselection()
            if not selection:
                messagebox.showwarning(
                    "No Selection", "Please select a junction to verify")
                return

            index = selection[0]
            if not hasattr(self, 'junction_data') or index >= len(self.junction_data):
                messagebox.showerror("Error", "Invalid selection")
                return

            junction = self.junction_data[index]
            source = junction.get('source', '')

            # Verify junction
            is_valid, message = self.junction_manager.verify_junction(source)

            if is_valid:
                messagebox.showinfo("Verification Result", f"✓ {message}")
            else:
                messagebox.showwarning("Verification Result", f"✗ {message}")

        except Exception as e:
            self.logger.error(f"Error verifying junction: {e}")
            messagebox.showerror(
                "Error", f"Failed to verify junction: {str(e)}")

    def _show_how_to(self):
        """Show how to use guide"""
        how_to_text = """How to Use OneDrive Custom Backup Tool

STEP 1: SELECT SOURCE FOLDER
• Click "Browse" next to "Source Folder"
• Choose the folder you want to backup to OneDrive
• This folder will be moved to OneDrive

STEP 2: SELECT TARGET FOLDER
• Click "Browse" next to "Target OneDrive Folder"
• Choose where in OneDrive you want to store the backup
• Usually in your OneDrive folder (e.g., OneDrive/Backup)

STEP 3: EXECUTE BACKUP
• Click "Execute Backup" to start the process
• The tool will:
  1. Move your folder to OneDrive
  2. Create a junction link at the original location
  3. Your applications will continue working normally

JUNCTION MANAGEMENT:
• Use "List Junctions" to see all existing junction links
• Remove unwanted junctions safely
• Verify junctions are working correctly

IMPORTANT NOTES:
• Always backup important data before using junction links
• Ensure OneDrive is syncing properly
• Junction links only work on the same drive
• Administrator rights may be required for some operations

WHAT IS A JUNCTION LINK?
A junction link is like a shortcut that makes a folder appear in two places at once. 
Your applications see the folder in its original location, but the actual files are 
stored in OneDrive and synced to the cloud.

TROUBLESHOOTING:
• If backup fails, check that OneDrive is running
• Ensure you have write permissions to both locations
• Try running as administrator if permission errors occur
• Check Windows Event Viewer for detailed error messages"""

        # Create how-to window
        how_to_window = tk.Toplevel(self.root)
        how_to_window.title("How to Use - OneDrive Backup Tool")
        how_to_window.geometry("700x600")
        how_to_window.configure(bg='#2b2b2b')
        how_to_window.transient(self.root)
        how_to_window.grab_set()

        # Main frame with scrollbar
        main_frame = tk.Frame(how_to_window, bg='#2b2b2b', padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title_label = tk.Label(
            main_frame,
            text="How to Use Guide",
            font=('Segoe UI', 14, 'bold'),
            bg='#2b2b2b',
            fg='#00ffff'
        )
        title_label.pack(pady=(0, 20))

        # Text area with scrollbar
        text_frame = tk.Frame(main_frame, bg='#2b2b2b')
        text_frame.pack(fill=tk.BOTH, expand=True)

        text_area = tk.Text(
            text_frame,
            font=('Segoe UI', 10),
            bg='#404040',
            fg='#ffffff',
            relief='flat',
            bd=1,
            wrap=tk.WORD
        )

        scrollbar = tk.Scrollbar(
            text_frame, orient=tk.VERTICAL, command=text_area.yview)
        text_area.configure(yscrollcommand=scrollbar.set)

        text_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Insert text
        text_area.insert(tk.END, how_to_text)
        text_area.config(state=tk.DISABLED)

        # Close button
        close_btn = tk.Button(
            main_frame,
            text="Close",
            command=how_to_window.destroy,
            font=('Segoe UI', 10),
            bg='#404040',
            fg='#ffffff',
            activebackground='#505050',
            activeforeground='#ffffff',
            relief='flat',
            bd=1,
            width=10
        )
        close_btn.pack(pady=(15, 0))

    def run(self):
        """Run the application"""
        try:
            self.logger.info("Starting GUI application")
            self.root.mainloop()
        except Exception as e:
            self.logger.error(f"GUI application error: {e}")
            raise
