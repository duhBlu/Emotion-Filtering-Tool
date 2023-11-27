import tkinter as tk
from tkinter import ttk
from collections import defaultdict
from PIL import Image, ImageTk
import tkinter.messagebox as mb
import os
import shutil

class ManualReviewView(ttk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.accepted_count = 0
        self.total_accepted_count = 0
        self.selected_images = defaultdict(bool) 
        self.tag_labels = {}
        self.pending_image_paths = []
        self.imageTk_objects = []
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
        
        # yeah i know this is hideous what r u gonna do about it
        data_upload_view = self.master.views["Upload"]
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
        
        accept_image_path = 'Resources/Icons/Accept background.png'
        reject_image_path = 'Resources/Icons/Reject background.png'
        
        accept_image = Image.open(accept_image_path)
        reject_image = Image.open(reject_image_path)

        accept_image_resized = self.resize_image(accept_image, 100, 100)
        reject_image_resized = self.resize_image(reject_image, 100, 100)

        # Create images with overlay and text
        self.accept_image_with_text = ImageTk.PhotoImage(self.add_overlay_and_text(accept_image_resized))
        self.reject_image_with_text = ImageTk.PhotoImage(self.add_overlay_and_text(reject_image_resized))

        # Setting up buttons with the default images (with text)
        self.accept_button = tk.Button(self, image=self.accept_image_with_text, text="Accept", compound="center", bg='#79c77a', borderwidth=0, command=self.accept_images)
        self.accept_button.grid(row=2, column=0, padx=5, pady=10, sticky="se")
        self.accept_button.bind("<Enter>", self.on_enter)
        self.accept_button.bind("<Leave>", self.on_leave)

        self.reject_button = tk.Button(self, image=self.reject_image_with_text, text="Reject", compound="center", bg='#c4455a', borderwidth=0, command=self.reject_images)
        self.reject_button.grid(row=2, column=1, padx=5, pady=10, sticky="sw")
        self.reject_button.bind("<Enter>", self.on_enter)
        self.reject_button.bind("<Leave>", self.on_leave)
        
        update_tags_button = ttk.Button(self, text="Update Tags", command=self.update_tags)
        update_tags_button.grid(row=2, column=0, padx=(320, 0), pady=(0,35), sticky='sw')
    
    def on_enter(self, event):
        if event.widget == self.accept_button:
            event.widget.config(bg='#3eda76')
        elif event.widget == self.reject_button:
            event.widget.config(bg='#db4141')

    def on_leave(self, event):
        if event.widget == self.accept_button:
            event.widget.config(bg='#afc9b8')
        elif event.widget == self.reject_button:
            event.widget.config(bg='#f2c4c2')

    def add_overlay_and_text(self, image):
        # Create an overlay with transparency
        overlay = Image.new('RGBA', image.size, (255, 255, 255, 220))
        return Image.alpha_composite(image.convert('RGBA'), overlay)

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
    
    '''
    Update the tags for the selected images
    '''    
    def update_tags(self):
        selected_image_paths = [path for path, selected in self.selected_images.items() if selected]
        for image_path in selected_image_paths:
            image_data = self.master.master_image_dict.get(image_path, {})
            image_tags = image_data.get('tags', {})

            # Define a dictionary with tag keys and their associated UI components and optional conditions
            ui_elements = {
                'emotion': (self.emotion_combobox.get(), None),
                'age': (self.age_entry.get(), lambda x: x.isdigit() and 0 <= int(x) <= 100),
                'race': (self.race_combobox.get(), None),
                'gender': (self.gender_combobox.get(), None)
            }

            # Update or remove tags based on selections
            for tag_key, (selection, condition) in ui_elements.items():
                if tag_key == 'age' and self.is_checked.get():
                    image_tags.pop(tag_key, None)
                elif selection == '<Remove>':
                    image_tags.pop(tag_key, None)
                elif selection != '<None>' and (condition is None or condition(selection)):
                    image_tags[tag_key] = selection

            if image_data:
                self.master.master_image_dict[image_path]['tags'] = image_tags

            new_tag_string = ', '.join([f"{v.lower()}" for _, v in image_data['tags'].items()])

            tag_label = self.tag_labels.get(image_path)
            if tag_label:
                tag_label.config(text=new_tag_string)

    '''
    Send data to Augmentation view
    '''
    def send_to_augment(self):
        if self.accepted_count == 0:
            mb.showinfo("Information", "No images have been selected for acceptance.")
        else:
            accepted_image_paths = [path for path, data in self.master.master_image_dict.items() 
                                    if data['working_directory'] == self.master.accepted_images_dir]
            self.master.views['Augment'].receive_data(accepted_image_paths)
            self.master.change_view('Augment')
    
            self.accepted_count = 0
            self.accepted_count_label.config(text=f"Total: {self.accepted_count}")
            self.total_accepted_count_label.config(text=f"Total this Session: {self.total_accepted_count}")

    '''
    Clear Images
    '''
    def clear_review(self):
        """Clears all images from the review view."""
        self.clear_image_grid()
        self.selected_images.clear()
        self.current_row = 0 
        self.current_col = 0
        self.current_row_width = 0 
        
    def clear_image_grid(self):
        # clear images and label/checkboxe children
        for widget in self.frame_images.winfo_children():
            widget.destroy()
    
    '''
    Load and Display Images
    '''
    def receive_data(self, image_paths):
        for _, image_path in enumerate(image_paths):
            self.pending_image_paths.append(image_path)
        self.show_images(image_paths, False)
    
    def show_images(self, image_paths, clear): 
        image_width = self.master.views["Upload"].width_entry.get() 
        image_width = int(image_width)
        if clear:
            self.clear_review()
        for image_path in image_paths:
            image_data = self.master.master_image_dict.get(image_path, {})
            photo_object = image_data.get('photo_object')
            tags = image_data.get('tags', {})

            # Resize the image to display width using the photo object
            resized_image = self.resize_image(photo_object, image_width)
            formatted_tags = ", ".join(tags.values()) if tags else ""
            
            self.add_image_to_review(image_path, resized_image, formatted_tags)

        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        
    def resize_image(self, image, image_width, max_height=None):
        original_width, original_height = image.size
        aspect_ratio = original_height / original_width

        # Calculate the new width and height based on the aspect ratio
        new_width = image_width
        new_height = int(image_width * aspect_ratio)

        # If max_height is provided, ensure the new height does not exceed it
        if max_height is not None and new_height > max_height:
            new_height = max_height
            new_width = int(max_height / aspect_ratio)

        # Resize and return the image
        image = image.resize((new_width, new_height), Image.LANCZOS)
        return image
    
    def add_image_to_review(self, image_path, image, tags):
        photo = ImageTk.PhotoImage(image)
        self.imageTk_objects.append(photo)

        image_width_with_padding = photo.width() + 10

        # Check if adding this image would exceed the max frame width
        if self.current_row_width + image_width_with_padding > self.canvas.winfo_width():
            # Reset for new row
            self.current_row_width = 0
            self.current_col = 0
            self.current_row += 1
        
        # Image Label
        img_label = ttk.Label(self.frame_images, image=photo)
        img_label.grid(row=self.current_row, column=self.current_col, sticky="nw", padx=5, pady=5)
        img_label.bind("<MouseWheel>", self._on_mousewheel)

        # Checkbutton (added to the top-left of the image)
        check_var = tk.IntVar()
        checkbutton = ttk.Checkbutton(self.frame_images, variable=check_var)
        checkbutton.grid(row=self.current_row, column=self.current_col, sticky="nw", padx=5, pady=5)
        checkbutton['command'] = lambda idx=image_path, var=check_var: self.toggle_selection(image_path, var)
        img_label.bind("<Button-1>", lambda event, idx=image_path, var=check_var: self.image_click(idx, var))

        # Add tags as a label to the image
        tag_label = ttk.Label(self.frame_images, text=tags)
        tag_label.grid(row=self.current_row, column=self.current_col, sticky="ne", padx=5, pady=5)
        tag_label.bind("<MouseWheel>", self._on_mousewheel)
        
        self.tag_labels[image_path] = tag_label
        self.current_row_width += image_width_with_padding
        self.current_col += 1

        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    '''
    Image Selection/Acceptance/Rejection logic
    '''
    def image_click(self, idx, var):
        var.set(1 - var.get())
        self.toggle_selection(idx, var)

    def toggle_selection(self, idx, var):
        self.selected_images[idx] = bool(var.get())

    def accept_images(self):
        self.process_selected_images(accept=True)

    def reject_images(self):
        self.process_selected_images(accept=False)
        
    # DEV NOTE
    # This method calls show images on all of the pending images, which causes the system to reload, resize, and display all of the unselected images again.
    # We are currently storing a reference to the photo object in this class, so we could just remove the images/labels from the grid and then update their index in the grid. 
    # This is similar to how we are updating the labels/tags on the images. It just updates the actual label reference instead of the whole grid of images
    def process_selected_images(self, accept=True):
        # Iterate over selected image paths
        selected_images_copy = self.selected_images.copy()
        for image_path, selected in selected_images_copy.items():
            if selected:
                image_data = self.master.master_image_dict.get(image_path, {})
                if accept:
                    # Move the image to the accepted images directory
                    dest_path = os.path.join(self.master.accepted_images_dir, os.path.basename(image_path))
                    shutil.copy2(image_path, dest_path)
                    image_data['working_directory'] = self.master.accepted_images_dir
                    self.master.master_image_dict[dest_path] = image_data
                    del self.master.master_image_dict[image_path]
                    os.remove(image_path)

                    self.accepted_count += 1
                    self.total_accepted_count += 1
                else:
                    # Remove the rejected image from the master image dictionary and delete the file
                    del self.master.master_image_dict[image_path]
                    os.remove(image_path)

                # Add this path to the list of paths to remove
                self.pending_image_paths.remove(image_path)
                self.selected_images.pop(image_path)

        # Show only the images that are still pending review
        self.show_images(self.pending_image_paths, True)

        # Update the UI with the counts of accepted images
        self.accepted_count_label.config(text=f"Total: {self.accepted_count}")
        self.total_accepted_count_label.config(text=f"Total this Session: {self.total_accepted_count}")



    
        
