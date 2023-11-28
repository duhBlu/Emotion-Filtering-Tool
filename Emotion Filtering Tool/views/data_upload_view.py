import io
import tkinter as tk
from tkinter import ttk, filedialog
import tkinter.messagebox as messagebox
from io import BytesIO
from PIL import Image
from functools import wraps
import sys
import threading
import zipfile
import tarfile
import os
import shutil
import uuid
import queue
import time
import h5py
from deepface import DeepFace


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
        self.threads = []
        self.process_lock = threading.Lock()
        self.dataset_image_counts = {}
        self.cancellation_event = threading.Event()
        self.pause_event = threading.Event()
        self.ui_update_queue = queue.Queue()   
        self.gender_mapping = {
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
        self.create_emotion_tab()
        self.create_age_tab()
        self.create_race_tab()
        self.create_gender_tab()

        # Upload button
        self.upload_button = ttk.Button(self, text="Upload Dataset", command=self.upload_dataset)
        self.upload_button.grid(row=1, column=0, padx=10, pady=(2, 0), sticky='sw')

        # Dataset Filename Listbox
        listbox_font = ('Helvetica', 12)
        self.dataset_filenames_listbox = tk.Listbox(self, selectmode=tk.MULTIPLE, bg=bg2, exportselection=False, font=listbox_font, activestyle='none')
        self.dataset_filenames_listbox.grid(row=2, column=0, padx=10, pady=(2, 10), sticky='nsew')
        self.dataset_filenames_listbox.configure(selectbackground='#3daee9', selectforeground='#F0F0F0')
        
        # Status Text with Scrollbar
        self.status_text = tk.Text(self, height=5, bg=bg3, wrap=tk.WORD, state=tk.DISABLED, bd=0, highlightthickness=0)
        self.status_text.grid(row=3, column=0, padx=10, pady=(2, 15), sticky='nsew')
        self.status_scroll = tk.Scrollbar(self, command=self.status_text.yview)
        self.status_text.config(yscrollcommand=self.status_scroll.set)
        self.status_scroll.grid(row=3, column=0, sticky='nse')

        self.clear_status_button = ttk.Button(self, text="Clear", command=self.clear_status_text)
        self.clear_status_button.grid(row=3, column=0, padx=(0, 30), pady=(0, 15), sticky='se')
        
        # Process Button Setup
        self.process_button = ttk.Button(self, text="No Dataset Uploaded", command=self.process_images, state=tk.DISABLED)
        self.process_button.grid(row=3, column=1, padx=(250, 20), pady=20, sticky='se')
        self.process_button['state'] = tk.DISABLED
        
        self.width_label = ttk.Label(self, text="Width:")
        self.width_label.grid(row=3, column=1, sticky='w', padx=(20, 0), pady=(220, 0))
    
        self.width_entry = ttk.Entry(self, width=5)
        self.width_entry.grid(row=3, column=1, sticky='w', padx=(60, 0), pady=(220, 0))
        self.width_entry.insert(0, "200")  # default width
        self.width_entry.bind("<KeyRelease>", self.on_width_entry_key_release)
        self.width_entry.bind("<FocusIn>", self.on_entry_focus)

    
    '''
    UI helper functions
    '''
    def on_entry_focus(self, event):
        event.widget.select_range(0, tk.END)
        event.widget.icursor(tk.END)
        
    def on_width_entry_key_release(self, event):
        current_text = self.width_entry.get()
        try:
            # Try to convert the text to an integer
            int(current_text)  # If this fails, ValueError will be raised
            self.last_valid_width = current_text  # Update the last valid value
        except ValueError:
            # If conversion fails, revert to the last valid value or default
            self.width_entry.delete(0, tk.END)
            self.width_entry.insert(0, self.last_valid_width if hasattr(self, 'last_valid_width') else "200")
        
    def validate_width_entry(self):
        try:
            user_width = int(self.width_entry.get())
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
    
    def clear_status_text(self):
        self.status_text.config(state=tk.NORMAL)
        self.status_text.delete("1.0", tk.END)
        self.status_text.config(state=tk.DISABLED)

    def append_status(self, status_text):
        """Appends the provided text to the bottom of the status text widget with a fading effect. Just for fun :3 """
        self.status_text.config(state=tk.NORMAL)
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
        self.status_text.config(state=tk.DISABLED)

    '''
    Upload Dataset
    '''
    def upload_dataset(self):
        """ promts the user for a file with images and calls the appropriate extraction function for the file type"""
        file_paths = filedialog.askopenfilenames(filetypes=[
            ('All Supported Types', '*.zip *.tar *.tar.gz *.tar.bz2 *.hdf5'),
            ('ZIP files', '*.zip'),
            ('TAR files', '*.tar *.tar.gz *.tar.bz2'),
            ('HDF5 files', '*.hdf5')
        ])
        if file_paths:
            self.start_time = time.time()
            self.process_button['text'] = "Loading..."
            self.process_button['state'] = tk.DISABLED
            
            for file_path in file_paths:
                self.extract_file(file_path)
    
    '''
    EXTRACT ARCHIVES
        Accepts .zip, .tar, .tar.gz, .tar.bz2, hdf5
        dont think the hdf5 is calculating time to upload, start time should not be self.start_time, should not be class variable, skewing ent time results for multiple parallel uploads
    '''
    def extract_file(self, file_path):
        # Determine the file extension
                basename = os.path.basename(file_path)
                ext = os.path.splitext(basename)[-1].lower()
                if basename.endswith('.tar.gz'):
                    ext = '.tar.gz'
                elif basename.endswith('.tar.bz2'):
                    ext = '.tar.bz2'
        # Call the correct threaded extraction function based on the file extension
                if ext in ['.zip', '.tar', '.tar.gz', '.tar.bz2']:
                    threading.Thread(target=self._threaded_extract_archive, args=(file_path, ext), daemon=True).start()
                elif ext == '.hdf5':
                    threading.Thread(target=self._threaded_extract_hdf5, args=(file_path,), daemon=True).start()
    
    # extracts images from zip.tar files and adds them to the dataset_filenames_listbox
    def _threaded_extract_archive(self, archive_path, ext):
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

        image_count = 0  
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
             
        for dirpath, _, _ in os.walk(extract_dir, topdown=False):
            if not os.listdir(dirpath):  # Empty directory
                os.rmdir(dirpath)
            
        if image_count > 0:
            self.dataset_image_counts[extract_dir] = image_count
            entry_text = f"\n  {base_name} \t({image_count})\n"
            self.dataset_filenames_listbox.insert(tk.END, entry_text)
            self._post_extraction_status(base_name, extract_dir, image_count)
        else:
            self.append_status(f"{base_name}: No images found in the {ext} file.")
        self.master.after(0, self._finish_upload) 

    # extracts images from hdf5 files that can be created in the export options and adds them to the dataset_filenames_listbox
    def _threaded_extract_hdf5(self, hdf5_path):
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

        if image_count > 0:
            self.dataset_image_counts[extract_dir] = image_count
            entry_text = f"\n  {base_name} \t({image_count})\n"
            self.dataset_filenames_listbox.insert(tk.END, entry_text)
            # Add other status messages and finish upload
            self._post_extraction_status(base_name, extract_dir, image_count)
        else:
            self.append_status(f"{base_name}: No images found in the HDF5 file.")   
        
        self.master.after(0, self._finish_upload) 
    
    def _post_extraction_status(self, base_name, extract_dir, image_count):
        elapsed_time = time.time() - self.start_time
        minutes, seconds = divmod(elapsed_time, 60)
        if minutes <= 0:
            self.append_status(f"{base_name}: Extracted {image_count} images in {int(seconds)} seconds")
        else:
            self.append_status(f"{base_name}: Extracted {image_count} images in {int(minutes)} minutes and {int(seconds)} seconds")
        self.append_status(f"{base_name}: Extracted to {extract_dir}")
        self.master.after(0, self._finish_upload) 
        
    def _finish_upload(self):
        self.process_button['text'] = "Process"
        self.process_button['state'] = tk.NORMAL    
        
    '''
    PROCESSING IMAGES
    '''
    def process_images(self):
        # Initialize variables
        self.processed_images_count = 0
        self.cancellation_event.clear()
        selected_indices = self.dataset_filenames_listbox.curselection()
        
        # Collect selected filtering options
        selected_emotions = [k for k, v in self.emotion_vars.items() if v.get()]
        selected_ages = [k for k, v in self.age_vars.items() if v.get()]
        selected_races = [k for k, v in self.race_vars.items() if v.get()]
        selected_genders = [k for k, v in self.gender_vars.items() if v.get()]

        # Check for dataset and filtering option selection
        if not selected_indices:
            messagebox.showinfo("No Datasets Selected", "Please select a dataset to process.")
            return
        elif not (selected_emotions or selected_ages or selected_races or selected_genders):
            messagebox.showinfo("No Filtering Options Selected", "Please select at least one filtering option.")
            return
        
        # Prepare actions based on selected options
        actions = {}
        if selected_emotions: actions['emotion'] = selected_emotions
        if selected_ages: actions['age'] = selected_ages
        if selected_genders: actions['gender'] = selected_genders
        if selected_races: actions['race'] = selected_races
        self.append_status(f"[proc]: Filtering images based on {actions}")

        self.master.change_view('Gallery')
        
        # Gather selected dataset folders
        selected_folders = [folder_path for idx, folder_path in enumerate(self.dataset_image_counts.keys()) if idx in selected_indices]

        # Determine number of threads
        NUM_THREADS = (os.cpu_count() // 2) or 4
        self.append_status(f"[proc]: Number of threads: {NUM_THREADS}")

        # Partition images by thread count for processing
        image_ranges = self._divide_images_by_count(selected_folders, NUM_THREADS)

        # Create and start threads for processing images
        for start_idx, end_idx in image_ranges:
            thread = threading.Thread(target=self._threaded_process_images, args=(actions, selected_folders, start_idx, end_idx))
            self.threads.append(thread)
            thread.start()

        #start the queue listener
        self.listen_for_ui_updates(thread_check=True)
        
        # Function to wait for all threads to complete
        def wait_for_threads():
            for thread in self.threads:
                thread.join()
            # Stop the listener after threads are done
            self.listen_for_ui_updates(thread_check=False)

        # Start a thread to wait for all processing threads
        wait_thread = threading.Thread(target=wait_for_threads)    
        wait_thread.start()

    # partition images by thread count
    def _divide_images_by_count(self, selected_folders, num_threads):
        """ 
        Partition the image index ranges into the number of threads specified.
        """
        # Calculate total images and set progress bar maximum
        total_images = sum(self.dataset_image_counts[folder] for folder in selected_folders)
        self.master.views["Gallery"].set_progress_maximum(total_images)

        # Adjust number of threads based on total images
        num_threads = min(total_images, num_threads)

        # Determine distribution of images across threads
        avg_images_per_thread = total_images // num_threads
        remaining_images = total_images % num_threads
        self.append_status(f"[proc]: Images per-thread: {avg_images_per_thread}")
        # Partition images into ranges for each thread
        current_idx = 0
        ranges = []
        for _ in range(num_threads):
            start_idx = current_idx
            end_idx = start_idx + avg_images_per_thread + (1 if remaining_images > 0 else 0)
            remaining_images -= 1 if remaining_images > 0 else 0
            ranges.append((start_idx, end_idx))
            current_idx = end_idx

        return ranges

    # yield batches of image paths within the specified index range
    def _batched_image_paths(self, folder_path, start_idx, end_idx):
        """ Yield batches of image paths within the specified index range. """
        BATCH_SIZE = min(10, end_idx - start_idx)
        img_paths = [os.path.join(folder_path, img_file) for img_file in os.listdir(folder_path)]
        for i in range(start_idx, end_idx, BATCH_SIZE):
            batch_end_idx = min(i + BATCH_SIZE, end_idx)
            self.append_status(f"[proc]: Yielding Batch: [{i}-{batch_end_idx}]")
            yield img_paths[i:batch_end_idx]
       
    '''What is this function doing?
    1. Each thread iterates through it's assigned selected_folders
    2. For each folder, it generates batches of image paths using _batched_image_paths
       which yields a subset of the paths based on the thread's assigned range.
    3. Each image path is procesed in a loop, and for each image path
       the neural_network_filter function is called with the current image and the selected actions (filters). 
       This function returns a dictionary of images that were accepted by the neural network filter along with their features.
    '''
    def _threaded_process_images(self, actions, selected_folders, start_idx, end_idx):
        self.append_status(f"[proc]: Processing range: [{start_idx}-{end_idx}]")
        candidate_folder = self.master.candidates_dir
        for folder_path in selected_folders:
            for batched_img_paths in self._batched_image_paths(folder_path, start_idx, end_idx):
                for img_path in batched_img_paths:
                    # Check for cancellation or pause events
                    if self.cancellation_event.is_set():
                        return
                    while self.pause_event.is_set():
                        time.sleep(0.5)
                    
                    accepted_images_dict = self.neural_network_filter([img_path], actions)
                    accepted_images_dict_copy = accepted_images_dict.copy()
                    # if images are accepted by the neural network, process the candidate images
                    for img_path, features in accepted_images_dict_copy.items():
                        unique_id = uuid.uuid4() # to avoid duplicate names
                        unique_path = f"{unique_id}_{os.path.basename(img_path)}"
                        candidate_image_path = os.path.join(candidate_folder, unique_path)
                        shutil.copy(img_path, candidate_image_path)
                            
                        # Read and update image information
                        with open(candidate_image_path, 'rb') as f:
                            image_data = f.read()
                            image = Image.open(BytesIO(image_data))
                        
                        update_data = {'type': 'update_gallery','image_path': candidate_image_path}
                            
                        # Update UI with new image
                    with self.process_lock:
                        self.master.add_image_to_master_dict(candidate_image_path, features, image, candidate_folder)
                        self.ui_update_queue.put(update_data)

    '''
    Listeners for UI updates
    '''  
    def pause_processing(self):
        self.append_status("Pausing processing...")
        self.pause_event.set()

    def resume_processing(self):
        self.append_status("Resuming processing...")
        self.pause_event.clear()
        
    def stop_processing(self):
        # kill all threads and clear the queue
        start_time = time.time()
        self.cancellation_event.set() 
        # join all threads and clear the queue
        for thread in self.threads:
            thread.join(timeout=1)
        while True:
            try:
                self.ui_update_queue.get_nowait()
            except queue.Empty:
                break
        elapsed_time = time.time() - start_time
        _, seconds = divmod(elapsed_time, 60)
        self.append_status(f"Stopped processing in {int(seconds)} seconds")
        
    # Callback system for checking the queue for UI updates
    # since tkinter objects are not thread safe
    def listen_for_ui_updates(self, thread_check=False):
        # Check if any threads are still alive or if the update queue still has items
        if thread_check and (any(thread.is_alive() for thread in self.threads) or not self.ui_update_queue.empty()):
            try:
                update_request = self.ui_update_queue.get_nowait()
                self.process_ui_update(update_request)
            except queue.Empty:
                pass
            # Schedule the next check in 100ms
            self.master.after(100, lambda: self.listen_for_ui_updates(thread_check=True))
        else:
            # Check and process any remaining items in the queue
            while not self.ui_update_queue.empty():
                try:
                    update_request = self.ui_update_queue.get_nowait()
                    self.process_ui_update(update_request)
                except queue.Empty:
                    break
            # Do not reschedule, effectively stopping the listener
            return


    def process_ui_update(self, update_request):
        match update_request['type']:
            case 'update_progress':
                self.master.views['Gallery'].update_progress(update_request['count'])
            case 'update_gallery':
                self.master.views['Gallery'].receive_data(update_request['image_path'])
            case _:
                print("Unknown update request type")

        self.master.views['Gallery'].update_idletasks() 

    def get_custom_emotion(self, deepface_output):
        # Define a threshold for the dominance of an emotion
        dominance_threshold = 0.1

        # Define the custom emotion scores with adjusted weights. I am guessing adjusted weights based on intuition here.
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

    def capture_output(func):
        """Wrapper to capture print output."""

        @wraps(func)
        def wrapper(*args, **kwargs):
            old_stdout = sys.stdout
            new_stdout = io.StringIO()
            sys.stdout = new_stdout
            try:
                return func(*args, **kwargs)
            finally:
                sys.stdout = old_stdout

        return wrapper
    
    # Neural netork source https://github.com/serengil/deepface
    @capture_output
    def neural_network_filter(self, image_paths, actions):
        self.temp_accepted_images = {}
        # Preparing action sets for filtering criteria
        action_sets = {key: set(value.lower() for value in actions[key]) for key in actions if actions[key]}
        try:
            for image_path in image_paths:
                analysis = DeepFace.analyze(img_path=image_path, actions=list(actions.keys()), detector_backend='mtcnn', enforce_detection=False)
                self.processed_images_count += 1
                self.ui_update_queue.put({'type': 'update_progress', 'count': self.processed_images_count})
                face_data = analysis
                features = {}

                # Process and check each feature if applicable
                if 'emotion' in actions:
                    emotion = self.get_custom_emotion(face_data['emotion']).lower() 
                    if emotion in action_sets.get('emotion', {emotion}):
                        features['emotion'] = emotion

                if 'gender' in actions:
                    gender = self.gender_mapping.get(face_data['dominant_gender'].lower(), face_data['dominant_gender'].lower() )
                    if gender in action_sets.get('gender', {gender}):
                        features['gender'] = gender

                if 'race' in actions:
                    race = face_data['dominant_race'].lower()
                    if race in action_sets.get('race', {race}):
                        features['race'] = race

                if 'age' in actions and self.age_within_selected_range(face_data['age'], actions.get('age')):
                    features['age'] = str(face_data['age'])

                # Add image to accepted if it meets all selected criteria
                if all(feature in features for feature in actions):
                    self.temp_accepted_images[image_path] = features

        except Exception as e:
            self.append_status(f"Error analyzing images. Error: {e}")
            print(f"Error analyzing images. Error: {e}")

        return self.temp_accepted_images




                    

                

