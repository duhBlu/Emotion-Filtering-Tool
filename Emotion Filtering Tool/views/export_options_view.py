import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
import os
import h5py
import numpy as np

class ExportOptionView(ttk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.image_count_var = tk.StringVar()
        self.paths_pending_export = []
        self.create_widgets()
        
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
        
        self.revert_button = ttk.Button(self.left_frame, text="Revert Changes", state='disabled')
        self.revert_button.grid(row=1, column=0, padx=(10, 10), pady=(0, 10), sticky="sw")
        
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
        
        self.add_dataset_button = ttk.Button(self.right_frame, text="Add Dataset", state='disabled')
        self.add_dataset_button.grid(row=0, column=0, columnspan=2, pady=(10, 5), sticky="n")
        
        self.show_history_button = ttk.Button(self.right_frame, text="Show History", state='disabled')
        self.show_history_button.grid(row=1, column=0, columnspan=2, pady=5, sticky="s")
        
        self.toggle_panel = tk.Frame(self.right_frame, bg=bg2)
        self.toggle_panel.grid(row=2, column=0, rowspan=2, columnspan=2, sticky="nsew", padx=10, pady=10, ipadx=10, ipady=10)
        self.toggle_panel.grid_rowconfigure(0, weight=1)
        self.toggle_panel.grid_columnconfigure(0, weight=1)

        self.label_count = ttk.Label(self.right_frame, background=bg1, textvariable=self.image_count_var)
        self.label_count.grid(row=4, column=0, padx=(0, 5), sticky="e")
        self.update_image_count()
        
        self.get_changes_button = ttk.Button(self.right_frame, text="Get Changes", state='disabled')
        self.get_changes_button.grid(row=4, column=1, padx=(5,0), sticky="w")
        
        self.commit_button = ttk.Button(self.right_frame, text="Commit", state='disabled')
        #self.commit_button.grid(row=4, column=0, padx=(5,0), sticky="e")        

        self.trash_button = ttk.Button(self.right_frame, text="Trash", state='disabled')
        #self.trash_button.grid(row=4, column=1, padx=(5,0), sticky="w")
    
    def receive_images(self, image_paths):
        self.paths_pending_export.extend(image_paths)
        self.update_image_count() 

    def update_image_count(self):
        count = len(self.paths_pending_export)
        self.image_count_var.set(f"Count of Incoming Images: {count}")
        
    def toggle_commit_trash_buttons(self):
        # Remove "Get Changes" button
        self.get_changes_button.grid_forget()
        
        # Add "Commit" and "Trash" buttons
        self.commit_button.grid(row=4, column=0, sticky="sw")
        self.trash_button.grid(row=4, column=1, sticky="se")
        
    def export_dataset(self):    
        file_formats = [
            ('All Supported Types', '*.hdf5'),
            ('HDF5 files', '*.hdf5')
        ]
        export_path = filedialog.asksaveasfilename(defaultextension=".hdf5",
                                                 filetypes=file_formats,
                                                 title="Export As")
        if export_path:
            ext = os.path.splitext(export_path)[-1].lower()
            export_dir = os.path.dirname(export_path)
            file_name = os.path.basename(export_path)
        else:
            return
       
        # json only works for now, but just as sample functionality, we should allow exporting to something else
        if ext == ".hdf5":
            self.export_hdf5(export_dir, file_name)
        else:
            print("Unsupported file format")

    def export_hdf5(self, export_dir, file_name):
        hdf5_path = os.path.join(export_dir, file_name)

        with h5py.File(hdf5_path, 'w') as hdf5_file:
            for idx, path in enumerate(self.paths_pending_export):
                image_info = self.master.master_image_dict[path]
                tags = image_info.get('tags', {})

                # Use the image object from the master image dictionary
                pil_image = image_info['photo_object']

                # Convert image to numpy array
                image_np = np.array(pil_image)

                # Create a dataset for the image with a generic name
                dataset_name = f"image_{idx}"
                image_dataset = hdf5_file.create_dataset(name=dataset_name, data=image_np)

                # Store metadata
                for tag, value in tags.items():
                    image_dataset.attrs[tag] = value

        print(f"Exported data to {hdf5_path} successfully.")





