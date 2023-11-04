import tkinter as tk
from tkinter import ttk, Entry, Label
from collections import defaultdict
from turtle import width
from PIL import Image, ImageTk
from io import BytesIO

class ManualReviewView(ttk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.photo_images = {}
        self.accepted_images = {}
        self.accepted_count = 0  # count of accepted images
        self.total_accepted_count = 0  # count of accepted images this session
        self.selected_images = defaultdict(bool)
        self.tag_labels = {}
        self.image_frames = {}
        self.current_row = 0 
        self.current_col = 0
        self.current_row_width = 0 
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)
        self.grid_rowconfigure(2, weight=0)
        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=0) 
        self.create_widgets()

        
    '''
    Initialize UI
    '''
    def create_widgets(self):
        self.canvas = tk.Canvas(self)
        self.canvas.grid(row=0, column=0,columnspan=2, rowspan=2, sticky="nsew")

        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollbar.grid(row=0, column=2, rowspan=2, sticky='nse')

        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.frame_images = ttk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.frame_images, anchor="nw")

        self.frame_images.bind("<Configure>", self.on_frame_configure)
        self.frame_images.bind("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        
        self.accepted_count_label = ttk.Label(self, text=f"Total: {self.accepted_count}")
        self.accepted_count_label.grid(row=2, column=1, padx=215, pady=(0,85), sticky="se")
        
        self.total_accepted_count_label = ttk.Label(self, text=f"Total this Session: {self.total_accepted_count}")
        self.total_accepted_count_label.grid(row=2, column=1, padx=10, pady=(0,85), sticky="se")
        
        self.send_to_augment_button = ttk.Button(self, text="Send Accepted to Augmentation", command=self.send_to_augment)
        self.send_to_augment_button.grid(row=2, column=1, ipadx=20, ipady=20, padx=10, pady=10, sticky="se")
        
        data_upload_view = self.master.views["Data Upload & Image Selection"]
        emotion_options = ['<None>', '<Remove>'] + list(data_upload_view.emotion_vars.keys())
        race_options = ['<None>', '<Remove>'] + list(data_upload_view.race_vars.keys())
        gender_options = ['<None>', '<Remove>'] + list(data_upload_view.gender_vars.keys())
        
        emotion_label = ttk.Label(self, text="Emotion:")
        gender_label = ttk.Label(self, text="Gender:")
        age_label = ttk.Label(self, text="Age:")
        race_label = ttk.Label(self, text="Race:")
        self.emotion_combobox = ttk.Combobox(self, width=10, values=emotion_options)
        self.gender_combobox = ttk.Combobox(self, width=10, values=gender_options)
        self.is_checked = tk.BooleanVar()
        trashcan_image = Image.open("./Resources/Icons/remove.png")
        trashcan_image = trashcan_image.resize((20, 20), Image.LANCZOS)
        self.tk_trashcan_image = ImageTk.PhotoImage(trashcan_image)
        self.age_entry = ttk.Entry(self, width=4, validate="key", validatecommand=(self.register(self.validate_age), '%P'))
        self.age_remove_checkbox = ttk.Checkbutton(self, image=self.tk_trashcan_image, variable=self.is_checked, onvalue=True, offvalue=False)
        self.race_combobox = ttk.Combobox(self, width=10, values=race_options)
        
        emotion_label.grid(row=2, column=0, sticky='w', pady=(10, 10), padx=(150, 0))
        gender_label.grid(row=2, column=0, sticky='w', pady=(80,5), padx=(150, 0))
        age_label.grid(row=2, column=0, sticky='w', pady=(10,5), padx=(5, 0))
        race_label.grid(row=2, column=0, sticky='w', pady=(90,10), padx=(5, 0))

        self.emotion_combobox.grid(row=2, column=0, sticky='w', pady=(10,10), padx=(210, 0))
        self.gender_combobox.grid(row=2, column=0, sticky='w', pady=(80,5), padx=(210, 0))
        self.age_entry.grid(row=2, column=0, sticky='w', pady=(10,5), padx=(40, 0))
        self.age_remove_checkbox.grid(row=2, column=0, sticky='w', pady=(10,5), padx=(90, 0))
        self.race_combobox.grid(row=2, column=0, sticky='w', pady=(90,10), padx=(40, 0))

        self.is_checked.trace('w', self.on_check)
        self.emotion_combobox.set('<None>')
        self.gender_combobox.set('<None>')
        self.race_combobox.set('<None>')
        
        
        # Setting up style for the accept button on hover
        self.accept_button = ttk.Button(self, text="Accept Selected", command=self.accept_images)
        self.accept_button.grid(row=2, column=0, padx=5, pady=10, ipadx=30, ipady=30, sticky="se")
       
        self.reject_button = ttk.Button(self, text="Reject Selected", command=self.reject_images)
        self.reject_button.grid(row=2, column=1, padx=5, pady=10, ipadx=30, ipady=30, sticky="sw")

        update_tags_button = ttk.Button(self, text="Update Tags", command=self.update_tags_for_selected_images)
        update_tags_button.grid(row=2, column=0, padx=(320, 0), pady=(0,35), sticky='sw')
    
    
    def on_frame_configure(self, event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(-1*(event.delta//120), "units")
        
    def on_check(self, *args):
        if self.is_checked.get():
            self.age_entry["state"] = ["disabled"]
        else:
            self.age_entry["state"] = ["normal"]

    def validate_age(self, P):
        if P.isdigit() and 0 <= int(P) <= 100:
            return True
        elif P == "":
            return True
        else:
            return False
        
    def update_tags_for_selected_images(self):
        ordered_paths = list(self.photo_images.keys())
        # Loop over the indices in self.selected_images
        for idx in self.selected_images:
            if self.selected_images[idx]:  # Check if the current image is selected
                # Use the index to get the correct file path
                image_path = ordered_paths[idx]
                image_tags = self.photo_images[image_path]['tags']

                # Update or remove tags based on the selections in the combo boxes
                emotion_selection = self.emotion_combobox.get()
                if emotion_selection == '<Remove>':
                    image_tags.pop('emotion', None)  # Remove the tag if it exists
                elif emotion_selection != '<None>':
                    image_tags['emotion'] = emotion_selection

                # Handle the age tag update or removal
                age_selection = self.age_entry.get()
                if self.is_checked.get():
                    image_tags.pop('age', None)  # Remove the age tag based on the checkbox
                elif age_selection.isdigit() and 0 <= int(age_selection) <= 100:
                    image_tags['age'] = age_selection  # Update the age tag if it's a valid number

                # Handle the race tag update or removal
                race_selection = self.race_combobox.get()
                if race_selection == '<Remove>':
                    image_tags.pop('race', None)
                elif race_selection != '<None>':
                    image_tags['race'] = race_selection

                # Handle the gender tag update or removal
                gender_selection = self.gender_combobox.get()
                if gender_selection == '<Remove>':
                    image_tags.pop('gender', None)
                elif gender_selection != '<None>':
                    image_tags['gender'] = gender_selection

                # Update the photo_images dictionary with the new tags
                self.photo_images[image_path]['tags'] = image_tags

                # Generate the new tag string
                new_tag_string = ', '.join([f"{v.lower()}" for _, v in image_tags.items()])

                # Retrieve the tag label using the image index
                tag_label = self.tag_labels.get(idx)

                # Update the tag label's text if it exists
                if tag_label:
                    tag_label.config(text=new_tag_string)
                self.canvas.update_idletasks()

    '''
    Send data to Augmentation view
    '''
    def send_to_augment(self):
        self.master.views['Image Augmentation'].show_images(self.accepted_images)
        self.master.change_view('Image Augmentation')
        self.accepted_images = {}
        self.accepted_count = 0
        self.total_accepted_count = 0
        self.accepted_count_label.config(text=f"Accepted Images: {self.accepted_count}")
        self.total_accepted_count_label.config(text=f"Accepted Images this Session: {self.total_accepted_count}")
    
    '''
    Clear Images
    '''
    def clear_review(self):
        """Clears all images from the review view."""
        for widget in self.frame_images.winfo_children():
            widget.destroy()

        # Reset attributes
        self.photo_images = {}
        self.accepted_images = {}
        self.selected_images = defaultdict(bool)
        self.image_frames = {}
        self.current_row = 0 
        self.current_col = 0
        self.current_row_width = 0 
    
    '''
    Load and Display Images
    '''
    def load_candidate_images(self, candidate_images):
        self.photo_images.update(candidate_images)
        self.show_images(self.photo_images, False)
    
    def clear_image_grid(self):
        for widget in self.frame_images.winfo_children():
            widget.destroy()

    def show_images(self, images, clear): 
        if clear:
            self.current_col = 0
            self.current_row = 0
            self.current_row_width = 0
            self.clear_image_grid()
        for idx, (image_path, image_data) in enumerate(images.items()):
            photo = image_data['photo']
            tags = image_data['tags']
            self.add_image_to_review(idx, image_path, photo, tags)

        # Update canvas scroll region
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def add_image_to_review(self, idx, image_path, photo, tags):
        image_width_with_padding = photo.width() + 10

        # Check if adding this image would exceed the max frame width
        if self.current_row_width + image_width_with_padding > self.canvas.winfo_width():
            # Reset for new row
            self.current_row_width = 0
            self.current_col = 0
            self.current_row += 1
        
        check_var = tk.IntVar()
        # Image Label
        img_label = ttk.Label(self.frame_images, image=photo)
        img_label.grid(row=self.current_row, column=self.current_col, sticky="nw", padx=5, pady=5)
        img_label.bind("<Button-1>", lambda event, idx=idx, var=check_var: self.image_click(idx, var))
        img_label.bind("<MouseWheel>", self._on_mousewheel)

        # Checkbutton (added to the top-left of the image)
        checkbutton = ttk.Checkbutton(self.frame_images, variable=check_var)
        checkbutton.grid(row=self.current_row, column=self.current_col, sticky="nw", padx=5, pady=5)
        checkbutton['command'] = lambda idx=idx, var=check_var: self.toggle_selection(idx, var)

        # Add tags as a label to the image
        tag_string = ', '.join([f"{v}" for _, v in tags.items()])
        tag_label = ttk.Label(self.frame_images, text=tag_string)
        tag_label.grid(row=self.current_row, column=self.current_col, sticky="ne", padx=5, pady=5)
        tag_label.bind("<MouseWheel>", self._on_mousewheel)
        
        self.tag_labels[idx] = tag_label
        
        # Update current row width and column
        self.current_row_width += image_width_with_padding
        self.current_col += 1

        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    '''
    Image Selection/Acceptance/Rejection logic
    '''
    def image_click(self, idx, var):
        # Toggle checkbox state
        var.set(1 - var.get())
        # Update the selection
        self.toggle_selection(idx, var)

    def toggle_selection(self, idx, var):
        self.selected_images[idx] = bool(var.get())

    def accept_images(self):
        self.process_selected_images(accept=True)

    def reject_images(self):
        self.process_selected_images(accept=False)

    def process_selected_images(self, accept=True):
        new_photo_images = {}
        for idx, image_data in enumerate(self.photo_images.items()):
            image_path, tag_data = image_data

            selected = self.selected_images.get(idx)
            
            if accept and selected:
                self.accepted_images[image_path] = tag_data
                self.accepted_count += 1
                self.total_accepted_count += 1  # Incrementing the total accepted count
            elif not selected:
                new_photo_images[image_path] = tag_data
        
        self.photo_images = new_photo_images  # Set photo_images to only the ones not selected
        self.show_images(self.photo_images, True)  # Refresh the view with remaining images
        self.accepted_count_label.config(text=f"Accepted Images: {self.accepted_count}")
        self.total_accepted_count_label.config(text=f"Accepted Images this Session: {self.total_accepted_count}")
        self.selected_images.clear()


    
        
