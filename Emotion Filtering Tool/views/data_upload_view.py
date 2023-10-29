import tensorflow as tf
from tensorflow.python.client import device_lib
from tkinter import ttk, filedialog
import tkinter as tk
import threading
import zipfile
import tarfile
import os
import shutil
import tkinter.messagebox as messagebox
from deepface import DeepFace
import queue
import time

bg1 = "#bfbfbf"
bg2 = "#e5e5e5"
bg3 = "#eff0f1"
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
        self.cancellation_requested = False
        self.ui_update_queue = queue.Queue()   
        self.gpu_lock = threading.Lock()
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
        self.emotion_mapping = {
            'angry': 'angry',
            'disgust': 'angry',
            'fear': 'confused',
            'happy': 'happy',
            'sad': 'sad',
            'surprise': 'surprised',
            'neutral': 'neutral'
        }
        self.colors = ['#{:02x}{:02x}{:02x}'.format(i, i, i) for i in range(0, 198, 207 // (15 - 1))] 
        self.create_widgets()
        self.listen_for_ui_updates()  

    '''
    Initialize UI
    '''
    def create_widgets(self):
        self.row_frames = [tk.Frame(self, bg=color) for color in [bg1]]
        for i, row_frame in enumerate(self.row_frames):
            row_frame.grid(row=i, columnspan=2, sticky='nsew')
            
        # Overall frame grid configuration
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1) # filtering options label, upload button, 
        self.grid_rowconfigure(2, weight=2) # notebook , dataset filename listbox
        self.grid_rowconfigure(3, weight=1) # process button

        self.grid_columnconfigure(0, weight=2)
        self.grid_columnconfigure(1, weight=5)

        # Filtering Options label
        label_font = ("Helvetica", 14)
        self.header_label = ttk.Label(self, text="Filtering options", font=label_font)
        self.header_label.grid(row=1, column=1, padx=10, pady=(20, 10), sticky='')

        # Create the notebook (tabbed interface)
        self.notebook = ttk.Notebook(self)
        self.notebook.grid(row=2, column=1, rowspan=2, padx=10, pady=10, sticky='nsew')

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
        self.dataset_filenames_listbox.grid(row=2, column=0, padx=10, pady=(2, 10), sticky='nsew')
        
        self.status_text = tk.Text(self, height=5, bg=bg3, wrap=tk.WORD, state=tk.DISABLED, bd=0, highlightthickness=0)
        self.status_text.grid(row=3, column=0, padx=10, pady=(2, 15), sticky='nsew')


        # Add a scrollbar
        self.status_scroll = tk.Scrollbar(self, command=self.status_text.yview)
        self.status_text.config(yscrollcommand=self.status_scroll.set)
        self.status_scroll.grid(row=3, column=0, sticky='nse')

        self.process_button = ttk.Button(self, text="Process", command=self.start_processing_images)
        self.process_button.grid(row=3, column=1, padx=20, pady=20, sticky='se')
        self.process_button['text'] = "no dataset uploaded"
        self.process_button['state'] = tk.DISABLED
        
        self.width_label = ttk.Label(self, text="Width:")
        self.width_label.grid(row=3, column=1, sticky='w', padx=(20, 0), pady=(220, 0))
    
        self.width_entry = ttk.Entry(self, width=5)
        self.width_entry.grid(row=3, column=1, sticky='w', padx=(60, 0), pady=(220, 0))
        self.width_entry.insert(0, "200")  # default width


        # Move the process button slightly to the right to accommodate the new entries
        self.process_button.grid(row=3, column=1, padx=(250, 20), pady=20, sticky='se')
        
    def create_emotion_tab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Emotions")

        emotion_options = ["Angry", "Crying", "Sad", "Surprised", "Confused", "Shy", "Neutral"] 
        self.emotion_vars = {option: tk.BooleanVar(value=True) for option in emotion_options}  # Each emotion gets its own BooleanVar
        
        for i, option in enumerate(emotion_options):
            ttk.Checkbutton(frame, text=option, variable=self.emotion_vars[option]).grid(row=i, column=0, sticky='w', padx=(20, 0), pady=(15, 0))

    def create_age_tab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Age Range")

        age_options = ["Infants (1 month to 1 year)", "Children (1 year through 12 years)", "Teenagers (13 years through 17 years.)", "Adults (18 years or older)", "Older adults (65 and older)"]
        self.age_vars = {option: tk.BooleanVar(value=True) for option in age_options}
        for i, option in enumerate(age_options):
            ttk.Checkbutton(frame, text=option, variable=self.age_vars[option]).grid(row=i, column=0, sticky='w', padx=(20, 0), pady=(15, 0))
            
    def create_race_tab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Race(wip)")
        race_options = ["Option1", "Option2", "Option3"]  
        self.race_vars = {option: tk.BooleanVar() for option in race_options}
        
        for i, option in enumerate(race_options):
            ttk.Checkbutton(frame, text=option, variable=self.race_vars[option]).grid(row=i, column=0, sticky='w', padx=(20, 0), pady=(15, 0))
            
    def create_gender_tab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Gender")

        gender_options = ["male", "female"]  
        self.gender_vars = {option: tk.BooleanVar(value=True) for option in gender_options}
        for i, option in enumerate(gender_options):
            ttk.Checkbutton(frame, text=option, variable=self.gender_vars[option]).grid(row=i, column=0, sticky='w', padx=(20, 0), pady=(15, 0))
    
    def append_status(self, status_text):
        """Appends the provided text to the top of the status text widget with fading effect."""
        self.status_text.config(state=tk.NORMAL, spacing1=5)  # Temporarily enable editing

        # Insert new message with the darkest color at the beginning
        self.status_text.insert("1.0", status_text + "\n")
        self.status_text.tag_add("color0", "1.0 linestart", "1.0 lineend")
        self.status_text.tag_configure("color0", foreground=self.colors[0])

        # Adjust colors of the subsequent lines to create the fading effect
        for i in range(1, len(self.colors)):
            line_start = f"1.0 + {i} lines linestart"
            line_end = f"1.0 + {i} lines lineend"
            self.status_text.tag_remove(f"color{i-1}", line_start, line_end)
            self.status_text.tag_add(f"color{i}", line_start, line_end)
            self.status_text.tag_configure(f"color{i}", foreground=self.colors[i])

        self.status_text.config(state=tk.DISABLED)
 
    '''
    Upload Dataset
    '''
    def upload_dataset(self):
        file_paths = filedialog.askopenfilenames(filetypes=[
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
        if file_paths:
            self.process_button['text'] = "Loading..."
            self.process_button['state'] = tk.DISABLED

            for file_path in file_paths:
                basename = os.path.basename(file_path)
                
                if basename.endswith('.tar.gz'):
                    ext = '.tar.gz'
                elif basename.endswith('.tar.bz2'):
                    ext = '.tar.bz2'
                else:
                    ext = os.path.splitext(file_path)[-1].lower()
 
                if ext in ['.zip', '.tar', '.tar.gz', '.tar.bz2']:
                    self.append_status(f"{basename.replace(ext, '')}: Starting Extraction")
                    self.extract_archive(file_path, ext)
    
    '''
    EXTRACT ARCHIVES
        Accepts .zip, .tar, .tar.gz, .tar.bz2
    '''
    def extract_archive(self, archive_path, ext):
        self.extract_dir = os.path.join(os.path.dirname(archive_path), "extracted_dir")
        if not os.path.exists(self.extract_dir): os.mkdir(self.extract_dir)
        self.candidates_dir = os.path.join(self.extract_dir, "Candidates")
        if not os.path.exists(self.candidates_dir): os.mkdir(self.candidates_dir)
        
        #ext = os.path.splitext(archive_path)[1]
        if ext == '.gz' or ext == '.bz2':  # Handle tar.gz and tar.bz2
            ext = '.'.join(os.path.basename(archive_path).split('.')[-2:])
        self.start_time = time.time()
        threading.Thread(target=self._threaded_extraction, args=(archive_path, ext), daemon=True).start()

    def _threaded_extraction(self, archive_path, ext):
        base_name = os.path.basename(archive_path).replace(ext, '')
        extract_dir = os.path.join(self.extract_dir, base_name).replace('\\', '/')

        if os.path.exists(extract_dir):
            shutil.rmtree(extract_dir)
            print(f"Deleted existing extract_dir: {extract_dir}")
        os.mkdir(extract_dir)
        if ext == '.zip':
            with zipfile.ZipFile(archive_path, 'r') as archive_ref:
                archive_ref.extractall(extract_dir)
        elif ext in ['.tar', '.tar.gz', '.tar.bz2']:
            with tarfile.open(archive_path) as archive_ref:
                archive_ref.extractall(extract_dir)

        # Move all image files to the root extract directory (flatten the structure)
        image_count = 0  
        # adding comments to explan the following code'
        # os.walk() returns a generator that yields a tuple of (dirpath, dirnames, filenames)

        for dirpath, _, filenames in os.walk(extract_dir):
            for f in filenames:
                if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.tif')):
                    # Modify filename to make it unique based on its original directory
                    subdir_name = os.path.basename(dirpath)
                    
                    unique_filename = f"{subdir_name}_{f}" if subdir_name != base_name else f # to prevent conflits with images with same name

                    destination = os.path.join(extract_dir, unique_filename)
                    if os.path.exists(destination):  # In case even the unique name exists (very rare but just to be safe)
                        unique_filename = f"{image_count}_{f}" 
                        destination = os.path.join(extract_dir, unique_filename)

                    shutil.move(os.path.join(dirpath, f), destination)
                    image_count += 1
             
        self.dataset_image_counts[extract_dir] = image_count
        
        for dirpath, _, _ in os.walk(extract_dir, topdown=False):
            if not os.listdir(dirpath):  # Empty directory
                os.rmdir(dirpath)
            
        entry_text = f"{base_name} \t({image_count})"
        # Add the root extraction directory name to the listbox
        self.dataset_filenames_listbox.insert(tk.END, entry_text)
        
        elapsed_time = time.time() - self.start_time
        minutes, seconds = divmod(elapsed_time, 60)
        if minutes <= 0:
            self.append_status(f"{base_name}: Extracted {image_count} images in {int(seconds)} seconds")
        else:
            self.append_status(f"{base_name}: Extracted {image_count} images in {int(minutes)} minutes {int(seconds)} seconds")
        
        self.append_status(f"{base_name}: Extracted to {extract_dir}")
        self.master.after(0, self._finish_extraction) 

    def _finish_extraction(self):
        self.process_button['text'] = "Process"
        self.process_button['state'] = tk.NORMAL    
        
    '''
    PROCESSING IMAGES
    '''
    def get_available_gpus(self):
        # using tensorflow==2.10.0, CuDNN 8.1.0.77, CUDA 11.2.0
        local_device_protos = device_lib.list_local_devices()
        cpus = tf.config.list_physical_devices('CPU')
        gpus = tf.config.list_physical_devices('GPU')
        return cpus, gpus
        
    def start_processing_images(self):
        self.master.change_view('Gallery')

        self.cancellation_requested = False
        self.processed_images_count = 0
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
        
        cpus, gpus = self.get_available_gpus()
        if gpus:
            try:
                tf.config.experimental.set_memory_growth(gpus[0], True)
            except RuntimeError as e:
                print(e)
            NUM_THREADS = os.cpu_count()
            BATCH_SIZE = 5  
            DEVICE = '/device:CPU:0'
        if cpus and not gpus:
            NUM_THREADS = os.cpu_count() or 4
            BATCH_SIZE = 5
            DEVICE = '/device:CPU:0'
        selected_folders = [folder_path for idx, folder_path in enumerate(self.dataset_image_counts.keys()) if idx in selected_indices]
        # Partition the image file indexes into the number of threads specified
        image_ranges = self._divide_images_by_count(selected_folders, NUM_THREADS)
        threads = []
        for start_idx, end_idx in image_ranges:
            thread = threading.Thread(target=self.process_images, args=(actions, selected_folders, start_idx, end_idx, BATCH_SIZE, DEVICE))
            threads.append(thread)
            thread.start()
    
        def wait_for_threads():
            for thread in threads:
                thread.join()
                
        wait_thread = threading.Thread(target=wait_for_threads)    
        wait_thread.start()
        
    def _divide_images_by_count(self, selected_folders, num_threads):
        """ 
        Partition the image index ranges into the number of threads specified
        """
        total_images = sum(self.dataset_image_counts[folder] for folder in selected_folders)
        self.master.views["Gallery"].set_progress_maximum(total_images)

        # Adjust the number of threads if the dataset is smaller
        num_threads = min(total_images, num_threads)
    
        avg_images_per_thread = total_images // num_threads
        remaining_images = total_images % num_threads  # This will handle the distribution of the remaining images

        current_idx = 0
        ranges = []
        for i in range(num_threads):
            start_idx = current_idx
            end_idx = start_idx + avg_images_per_thread

            if remaining_images > 0:
                end_idx += 1  # Distribute the remaining images
                remaining_images -= 1

            ranges.append((start_idx, end_idx))
            current_idx = end_idx

        return ranges

    
    def _batched_image_paths(self, folder_path, BATCH_SIZE):
        """
        Lazy Loading
        A generator that yields image paths in batches of size BATCH_SIZE
        """
        img_paths = (os.path.join(folder_path, img_file) for img_file in os.listdir(folder_path))
        batch = []
        for img_path in img_paths:
            if self.cancellation_requested:
                self.cancellation_requested = False
                return
            batch.append(img_path)
            if len(batch) == BATCH_SIZE:
                yield batch
                batch = []
        if batch:
            yield batch
    
    
    def process_images(self, actions, selected_folders, start_idx, end_idx, BATCH_SIZE, DEVICE):
        processed_so_far = 0
        base_dir = os.path.dirname(selected_folders[0]) if selected_folders else ""
        candidate_folder = self.candidates_dir
    
        for folder_path in selected_folders:
            for img_path in os.listdir(folder_path):
                if start_idx <= processed_so_far < end_idx:
                    # analyze the images
                    accepted_images_dict = self.neural_network_filter([os.path.join(folder_path, img_path)], actions, DEVICE)
                    for img_path, features in accepted_images_dict.items():
                        if self.cancellation_requested:
                            return
                        candidate_image_path = os.path.join(candidate_folder, os.path.basename(img_path))
                        shutil.copy(img_path, candidate_image_path)
                        self.image_tag_mappings[candidate_image_path] = {'original_path': img_path, 'tags': features}
                        update_data = {
                            'type': 'update_gallery',
                            'folder': candidate_folder,
                            'image_data': {candidate_image_path: self.image_tag_mappings.get(candidate_image_path)}
                        }
                        self.ui_update_queue.put(update_data)
                processed_so_far += 1
                if processed_so_far >= end_idx:
                    break
    '''
    Listeners for UI updates
    '''           
    def listen_for_ui_updates(self):
        try:
            # Non-blocking get from the queue
            update_request = self.ui_update_queue.get_nowait()

            # Dispatch the update request to the processing function
            self.process_ui_update(update_request)
            
        except queue.Empty:
            # If the queue is empty, just pass
            pass
        
        # Schedule the next check in 100ms
        self.master.after(100, self.listen_for_ui_updates)

    def process_ui_update(self, update_request):
        if update_request['type'] == 'update_progress':
            self.master.views['Gallery'].update_progress(update_request['count'])
        elif update_request['type'] == 'update_gallery':
            self.master.views['Gallery'].receive_data(update_request['folder'], update_request['image_data'])

        self.master.views['Gallery'].update_idletasks() 

    def get_custom_emotion(self, deepface_output):
        custom_emotion_scores = {
            "Angry": deepface_output['angry'],
            "Crying": 0.8 * deepface_output['sad'] + 0.2 * deepface_output['neutral'],
            "Sad": deepface_output['sad'],
            "Surprised": deepface_output['surprise'],
            "Confused": 0.5 * deepface_output['neutral'] + 0.3 * deepface_output['fear'] + 0.2 * deepface_output['angry'],
            "Shy": 0.9 * deepface_output['neutral'] + 0.1 * deepface_output['fear'],
            "Neutral": deepface_output['neutral']
        }
        dominant_custom_emotion = max(custom_emotion_scores, key=custom_emotion_scores.get)
        return dominant_custom_emotion
    
    def age_within_selected_range(self, detected_age, selected_age_ranges):
        if "Infants (1 month to 1 year)" in selected_age_ranges and 1 <= detected_age < 12:
            return True
        elif "Children (1 year through 12 years)" in selected_age_ranges and 12 <= detected_age < 13:
            return True
        elif "Teenagers (13 years through 17 years.)" in selected_age_ranges and 13 <= detected_age <= 17:
            return True
        elif "Adults (18 years or older)" in selected_age_ranges and 18 <= detected_age < 65:
            return True
        elif "Older adults (65 and older)" in selected_age_ranges and detected_age >= 65:
            return True
        return False

    # Neural netork source https://github.com/serengil/deepface
    def neural_network_filter(self, image_paths, actions, DEVICE):
        accepted_images = {}
        try:
            for image_path in image_paths:
                with self.gpu_lock:
                    with tf.device(DEVICE):
                        #Deepface
                        analysis = DeepFace.analyze(img_path=image_path, actions=list(actions.keys()), detector_backend='mtcnn', enforce_detection=False)
                print(analysis)
                self.processed_images_count += 1
                update_request = {
                    'type': 'update_progress',
                    'count': self.processed_images_count
                }
                self.ui_update_queue.put(update_request)
               

                # analyze the face data frum deepface
                face_data = analysis[0]
                features = {}
                if actions.get('emotion'):
                    emotion_scores = face_data['emotion']
                    mapped_emotion = self.get_custom_emotion(emotion_scores)
                    features['emotion'] = mapped_emotion.lower()

                if actions.get('gender'):
                    features['gender'] = self.label_mapping.get(face_data['dominant_gender'].lower(), face_data['dominant_gender'].lower())

                if actions.get('race'):
                    features['race'] = face_data['dominant_race'].lower()

                if actions.get('age'):
                    detected_age = face_data['age']
                    age_is_acceptable = self.age_within_selected_range(detected_age, actions.get('age'))
                    if age_is_acceptable:
                        features['age'] = str(detected_age)

                if (
                    (not actions.get('emotion') or features['emotion'] in [emotion.lower() for emotion in actions.get('emotion')]) and
                    (not actions.get('age') or 'age' in features) and
                    (not actions.get('race') or features['race'] in [race.lower() for race in actions.get('race')]) and
                    (not actions.get('gender') or features['gender'] in [gender.lower() for gender in actions.get('gender')])
                ):
                    accepted_images[image_path] = features

            return accepted_images

        except Exception as e:
            print(f"Error analyzing images. Error: {e}")
            return {}




                    

                

