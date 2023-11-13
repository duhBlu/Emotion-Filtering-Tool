import random
import shutil
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
import os
import json
import zipfile

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
            ('All Supported Types', '*.json *.xml *.csv *.npy *.npz *.hdf5'),
            ('JSON files', '*.json'),
            ('XML files', '*.xml'),
            ('CSV files', '*.csv'),
            ('Numpy files', '*.npy *.npz'),
            ('HDF5 files', '*.hdf5')
        ]
        export_path = filedialog.asksaveasfilename(defaultextension=".json",
                                                 filetypes=file_formats,
                                                 title="Export As")
        if export_path:
            ext = os.path.splitext(export_path)[-1].lower()
            export_dir = os.path.dirname(export_path)
            file_name = os.path.basename(export_path)
        else:
            return
       
        # json only works for now, but just as sample functionality, we should allow exporting to something else
        if ext == ".json":
            self.export_json(export_dir, file_name)
        elif ext == ".xml":
            self.export_xml(export_dir, file_name)
        elif ext == ".csv":
            self.export_csv(export_dir, file_name)
        elif ext in [".npy", ".npz"]:
            self.export_numpy(export_dir, file_name)
        elif ext == ".hdf5":
            self.export_hdf5(export_dir, file_name)
        else:
            print("Unsupported file format")  # Handle this case in your UI

    def export_json(self, export_dir, file_name):
        # Create an 'images' subdirectory within the export directory
        images_dir = os.path.join(export_dir, 'images')
        if not os.path.exists(images_dir):
            os.makedirs(images_dir)

        # Build the export data dictionary
        export_data = {}
        for path in self.paths_pending_export:
            # Get the filename and create a relative path within the 'images' directory
            filename = os.path.basename(path)
            relative_path = os.path.join('images', filename)
            image_info = self.master.master_image_dict[path]
        
            # Add the image file to the 'images' directory
            shutil.copy(path, os.path.join(images_dir, filename))
        
            # Use the relative path for the image in the JSON data
            export_data[relative_path] = {
                'tags': image_info.get('tags', {}),
                # Include other relevant metadata as needed
            }
    
        # Serialization of JSON data
        json_file_path = os.path.join(export_dir, file_name)
        with open(json_file_path, 'w', encoding='utf-8') as json_file:
            json.dump(export_data, json_file, ensure_ascii=False, indent=4)

        # Create a zip file that includes the JSON file and the 'images' directory
        zip_file_path = os.path.join(export_dir, 'dataset.zip')
        with zipfile.ZipFile(zip_file_path, 'w') as zipf:
            # Add the JSON file
            zipf.write(json_file_path, os.path.basename(json_file_path))
        
            # Add all files from the 'images' directory
            for root, _, files in os.walk(images_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    zipf.write(file_path, os.path.relpath(file_path, start=export_dir))
        
        # Optionally, clear the export data and image files now that they have been zipped
        shutil.rmtree(images_dir)
        os.remove(json_file_path)

        # Clear the paths from pending export and remove them from the master_image_dict
        for path in self.paths_pending_export:
            del self.master.master_image_dict[path]
        self.paths_pending_export.clear()

        print(f"Exported data to {zip_file_path} successfully.")



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



