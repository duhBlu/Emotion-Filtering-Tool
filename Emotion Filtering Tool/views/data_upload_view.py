from tkinter import ttk, filedialog
from PIL import Image, ImageTk
import tkinter as tk
import threading
import zipfile
import os
from PIL import Image
import cv2

import asyncio
import aiofiles
from io import BytesIO

from views.gallery_view import GalleryView




class DataUploadView(tk.Frame):
    def __init__(self, main_window, gallery_view=None, master=None):
        super().__init__(master)
        self.main_window = main_window
        self.gallery_view = gallery_view 
        self.uploaded_files = []
        self.extracted_folder_paths = []
        self.create_widgets()

    def create_widgets(self):
        self.upload_button = ttk.Button(self, text="Upload Dataset", command=self.upload_dataset)
        self.upload_button.grid(row=0, column=0, padx=10, pady=10)

        self.image_listbox = tk.Listbox(self)
        self.image_listbox.grid(row=1, column=0, padx=10, pady=10)

        self.process_button = ttk.Button(self, text="Process", command=self.process_images)
        self.process_button.grid(row=2, column=1, padx=10, pady=10, sticky='e')  # This places the button on the bottom right
        
        self.loading_label = ttk.Label(self, text="Loading...")
        self.loading_label.grid(row=3, column=0, columnspan=2)  # Assuming it spans two columns.
        self.loading_label.grid_remove() 

    
    def upload_dataset(self):
        self.loading_label.grid()  # Display the loading label
        self.process_button['state'] = tk.DISABLED
        
        file_path = filedialog.askopenfilename(filetypes=[('ZIP files', '*.zip'), ('CSV files', '*.csv')])
        if file_path:
            filename = os.path.basename(file_path)
            self.uploaded_files.append(file_path)
            self.image_listbox.insert(tk.END, filename)

            # Check if the uploaded file is a ZIP file and extract it
            if file_path.endswith('.zip'):
                self.extract_zip_file(file_path)


    def process_images(self):
        if not self.gallery_view:
            self.gallery_view = GalleryView(master=self.master)
        self.main_window.change_view('Gallery')
        self.gallery_view.load_images_from_folder(self.extracted_folder_paths)
        # Testing this for now. just trying to get the uploaded images to display in the gallery view, but we can pass the extracted image paths into the nn to be loaded + filtered
        # then the candidate paths will then be sent into the gallery view


    def extract_zip_file(self, zip_path):
        # Kick off a new thread to handle the extraction and processing
        threading.Thread(target=self._threaded_extraction, args=(zip_path,)).start()

    def _threaded_extraction(self, zip_path):
        # Create a directory to extract the ZIP content
        extract_dir = os.path.join(os.path.dirname(zip_path), os.path.basename(zip_path).replace('.zip', ''))
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)

        # Set the path to the extracted folder
        self.extracted_folder_paths.append(extract_dir.replace("\\", "/"))
        
        self.master.after(0, self._finish_extraction)


    def _finish_extraction(self):
        self.loading_label.grid_remove()  # Hide the loading label
        self.process_button['state'] = tk.NORMAL


        
