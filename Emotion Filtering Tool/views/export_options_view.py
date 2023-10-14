from email.mime import image
import random
import tkinter as tk
from tkinter import ttk
import subprocess
from tkinter import filedialog
import os
from zipfile import ZipFile

class ExportOptionView(ttk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.image_count_var = tk.StringVar()
        self.new_images = []
        self.create_widgets()
        self.sample_tags = ["happy", "sad", "angry"]
        self.tagged_images = {}
        
        
    def create_widgets(self):
        # Overall Grid Configuration
        self.grid_columnconfigure(0, weight=4)
        self.grid_columnconfigure(1, weight=0)  # For the divider
        self.grid_columnconfigure(2, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Colors
        bg1 = "#bfbfbf"  # Light color for left column
        bg2 = "#e5e5e5"  # Darker color for right column
        divider_color = "#84848e"  # Even darker color for the divider

        # Left Column Setup
        self.left_frame = tk.Frame(self, bg=bg1)
        self.left_frame.grid(row=0, column=0, sticky="nsew")
        self.left_frame.grid_columnconfigure(0, weight=1)
        self.left_frame.grid_rowconfigure(0, weight=5)
        self.left_frame.grid_rowconfigure(1, weight=1)
        
        self.toggle_frame = tk.Frame(self.left_frame, bg=bg2)
        self.toggle_frame.grid(row=0, column=0, padx=10, pady=10,  sticky="nsew")
        self.toggle_frame.grid_columnconfigure(0, weight=1)
        self.toggle_frame.grid_rowconfigure(0, weight=1)
        
        self.revert_button = ttk.Button(self.left_frame, text="Revert Changes")
        self.revert_button.grid(row=1, column=0, padx=(0, 10), pady=(0, 10), sticky="sw")
        
        self.export_button = ttk.Button(self.left_frame, text="Export", command=self.export_dataset)
        self.export_button.grid(row=1, column=0, padx=(0, 10), pady=(0, 10), sticky="se")
        
        # Divider
        self.divider = tk.Frame(self, bg=divider_color, width=2)
        self.divider.grid(row=0, column=1, sticky="ns")

        # Right Column Setup
        self.right_frame = tk.Frame(self, bg=bg1)
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
        
        self.toggle_panel = tk.Frame(self.right_frame, bg=bg2)
        self.toggle_panel.grid(row=2, column=0, rowspan=2, columnspan=2, sticky="nsew", padx=10, pady=10, ipadx=10, ipady=10)
        self.toggle_panel.grid_rowconfigure(0, weight=1)
        self.toggle_panel.grid_columnconfigure(0, weight=1)

        self.label_count = ttk.Label(self.right_frame, background=bg1, textvariable=self.image_count_var)
        self.label_count.grid(row=4, column=0, padx=(0, 5), sticky="e")
        self.update_image_count()
        
        self.get_changes_button = ttk.Button(self.right_frame, text="Get Changes")
        self.get_changes_button.grid(row=4, column=1, padx=(5,0), sticky="w")
        
        self.commit_button = ttk.Button(self.right_frame, text="Commit")
        #self.commit_button.grid(row=4, column=0, padx=(5,0), sticky="e")        

        self.trash_button = ttk.Button(self.right_frame, text="Trash")
        #self.trash_button.grid(row=4, column=1, padx=(5,0), sticky="w")
    
    def receive_images(self, images):
        self.new_images = images
        self.update_image_count() 

    def update_image_count(self):
        count = len(self.new_images)
        self.image_count_var.set(f"Count of Incoming Images: {count}")
        
    def toggle_commit_trash_buttons(self):
        # Remove "Get Changes" button
        self.get_changes_button.grid_forget()
        
        # Add "Commit" and "Trash" buttons
        self.commit_button.grid(row=4, column=0, sticky="sw")
        self.trash_button.grid(row=4, column=1, sticky="se")
        
    def export_dataset(self):    
        for image in self.new_images:
            tag = random.choice(self.sample_tags)
        
            if tag not in self.tagged_images:
                self.tagged_images[tag] = []
        
            self.tagged_images[tag].append(image)
        file_formats = [
            ('All Supported Types', '*.zip *.tar *.tar.gz *.tar.bz2 *.json *.xml *.csv *.npy *.npz *.hdf5'),
            ('ZIP files', '*.zip'),
            ('TAR files', '*.tar'),
            ('TAR.GZ files', '*.tar.gz'),
            ('TAR.BZ2 files', '*.tar.bz2'),
            ('JSON files', '*.json'),
            ('XML files', '*.xml'),
            ('CSV files', '*.csv'),
            ('Numpy files', '*.npy *.npz'),
            ('HDF5 files', '*.hdf5')
        ]

        file_path = filedialog.asksaveasfilename(defaultextension=".zip",
                                                 filetypes=file_formats,
                                                 title="Export As")
        
        if not file_path:
            return  # User canceled save
        
        ext = os.path.splitext(file_path)[-1].lower()

        if ext == ".zip":
            self.export_zip(file_path, self.tagged_images)
        elif ext in [".tar", ".tar.gz", ".tar.bz2"]:
            self.export_tar(file_path, self.tagged_images, ext)
        elif ext == ".json":
            self.export_json(file_path, self.tagged_images)
        elif ext == ".xml":
            self.export_xml(file_path, self.tagged_images)
        elif ext == ".csv":
            self.export_csv(file_path, self.tagged_images)
        elif ext in [".npy", ".npz"]:
            self.export_numpy(file_path, self.tagged_images, ext)
        elif ext == ".hdf5":
            self.export_hdf5(file_path, self.tagged_images)
        else:
            print("Unsupported file format")  # Handle this case in your UI

    def export_zip(self, file_path, tagged_images):
        with ZipFile(file_path, 'w') as zf:
            for tag, images in tagged_images.items():
                for image in images:
                    zf.write(image, os.path.join(tag, image)) 

    def export_tar(self, file_path, tagged_images, ext):
        print(f"Exporting as TAR ({ext}) to {file_path}")
        # Your TAR export logic here

    def export_json(self, file_path, tagged_images):
        print(f"Exporting as JSON to {file_path}")
        # Your JSON export logic here

    def export_xml(self, file_path, tagged_images):
        print(f"Exporting as XML to {file_path}")
        # Your XML export logic here

    def export_csv(self, file_path, tagged_images):
        print(f"Exporting as CSV to {file_path}")
        # Your CSV export logic here

    def export_numpy(self, file_path, tagged_images, ext):
        print(f"Exporting as NumPy ({ext}) to {file_path}")
        # Your NumPy export logic here

    def export_hdf5(self, file_path, tagged_images):
        print(f"Exporting as HDF5 to {file_path}")
        # Your HDF5 export logic here



