from email.mime import image
import tkinter as tk
from tkinter import ttk
import subprocess


class ExportOptionView(ttk.Frame):
    def __init__(self, parent, shared_data, **kwargs):
        super().__init__(parent, **kwargs)
        self.shared_data = shared_data
        self.create_widgets()
        
        
    def create_widgets(self):
        # Overall Grid Configuration
        self.grid_columnconfigure(0, weight=4)
        self.grid_columnconfigure(1, weight=0)  # For the divider
        self.grid_columnconfigure(2, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Colors
        left_color = "#2e2e2e"  # Light color for left column
        right_color = "#1f1f1f"  # Darker color for right column
        divider_color = "#1e1e1e"  # Even darker color for the divider
        text_color = "#F0F0F0"  # Text color

        # Left Column Setup
        self.left_frame = tk.Frame(self, bg=left_color)
        self.left_frame.grid(row=0, column=0, sticky="nsew")
        self.left_frame.grid_columnconfigure(0, weight=1)
        self.left_frame.grid_rowconfigure(0, weight=5)
        self.left_frame.grid_rowconfigure(1, weight=1)
        
        self.toggle_frame = tk.Frame(self.left_frame, bg=right_color)
        self.toggle_frame.grid(row=0, column=0, padx=10, pady=10,  sticky="nsew")
        self.toggle_frame.grid_columnconfigure(0, weight=1)
        self.toggle_frame.grid_rowconfigure(0, weight=1)
        
        self.revert_button = ttk.Button(self.left_frame, text="Revert Changes")
        self.revert_button.grid(row=1, column=0, padx=(0, 10), pady=(0, 10), sticky="se")
        
        # Divider
        self.divider = tk.Frame(self, bg=divider_color, width=2)
        self.divider.grid(row=0, column=1, sticky="ns")

        # Right Column Setup
        self.right_frame = tk.Frame(self, bg=right_color)
        self.right_frame.grid(row=0, column=2, sticky="nsew")
        self.right_frame.grid_rowconfigure((0, 1), weight=0)
        self.right_frame.grid_rowconfigure((2, 3), weight=5)
        self.right_frame.grid_rowconfigure((4), weight=1)
        self.right_frame.grid_columnconfigure(0, weight=1)
        self.right_frame.grid_columnconfigure(1, weight=1)
        
        self.add_dataset_button = ttk.Button(self.right_frame, text="Add Dataset")
        self.add_dataset_button.grid(row=0, column=0, columnspan=2, pady=(10, 5), sticky="n")
        
        self.show_history_button = ttk.Button(self.right_frame, text="Show History")
        self.show_history_button.grid(row=1, column=0, columnspan=2, pady=5, sticky="s")
        
        self.toggle_panel = tk.Frame(self.right_frame, bg=left_color)
        self.toggle_panel.grid(row=2, column=0, rowspan=2, columnspan=2, sticky="nsew")
        self.toggle_panel.grid_rowconfigure(0, weight=1)
        self.toggle_panel.grid_columnconfigure(0, weight=1)

        self.label_count = ttk.Label(self.right_frame, background=right_color, foreground=text_color, text=f"Count of Incoming Images: {len(self.shared_data)}")
        #self.label_count.grid(row=4, column=0, padx=(0, 5), sticky="e")
        
        self.get_changes_button = ttk.Button(self.right_frame, text="Get Changes")
        #self.get_changes_button.grid(row=4, column=1, padx=(5,0), sticky="w")
        
        self.commit_button = ttk.Button(self.right_frame, text="Commit")
        self.commit_button.grid(row=4, column=0, padx=(5,0), sticky="e")        

        self.trash_button = ttk.Button(self.right_frame, text="Trash")
        self.trash_button.grid(row=4, column=1, padx=(5,0), sticky="w")

    def toggle_commit_trash_buttons(self):
        # Remove "Get Changes" button
        self.get_changes_button.grid_forget()
        
        # Add "Commit" and "Trash" buttons
        self.commit_button.grid(row=4, column=0, sticky="sw")
        self.trash_button.grid(row=4, column=1, sticky="se")



