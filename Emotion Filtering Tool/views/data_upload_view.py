from ast import arg
from asyncio.windows_events import NULL
from doctest import debug
from tkinter import ttk, filedialog
import tkinter as tk
import threading
import zipfile
import tarfile
import os
import random
import shutil
from PIL import Image, ImageTk
from io import BytesIO
import json
import csv
import cv2
import xml.etree.ElementTree as ET
import time
import tkinter.messagebox as messagebox
from deepface import DeepFace
import tensorflow as tf


bg1 = "#bfbfbf"
bg2 = "#e5e5e5"
darker_bg = "#1f1f1f"
secondary_bg = "#1e1e1e"
text_color = "#F0F0F0"

class DataUploadView(ttk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.uploaded_files = []
        self.process_lock = threading.Lock()
        self.dataset_image_counts = {}
        self.image_tag_mappings = {}
        self.label_mapping = {
            'man': 'male',
            'boy': 'male',
            'guy': 'male',
            'male person': 'male',
            'woman': 'female',
            'girl': 'female',
            'lady': 'female',
            'female person': 'female',
        }
        self.create_widgets()


    def create_widgets(self):
        self.row_frames = [tk.Frame(self, bg=color) for color in [bg1]]
        for i, row_frame in enumerate(self.row_frames):
            row_frame.grid(row=i, columnspan=2, sticky='nsew')
            
        # Overall frame grid configuration
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1) # filtering options label, upload button, 
        self.grid_rowconfigure(2, weight=2) # notebook , dataset filename listbox
        self.grid_rowconfigure(3, weight=0) # process button

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=3)

        # Filtering Options label
        label_font = ("Helvetica", 14)
        self.header_label = ttk.Label(self, text="Filtering options", font=label_font)
        self.header_label.grid(row=1, column=1, padx=10, pady=(20, 10), sticky='')

        # Create the notebook (tabbed interface)
        self.notebook = ttk.Notebook(self)
        self.notebook.grid(row=2, column=1, rowspan=1, padx=10, pady=10, sticky='nsew')

        # Tabs for the notebook
        self.create_emotion_tab()
        self.create_age_tab()
        self.create_race_tab()
        self.create_gender_tab()

        # Upload button
        self.upload_button = ttk.Button(self, text="Upload Dataset", command=self.upload_dataset)
        self.upload_button.grid(row=1, column=0, padx=10, pady=(2, 0), sticky='sw')

        # Dataset Filename Listbox
        self.dataset_filenames_listbox = tk.Listbox(self, selectmode=tk.MULTIPLE, bg=bg2)
        self.dataset_filenames_listbox.grid(row=2, column=0, padx=10, pady=2, sticky='nsew')

        style = ttk.Style()
        style.configure("Red.TButton", foreground="red")

        self.process_button = ttk.Button(self, text="Process", command=self.start_processing_images, style="Red.TButton")
        self.process_button.grid(row=3, column=1, padx=20, pady=20, sticky='e')
        self.process_button['text'] = "no dataset uploaded"
        self.process_button['state'] = tk.DISABLED


    def create_emotion_tab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Emotions")

        emotion_options = ["Angry", "Crying", "Sad", "Surprised", "Confused", "Shy"] 
        self.emotion_vars = {option: tk.BooleanVar() for option in emotion_options}  # Each emotion gets its own BooleanVar
        
        for i, option in enumerate(emotion_options):
            ttk.Checkbutton(frame, text=option, variable=self.emotion_vars[option]).grid(row=i, column=0, sticky='w')

    def create_age_tab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Age(wip)")

        age_options = ["Kids", "Adult", "Elder"]
        self.age_vars = {option: tk.BooleanVar() for option in age_options}
        for i, option in enumerate(age_options):
            ttk.Checkbutton(frame, text=option, variable=self.age_vars[option]).grid(row=i, column=0, sticky='w')
            
    def create_race_tab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Race(wip)")

        race_options = ["Option1", "Option2", "Option3"]  
        self.race_vars = {option: tk.BooleanVar() for option in race_options}
        

        for i, option in enumerate(race_options):
            ttk.Checkbutton(frame, text=option, variable=self.race_vars[option]).grid(row=i, column=0, sticky='w')
            
    def create_gender_tab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Gender")

        gender_options = ["male", "female"]  
        self.gender_vars = {option: tk.BooleanVar() for option in gender_options}
        for i, option in enumerate(gender_options):
            ttk.Checkbutton(frame, text=option, variable=self.gender_vars[option]).grid(row=i, column=0, sticky='w')
    
    '''
    Upload Dataset
    '''
    def get_full_extension(file_path):
        basename = os.path.basename(file_path)
        if basename.endswith('.tar.gz'):
            return '.tar.gz'
        elif basename.endswith('.tar.bz2'):
            return '.tar.bz2'
        else:
            return os.path.splitext(file_path)[-1].lower()

    def upload_dataset(self):
        file_path = filedialog.askopenfilename(filetypes=[
            ('All Supported Types', '*.zip *.tar *.tar.gz *.tar.bz2'),
            ('ZIP files', '*.zip'),
            ('TAR files', '*.tar *.tar.gz *.tar.bz2'),
            #('All Supported Types', '*.zip *.tar *.tar.gz *.tar.bz2 *.json *.xml *.csv *.npy *.npz *.hdf5'),
            # ('JSON files', '*.json'),
            # ('XML files', '*.xml'),
            # ('CSV files', '*.csv'),
            # ('Numpy files', '*.npy *.npz'),
            # ('HDF5 files', '*.hdf5'),
        ])
        if file_path:
            self.process_button['text'] = "Loading..."
            self.process_button['state'] = tk.DISABLED

            basename = os.path.basename(file_path)
            if basename.endswith('.tar.gz'):
                extension = '.tar.gz'
            elif basename.endswith('.tar.bz2'):
                extension = '.tar.bz2'
            else:
                extension = os.path.splitext(file_path)[-1].lower()
 
            if extension in ['.zip', '.tar', '.tar.gz', '.tar.bz2']:
                self.extract_archive(file_path, extension)
    
    '''
    EXTRACT ARCHIVES
        Accepts .zip, .tar, .tar.gz, .tar.bz2
    '''
    def extract_archive(self, archive_path, ext):
        #ext = os.path.splitext(archive_path)[1]
        if ext == '.gz' or ext == '.bz2':  # Handle tar.gz and tar.bz2
            ext = '.'.join(os.path.basename(archive_path).split('.')[-2:])
        threading.Thread(target=self._threaded_extraction, args=(archive_path, ext), daemon=True).start()


    def _threaded_extraction(self, archive_path, ext):
        base_name = os.path.basename(archive_path).replace(ext, '')
        extract_dir = os.path.join(os.path.dirname(archive_path), base_name)

        if os.path.exists(extract_dir):
            shutil.rmtree(extract_dir)
        os.mkdir(extract_dir)
        if ext == '.zip':
            with zipfile.ZipFile(archive_path, 'r') as archive_ref:
                archive_ref.extractall(extract_dir)
        elif ext in ['.tar', '.tar.gz', '.tar.bz2']:
            with tarfile.open(archive_path) as archive_ref:
                archive_ref.extractall(extract_dir)

        # Move all image files to the root extract directory (flatten the structure)
        image_count = 0  

        for dirpath, _, filenames in os.walk(extract_dir):
            for f in filenames:
                if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.tif')):
                    # Modify filename to make it unique based on its original directory
                    subdir_name = os.path.basename(dirpath)
                    unique_filename = f"{subdir_name}_{f}" if subdir_name != base_name else f

                    destination = os.path.join(extract_dir, unique_filename)
                    if os.path.exists(destination):  # In case even the unique name exists (very rare but just to be safe)
                        unique_filename = f"{image_count}_{f}"  # Use UUID for guaranteed uniqueness
                        destination = os.path.join(extract_dir, unique_filename)

                    shutil.move(os.path.join(dirpath, f), destination)
                    image_count += 1
        self.dataset_image_counts[extract_dir] = image_count
        # Remove any leftover empty directories
        for dirpath, _, _ in os.walk(extract_dir, topdown=False):
            if not os.listdir(dirpath):  # Empty directory
                os.rmdir(dirpath)
            
        entry_text = f"{base_name} ({image_count})"
        # Add the root extraction directory name to the listbox
        self.dataset_filenames_listbox.insert(tk.END, entry_text)

        self.master.after(0, self._finish_extraction) 

    def _finish_extraction(self):
        self.process_button['text'] = "Process"
        self.process_button['state'] = tk.NORMAL    

    '''
    PROCESSING IMAGES
    '''
    def start_processing_images(self):
        selected_indices = self.dataset_filenames_listbox.curselection()
    
        # Check for selected options
        selected_emotions = [k for k, v in self.emotion_vars.items() if v.get()]
        selected_ages = [k for k, v in self.age_vars.items() if v.get()]
        selected_races = [k for k, v in self.race_vars.items() if v.get()]
        selected_genders = [k for k, v in self.gender_vars.items() if v.get()]
        actions = {}
        if selected_emotions: actions['emotion']=selected_emotions
        if selected_ages: actions['age']=selected_ages
        if selected_genders: actions['gender']=selected_genders
        if selected_races: actions['race']=selected_races
        # If no datasets or no filtering options are selected, show an informative message
        if not selected_indices:
            messagebox.showinfo("No Datasets Selected", "Please select a dataset to process.")
            return
        elif not (selected_emotions or selected_ages or selected_races or selected_genders):
            messagebox.showinfo("No Filtering Options Selected", "Please select at least one filtering option.")
            return

        with self.process_lock:
            threading.Thread(target=self.process_images, args=(actions, selected_indices,)).start()
        self.master.change_view('Gallery')



    # Neural netork source https://github.com/serengil/deepface
    def neural_network_filter(self, image_paths, actions): #, sizeX, sizeY):
        accepted_images = {}
        try:
            for image_path in image_paths:
                # Analyzing age, gender, race, and emotion for the current image
                analysis = DeepFace.analyze(img_path=image_path, actions=list(actions.keys()), detector_backend='mtcnn', enforce_detection=False)
                self.processed_images_count += 1
                self.master.views['Gallery'].update_progress(self.processed_images_count)
                print(analysis)
                face_data = analysis[0]
                
                features = {}
                if actions.get('emotion'):
                    features['emotion'] = face_data['dominant_emotion'].lower()
                if actions.get('gender'):
                    features['gender'] = self.label_mapping.get(face_data['dominant_gender'].lower(), face_data['dominant_gender'].lower())
                if actions.get('race'):
                    features['race'] = face_data['dominant_race'].lower()
                if actions.get('age'):
                    features['age'] = str(face_data['age'])


                # Check if the user's desired emotion matches the detected dominant emotion
                if (
                    (not actions.get('emotion') or features['emotion'] in actions['emotion']) and
                    (not actions.get('age') or features['age'] in actions.get('age')) and
                    (not actions.get('race') or features['race'] in actions.get('race')) and
                    (not actions.get('gender') or features['gender'] in actions.get('gender'))
                ):
                    accepted_images[image_path] = features

            return accepted_images

        except Exception as e:
            print(f"Error analyzing images. Error: {e}")
            return {}

    def process_images(self, actions, selected_indices):
        BATCH_SIZE = 5
    
        selected_folders = [folder_path for idx, folder_path in enumerate(self.dataset_image_counts.keys()) if idx in selected_indices]
    
        total_images = sum(self.dataset_image_counts[folder] for folder in selected_folders)
        self.master.views['Gallery'].set_progress_maximum(total_images)
        self.processed_images_count = 0
    
        base_dir = os.path.dirname(selected_folders[0]) if selected_folders else ""
        candidate_folder = os.path.join(base_dir, "Candidates").replace("\\", "/")

        if os.path.exists(candidate_folder):
            shutil.rmtree(candidate_folder)
            print(f"Deleted existing candidates folder: {candidate_folder}")

        os.mkdir(candidate_folder)

        for folder_path in selected_folders:
            if folder_path == candidate_folder:
                continue

            for batch in self._batched_image_paths(folder_path, BATCH_SIZE):
                accepted_images_dict = self.neural_network_filter(batch, actions)
                for img_path, features in accepted_images_dict.items():
                    candidate_image_path = os.path.join(candidate_folder, os.path.basename(img_path))
                    actual_tags = list(features.values())
                    self.image_tag_mappings[candidate_image_path] = {'original_path': img_path, 'tags': actual_tags}
                    shutil.copy(img_path, candidate_image_path)
                    self.master.views['Gallery'].receive_data(candidate_folder, {candidate_image_path: self.image_tag_mappings.get(candidate_image_path)})
                    self.master.views['Gallery'].update_idletasks()

    def _batched_image_paths(self, folder_path, BATCH_SIZE):
        """
        A generator that yields image paths in batches of size BATCH_SIZE
        """
        img_paths = (os.path.join(folder_path, img_file) for img_file in os.listdir(folder_path))
        batch = []
        for img_path in img_paths:
            batch.append(img_path)
            if len(batch) == BATCH_SIZE:
                yield batch
                batch = []
        if batch:  # for any remaining images in the last batch
            yield batch

                    

                

