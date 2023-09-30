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
        # Overall frame grid configuration
        self.grid_rowconfigure(0, weight=0)  # Header label remains fixed size
        self.grid_rowconfigure(1, weight=1)  # Upload button and listbox
        self.grid_rowconfigure(2, weight=1)  # Notebook expands vertically
        self.grid_rowconfigure(3, weight=1)  # Process button remains fixed size

        self.grid_columnconfigure(0, weight=1)  
        self.grid_columnconfigure(1, weight=3)  # This ensures the majority of horizontal space is occupied by the notebook
        self.grid_columnconfigure(2, weight=1) 

        # Header label
        self.header_label = ttk.Label(self, text="Filtering options")
        self.header_label.grid(row=0, column=1, padx=10, pady=10, sticky='ew', columnspan=3)

        # Create the notebook (tabbed interface)
        self.notebook = ttk.Notebook(self)
        self.notebook.grid(row=1, column=1, rowspan=2, padx=10, pady=10, sticky='nsew')

        # Tabs for the notebook
        self.create_race_tab()
        self.create_age_tab()
        self.create_emotion_tab()

        # Upload button
        self.upload_button = ttk.Button(self, text="Upload Dataset", command=self.upload_dataset)
        self.upload_button.grid(row=1, column=0, padx=10, pady=2, sticky='nw')

        # Image listbox
        self.image_listbox = tk.Listbox(self)
        self.image_listbox.grid(row=2, column=0, padx=10, pady=2, sticky='nsew')

        # Process button
        self.process_button = ttk.Button(self, text="Process", command=self.process_images)
        self.process_button.grid(row=3, column=2, padx=10, pady=10, sticky='e')

        # Loading label
        self.loading_label = ttk.Label(self, text="Loading...")
        self.loading_label.grid(row=3, column=0, sticky='w')
        self.loading_label.grid_remove()


    def create_race_tab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Race")

        # Radiobuttons for the "Race" tab
        race_options = ["Option1", "Option2", "Option3"]  # Modify these options accordingly
        self.race_var = tk.StringVar(value=race_options[0])

        for i, option in enumerate(race_options):
            ttk.Radiobutton(frame, text=option, variable=self.race_var, value=option).grid(row=i, column=0, sticky='w')

    def create_age_tab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Age")

        # Radiobuttons for the "Age" tab
        age_options = ["Option1", "Option2", "Option3"]  # Modify these options accordingly
        self.age_var = tk.StringVar(value=age_options[0])

        for i, option in enumerate(age_options):
            ttk.Radiobutton(frame, text=option, variable=self.age_var, value=option).grid(row=i, column=0, sticky='w')

    def create_emotion_tab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Emotions")

        # Radiobuttons for the "Emotions" tab
        emotion_options = ["Option1", "Option2", "Option3"]  # Modify these options accordingly
        self.emotion_var = tk.StringVar(value=emotion_options[0])

        for i, option in enumerate(emotion_options):
            ttk.Radiobutton(frame, text=option, variable=self.emotion_var, value=option).grid(row=i, column=0, sticky='w')

    
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


        
