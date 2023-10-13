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
import xml.etree.ElementTree as ET
import time
import tkinter.messagebox as messagebox

bg1 = "#bfbfbf"
bg2 = "#e5e5e5"
darker_bg = "#1f1f1f"
secondary_bg = "#1e1e1e"
text_color = "#F0F0F0"

class DataUploadView(ttk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.uploaded_files = []
        self.extracted_folders_dict = {}
        self.image_tag_mappings = {}
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
        self.emotion_var = tk.StringVar(value=emotion_options[0])

        for i, option in enumerate(emotion_options):
            ttk.Radiobutton(frame, text=option, variable=self.emotion_var, value=option).grid(row=i, column=0, sticky='w')

    def create_age_tab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Age(wip)")

        age_options = ["Kids", "Adult", "Elder"]
        self.age_var = tk.StringVar(value=age_options[0])

        for i, option in enumerate(age_options):
            ttk.Radiobutton(frame, text=option, variable=self.age_var, value=option).grid(row=i, column=0, sticky='w')
            
    def create_race_tab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Race(wip)")

        race_options = ["Option1", "Option2", "Option3"]  
        self.race_var = tk.StringVar(value=race_options[0])

        for i, option in enumerate(race_options):
            ttk.Radiobutton(frame, text=option, variable=self.race_var, value=option).grid(row=i, column=0, sticky='w')
    
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

        if extract_dir not in self.extracted_folders_dict:
            self.extracted_folders_dict[extract_dir] = []

        if os.path.exists(extract_dir):
            shutil.rmtree(extract_dir)

        os.mkdir(extract_dir)

        if ext == '.zip':
            with zipfile.ZipFile(archive_path, 'r') as archive_ref:
                archive_ref.extractall(extract_dir)
        elif ext in ['.tar', '.tar.gz', '.tar.bz2']:
            with tarfile.open(archive_path) as archive_ref:
                archive_ref.extractall(extract_dir)


        # This code just checks if there are any subfolders in the uploaded file
        # If subfolder has images, save filepath.
        # once all subfolders have been checked, move the sub folder to new directory
        # then cleans up the file directory of any remaining empty folders.
        # we are left with only folders with images, the filenames of those folders will be added to the list box of uploaded files.
        subfolders_with_images = []
        folders_to_remove = []

        for dirpath, _, filenames in os.walk(extract_dir): # os.walk is cool
            has_images = any(f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.tif')) for f in filenames)
            if has_images:
                subfolders_with_images.append(dirpath)
    
        for folder in subfolders_with_images:
            target_folder = os.path.join(extract_dir, os.path.basename(folder))
            if not os.path.exists(target_folder):
                os.mkdir(target_folder)
        
            for f in os.listdir(folder):
                fpath = os.path.join(folder, f)
                if os.path.isfile(fpath):
                    shutil.move(fpath, os.path.join(target_folder, f))
                    folders_to_remove_after_walk = []
    
        # First move the image files to the respective directories at root level.
        for dirpath, _, filenames in os.walk(extract_dir):
            has_images = any(f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.tif')) for f in filenames)
        
            if has_images:
                target_folder = os.path.join(extract_dir, os.path.basename(dirpath))
                if dirpath != target_folder:
                    if not os.path.exists(target_folder):
                        os.makedirs(target_folder)
                    for f in filenames:
                        if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.tif')):
                            shutil.move(os.path.join(dirpath, f), os.path.join(target_folder, f))
    
        # Now, check for directories to remove (start from leaf and go upwards).
        for dirpath, _, _ in os.walk(extract_dir, topdown=False):
            if not os.listdir(dirpath):  # Empty directory
                os.rmdir(dirpath)
                folders_to_remove_after_walk.append(dirpath) 

        # Populate the Listbox and dictionary with the final set of folders
        final_subdirs = [d for d in os.listdir(extract_dir) if os.path.isdir(os.path.join(extract_dir, d))]
        if final_subdirs:
            for subdir in final_subdirs:
                self.extracted_folders_dict[extract_dir].append(os.path.join(extract_dir, subdir))
                self.dataset_filenames_listbox.insert(tk.END, subdir)
        else:
            self.extracted_folders_dict[extract_dir] = []
            root_folder_name = os.path.basename(extract_dir)
            self.dataset_filenames_listbox.insert(tk.END, root_folder_name)

        self.master.after(0, self._finish_extraction)

    def _finish_extraction(self):
        self.process_button['text'] = "Process"
        self.process_button['state'] = tk.NORMAL    

    '''
    PROCESSING IMAGES
    '''
    def start_processing_images(self):
        selected_indices = self.dataset_filenames_listbox.curselection()
        if not selected_indices:
            messagebox.showinfo("No Datasets Selected", "Please select a dataset to process.")
            return
        threading.Thread(target=self.process_images).start()
        self.master.change_view('Gallery')

    def neural_network_filter(self, image_path):
        # Dev note
        # This function should actually call the neural network to decide if an image is a candidate or not
        # Right now it just simulates the behavior with a random choice.
        is_accepted = random.choice([True, False])
        
        # If the image is accepted, add the tags
        # just for testing but will need to re-implement this
        if is_accepted:
            tags = [
                self.emotion_var.get(),
                self.age_var.get(),
                self.race_var.get()
            ]
            self.image_tag_mappings[image_path] = tags  # Associate the tags with this image
        print(self.image_tag_mappings)  
        return is_accepted

    def process_images(self):
        # Get the indices of selected items
        selected_indices = self.dataset_filenames_listbox.curselection()

        # Get the list of extracted folder paths from the dictionary
        all_extracted_folders = []
        for root_folder, sub_folders in self.extracted_folders_dict.items():
            all_extracted_folders.extend(sub_folders)

        # Create directory to hold "candidate" images
        base_dir = os.path.dirname(all_extracted_folders[0]) if all_extracted_folders else ""
        candidate_folder = os.path.join(base_dir, "Candidates").replace("\\", "/")

        # Check if "candidates" folder already exists; if yes, then delete it
        if os.path.exists(candidate_folder):
            shutil.rmtree(candidate_folder)
            print(f"Deleted existing candidates folder: {candidate_folder}")

        # Create a new "candidates" folder
        os.mkdir(candidate_folder)

        for index in selected_indices:
            folder_path = all_extracted_folders[index]  # Use indexed folder path from all_extracted_folders

            # Make sure folder_path and candidate_folder are not the same
            if folder_path == candidate_folder:
                continue

            for img_file in os.listdir(folder_path):
                img_path = os.path.join(folder_path, img_file)

                is_accepted = self.neural_network_filter(img_path)  # Call the neural network filtering function

                if is_accepted:
                    # Copy it to the "candidates" folder
                    candidate_image_path = os.path.join(candidate_folder, img_file)
                    shutil.copy(img_path, candidate_image_path)
                    # Send this image path to GalleryView to load and display
                    # Only send the mapping of the current image
                    self.master.views['Gallery'].receive_data(candidate_folder, {candidate_image_path: self.image_tag_mappings.get(img_path, [])})

