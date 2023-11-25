from datetime import datetime
from io import BytesIO
from tkinter import ttk, filedialog
import tkinter as tk
import threading
import uuid
import zipfile
import tarfile
import os
import shutil
import tkinter.messagebox as messagebox
from PIL import Image
from deepface import DeepFace
import queue
import time

import h5py


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
        self.cancellation_event = threading.Event()
        self.pause_event = threading.Event()
        self.ui_update_queue = queue.Queue()   
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

        self.process_button = ttk.Button(self, text="Process", command=self.process_images)
        self.process_button.grid(row=3, column=1, padx=20, pady=20, sticky='se')
        self.process_button['text'] = "no dataset uploaded"
        self.process_button['state'] = tk.DISABLED
        
        self.width_label = ttk.Label(self, text="Width:")
        self.width_label.grid(row=3, column=1, sticky='w', padx=(20, 0), pady=(220, 0))
    
        self.width_entry = ttk.Entry(self, width=5)
        self.width_entry.grid(row=3, column=1, sticky='w', padx=(60, 0), pady=(220, 0))
        self.width_entry.insert(0, "200")  # default width
        self.width_entry.bind("<FocusOut>", self.validate_width_entry)


        # Move the process button slightly to the right to accommodate the new entries
        self.process_button.grid(row=3, column=1, padx=(250, 20), pady=20, sticky='se')
    
    def validate_width_entry(self, event):
        try:
            # Get the current width value from the entry
            user_width = int(self.width_entry.get())
            # Calculate half of the canvas width
            half_canvas_width = self.master.views["Gallery"].canvas.winfo_width() // 2

            # If user's entry is greater than half the canvas width, reset it to half
            if user_width > half_canvas_width:
                self.width_entry.delete(0, tk.END)
                self.width_entry.insert(0, str(half_canvas_width))
        except ValueError:
            # Handle the case where the entry is not an integer
            self.width_entry.delete(0, tk.END)
            self.width_entry.insert(0, "200")
    
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
        self.age_vars = {option: tk.BooleanVar() for option in age_options}
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
        self.gender_vars = {option: tk.BooleanVar() for option in gender_options}
        for i, option in enumerate(gender_options):
            ttk.Checkbutton(frame, text=option, variable=self.gender_vars[option]).grid(row=i, column=0, sticky='w', padx=(20, 0), pady=(15, 0))
    
    def append_status(self, status_text):
        """Appends the provided text to the bottom of the status text widget with a fading effect."""
        self.status_text.config(state=tk.NORMAL)  # Temporarily enable editing

        # Insert new message at the end
        self.status_text.insert(tk.END, status_text + "\n")

        # Update the tags for each existing line to shift the gradient up
        for i in range(len(self.colors) - 1, 0, -1):
            self.status_text.tag_remove(f"color{i}", "1.0", tk.END)
            self.status_text.tag_add(f"color{i}", f"end-{i+1}l linestart", f"end-{i}l lineend")
            self.status_text.tag_configure(f"color{i}", foreground=self.colors[i])

        # Apply the darkest color to the new message
        self.status_text.tag_add("color0", "end-1l linestart", "end-1l lineend")
        self.status_text.tag_configure("color0", foreground=self.colors[0])

        # Apply the lightest color to any lines beyond the number of colors
        total_lines = int(self.status_text.index('end-1c').split('.')[0])
        if total_lines > len(self.colors):
            for i in range(total_lines - len(self.colors)):
                self.status_text.tag_add(f"color{len(self.colors)-1}", f"{i+1}.0 linestart", f"{i+1}.0 lineend")

        # Scroll to the bottom of the text widget
        self.status_text.yview_moveto(1)

        self.status_text.config(state=tk.DISABLED)  # Disable editing again

    '''
    Upload Dataset
    '''
    def upload_dataset(self):
        file_paths = filedialog.askopenfilenames(filetypes=[
            ('All Supported Types', '*.zip *.tar *.tar.gz *.tar.bz2 *.hdf5'),
            ('ZIP files', '*.zip'),
            ('TAR files', '*.tar *.tar.gz *.tar.bz2'),
            ('HDF5 files', '*.hdf5')
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
                    self.extract_archive(file_path, ext)
                elif ext == '.hdf5':
                    self.extract_hdf5(file_path)
    
    '''
    EXTRACT ARCHIVES
        Accepts .zip, .tar, .tar.gz, .tar.bz2, hdf5
        dont think the hdf5 is calculating time to upload, start time should not be self.start_time, should not be class variable, skewing ent time results for multiple parallel uploads
    '''
    def extract_archive(self, archive_path, ext):
        #ext = os.path.splitext(archive_path)[1]
        if ext == '.gz' or ext == '.bz2':  # Handle tar.gz and tar.bz2
            ext = '.'.join(os.path.basename(archive_path).split('.')[-2:])
        self.start_time = time.time()
        threading.Thread(target=self._threaded_archive_extraction, args=(archive_path, ext), daemon=True).start()

    def _threaded_archive_extraction(self, archive_path, ext):
        base_name = os.path.basename(archive_path).replace(ext, '')
        extract_dir = os.path.join(self.master.extracted_images_dir, base_name).replace('\\', '/')

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
        self.master.after(0, self._finish_upload) 

    def extract_hdf5(self, hdf5_path):
        base_name = os.path.basename(hdf5_path).replace('.hdf5', '')
        extract_dir = os.path.join(self.master.extracted_images_dir, base_name).replace('\\', '/')

        if os.path.exists(extract_dir):
            shutil.rmtree(extract_dir)
        os.mkdir(extract_dir)

        with h5py.File(hdf5_path, 'r') as hdf5_file:
            image_count = 0
            for dataset_name in hdf5_file:
                image_data = hdf5_file[dataset_name][...]
                image_path = os.path.join(extract_dir, f"{dataset_name}.png")  # or appropriate format
                Image.fromarray(image_data).save(image_path)
                image_count += 1

        self.dataset_image_counts[extract_dir] = image_count
        entry_text = f"{base_name} \t({image_count})"
        self.dataset_filenames_listbox.insert(tk.END, entry_text)
        self.master.after(0, self._finish_upload) 
        
    def _finish_upload(self):
        self.process_button['text'] = "Process"
        self.process_button['state'] = tk.NORMAL    
        
    '''
    PROCESSING IMAGES
    '''
    def process_images(self):
        while True:
            try:
                self.ui_update_queue.get_nowait()
            except queue.Empty:
                break
        self.processed_images_count = 0
        selected_indices = self.dataset_filenames_listbox.curselection()
        self.cancellation_event.clear()
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
        
        self.master.change_view('Gallery')
        NUM_THREADS = (os.cpu_count() // 2) or 4
      
        selected_folders = [folder_path for idx, folder_path in enumerate(self.dataset_image_counts.keys()) if idx in selected_indices]
        # Partition the image file indexes into the number of threads specified
        image_ranges = self._divide_images_by_count(selected_folders, NUM_THREADS)
        self.threads = []
        for start_idx, end_idx in image_ranges:
            thread = threading.Thread(target=self._threaded_process_images, args=(actions, selected_folders, start_idx, end_idx))
            self.threads.append(thread)
            thread.start()
    
        def wait_for_threads():
            for thread in self.threads:
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
            batch.append(img_path)
            if len(batch) == BATCH_SIZE:
                yield batch
                batch = []
        if batch:
            yield batch
            
    def _threaded_process_images(self, actions, selected_folders, start_idx, end_idx):
        print("started processing")
        processed_so_far = 0
        candidate_folder = self.master.candidates_dir
        for folder_path in selected_folders:
            # Use the lazy loader here
            for batched_img_paths in self._batched_image_paths(folder_path, 10):
                for img_path in batched_img_paths:
                    if self.cancellation_event.is_set():
                        return
                    while self.pause_event.is_set():  # Pauses the processing while the pause event is set
                        time.sleep(0.5)
                    if start_idx <= processed_so_far < end_idx:
                        accepted_images_dict = self.neural_network_filter([img_path], actions)
                        for img_path, features in accepted_images_dict.items():
                            unique_id = uuid.uuid4()
                            unique_path = f"{unique_id}_{os.path.basename(img_path)}"
                            candidate_image_path = os.path.join(candidate_folder, unique_path)
                            shutil.copy(img_path, candidate_image_path)
                            with open(candidate_image_path, 'rb') as f:
                                image_data = f.read()
                                image = Image.open(BytesIO(image_data))
                                # Update the master image dictionary via the MainWindow
                                self.master.add_image_to_master_dict(
                                    candidate_image_path,
                                    features,  # Assuming 'features' contains tags
                                    image,
                                    candidate_folder
                                )
                            update_data = {
                                'type': 'update_gallery',
                                'image_path': candidate_image_path
                            }
                            self.ui_update_queue.put(update_data)
                    processed_so_far += 1
                    if processed_so_far >= end_idx:
                        break

    '''
    Listeners for UI updates
    '''  
    def pause_processing(self):
        self.pause_event.set()

    def resume_processing(self):
        self.pause_event.clear()
        
    def stop_processing(self):
        self.cancellation_event.set() 
        for thread in self.threads:  # Assuming you have a list of threads
            thread.join(timeout=1)  # Join with a timeout
        while True:
            try:
                self.ui_update_queue.get_nowait()
            except queue.Empty:
                break
        
    def listen_for_ui_updates(self):
        if self.cancellation_event.is_set():
            pass
        else:
            try:
                update_request = self.ui_update_queue.get_nowait()
                self.process_ui_update(update_request)
            except queue.Empty:
                pass
        # Schedule the next check in 100ms
        self.master.after(100, self.listen_for_ui_updates)

    def process_ui_update(self, update_request):
        if update_request['type'] == 'update_progress':
            self.master.views['Gallery'].update_progress(update_request['count'])
        elif update_request['type'] == 'update_gallery':
            self.master.views['Gallery'].receive_data(update_request['image_path'])

        self.master.views['Gallery'].update_idletasks() 

    def get_custom_emotion(self, deepface_output):
        # Define a threshold for the dominance of an emotion
        dominance_threshold = 0.1

        # Define the custom emotion scores with adjusted weights
        custom_emotion_scores = {
            "Angry": deepface_output['angry'] + 0.2 * deepface_output['neutral'],
            "Crying": 0.8 * deepface_output['sad'] + 0.1 * deepface_output['neutral'],
            "Sad": deepface_output['sad'],
            "Surprised": deepface_output['surprise'],
            "Confused": 0.3 * deepface_output['neutral'] + 0.4 * deepface_output['fear'] + 0.3 * deepface_output['angry'],
            "Shy": 0.6 * deepface_output['neutral'] + 0.4 * deepface_output['fear'],
            "Neutral": deepface_output['neutral']
        }

        # Normalize the scores
        total_score = sum(custom_emotion_scores.values())
        for emotion in custom_emotion_scores:
            custom_emotion_scores[emotion] /= total_score

        # Sort the emotions by their scores in descending order
        sorted_emotions = sorted(custom_emotion_scores.items(), key=lambda item: item[1], reverse=True)

        # Get the dominant emotion, if it's not 'Neutral', or the second highest otherwise
        if sorted_emotions[0][0] == "Neutral" and len(sorted_emotions) > 1:
            # Check if the neutral score is not dominantly higher than the second
            if sorted_emotions[0][1] - sorted_emotions[1][1] < dominance_threshold:
                dominant_custom_emotion = sorted_emotions[1][0]
            else:
                dominant_custom_emotion = "Neutral"
        else:
            dominant_custom_emotion = sorted_emotions[0][0]

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
    def neural_network_filter(self, image_paths, actions):
        print("filtering images")
        accepted_images = {}
        try:
            for image_path in image_paths:
                if self.cancellation_event.is_set():
                    pass
                else:
                    analysis = DeepFace.analyze(img_path=image_path, actions=list(actions.keys()), detector_backend='mtcnn', enforce_detection=False)
                    #print(analysis)]
                    # future dev note
                    # instead of using DeepFace to process images, attach a chat gpt api to the image and use the chat gpt api to process the image
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




                    

                

