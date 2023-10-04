from asyncio.windows_events import NULL
from tkinter import ttk, filedialog
import tkinter as tk
import threading
import zipfile
import os

from views.gallery_view import GalleryView




class DataUploadView(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master) 
        self.uploaded_files = []
        self.extracted_folder_paths = []
        self.create_widgets()


    def create_widgets(self):
        # Overall frame grid configuration
        self.grid_rowconfigure(0, weight=0)  
        self.grid_rowconfigure(1, weight=1)  
        self.grid_rowconfigure(2, weight=2) 
        self.grid_rowconfigure(3, weight=0) 

        self.grid_columnconfigure(0, weight=1)  
        self.grid_columnconfigure(1, weight=3)  # This ensures the majority of horizontal space is occupied by the notebook

        # Header label
        self.header_label = ttk.Label(self, text="Filtering options")
        self.header_label.grid(row=1, column=1, padx=10, pady=10, sticky='')

        # Create the notebook (tabbed interface)
        self.notebook = ttk.Notebook(self)
        self.notebook.grid(row=2, column=1, rowspan=1, padx=10, pady=10, sticky='nsew')

        # Tabs for the notebook
        self.create_race_tab()
        self.create_age_tab()
        self.create_emotion_tab()

        # Upload button
        self.upload_button = ttk.Button(self, text="Upload Dataset", command=self.upload_dataset)
        self.upload_button.grid(row=1, column=0, padx=10, pady=(2,0), sticky='sw')

        # Image listbox
        self.dataset_filenames_listbox = tk.Listbox(self)
        self.dataset_filenames_listbox.grid(row=2, column=0, padx=10, pady=2, sticky='nsew')

        # Process button
        self.process_button = ttk.Button(self, text="Process", command=self.process_images)
        self.process_button.grid(row=3, column=1, padx=20, pady=20, sticky='e')


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
        
        
        file_path = filedialog.askopenfilename(filetypes=[('ZIP files', '*.zip'), ('CSV files', '*.csv')])
        if file_path:
            filename = os.path.basename(file_path)
            self.uploaded_files.append(file_path)
            self.dataset_filenames_listbox.insert(tk.END, filename)

            # Check if the uploaded file is a ZIP file and extract it
            if file_path.endswith('.zip'):
                self.extract_zip_file(file_path)
                self.process_button['text'] = "loading..."
                self.process_button['state'] = tk.DISABLED


    def process_images(self):
        self.master.views['Gallery'].load_images_from_folder(self.extracted_folder_paths)
        self.master.change_view('Gallery')
        # we can pass the extracted image paths into the nn to be loaded + filtered
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
        self.process_button['text'] = "Process"
        self.process_button['state'] = tk.NORMAL


        
