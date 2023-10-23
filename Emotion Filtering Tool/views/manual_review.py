import tkinter as tk
from tkinter import ttk
from collections import defaultdict

class ManualReviewView(ttk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.photo_images = []
        self.accepted_images = []  # list to store accepted images
        self.accepted_count = 0  # count of accepted images
        self.selected_images = defaultdict(bool)
        self.image_frames = {}
        self.current_row = 0 
        self.current_col = 0
        self.current_row_width = 0 
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)
        self.grid_rowconfigure(2, weight=0)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0) 
        self.create_widgets()
        self.style = ttk.Style(master)
        self.style.layout('noArrow.TCombobox', 
                          [('Combobox.background', {'children':
                                                    [('Combobox.padding', {'expand': '1',
                                                                           'children':
                                                                           [('Combobox.label', {'side': 'left', 'sticky': ''})]
                                                                          }
                                                     )]
                                                   }
                           )]
                         )
        
    '''
    Initialize UI
    '''
    def create_widgets(self):
        self.canvas = tk.Canvas(self)
        self.canvas.grid(row=0, column=0, sticky="nsew")

        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollbar.grid(row=0, column=1, sticky='nse')

        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.frame_images = ttk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.frame_images, anchor="nw")

        self.frame_images.bind("<Configure>", self.on_frame_configure)
        self.frame_images.bind("<MouseWheel>", self._on_mousewheel)

        self.accept_button = ttk.Button(self, text="Accept Selected", command=self.accept_images)
        self.accept_button.grid(row=1, column=0, padx=10, pady=10, sticky="w")
        
        self.accepted_count_label = ttk.Label(self, text=f"Accepted Images: {self.accepted_count}")
        self.accepted_count_label.grid(row=1, column=0, padx=10, pady=10, sticky="")

        self.reject_button = ttk.Button(self, text="Reject Selected", command=self.reject_images)
        self.reject_button.grid(row=1, column=0, padx=10, pady=10, sticky="e")
        
        self.send_to_augment_button = ttk.Button(self, text="Send Accepted to Augmentation", command=self.send_to_augment)
        self.send_to_augment_button.grid(row=2, column=0, padx=10, pady=10, sticky="")
        
    def on_frame_configure(self, event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def on_frame_configure(self, event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(-1*(event.delta//120), "units")
        
    '''
    Send data to Augmentation view
    '''
    def send_to_augment(self):
        self.master.views['Image Augmentation'].show_images(self.accepted_images)
        self.master.change_view('Image Augmentation')
        self.accepted_images = []
        self.accepted_count = 0
        self.accepted_count_label.config(text=f"Accepted Images: {self.accepted_count}")
    
    '''
    Clear Images
    '''
    def clear_review(self):
        """Clears all images from the review view."""
        for widget in self.frame_images.winfo_children():
            widget.destroy()

        # Reset attributes
        self.photo_images = []
        self.accepted_images = []
        self.selected_images = defaultdict(bool)
        self.image_frames = {}
        self.current_row = 0 
        self.current_col = 0
        self.current_row_width = 0 
    
    '''
    Load and Display Images
    '''
    def show_images(self, new_photo_images):
        # Append new images to existing list
        start_idx = len(self.photo_images)
        self.photo_images.extend(new_photo_images)
    
        # Show new images
        for idx, photo in enumerate(new_photo_images, start=start_idx):
            self.add_image_to_review(idx, photo)

        # Update canvas scroll region
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        
    def add_image_to_review(self, idx, photo):
        image_width_with_padding = photo.width() + 10 + 20 

        # Check if adding this image would exceed the max frame width
        if self.current_row_width + image_width_with_padding > self.canvas.winfo_width():
            # Reset for new row
            self.current_row_width = 0
            self.current_col = 0
            self.current_row += 1

        frame = ttk.Frame(self.frame_images, relief="flat")
        frame.grid(row=self.current_row, column=self.current_col, sticky="nw", padx=5, pady=5)
        self.image_frames[idx] = frame

        
        check_var = tk.IntVar()
        checkbutton = ttk.Checkbutton(frame, variable=check_var)
        checkbutton.grid(row=0, column=0, sticky="nw")
        checkbutton['command'] = lambda idx=idx, var=check_var: self.toggle_selection(idx, var)
        
        img_label = ttk.Label(frame, image=photo)
        img_label.grid(row=1, column=0, columnspan=5, sticky="n")  # span enough columns to cover all comboboxes
        img_label.bind("<Button-1>", lambda event, idx=idx, var=check_var: self.image_click(idx, var))
        img_label.bind("<MouseWheel>", self._on_mousewheel)
        self.selected_images[idx] = False
        
        image_path = list(self.master.views["Gallery"].image_tag_mappings.keys())[0]
        tag_data = self.master.views["Gallery"].image_tag_mappings.get(image_path, {}).get('tags', {})

        
        selected_emotions = [k for k, v in self.master.views['Data Upload & Image Selection'].emotion_vars.items() if v.get()]
        selected_ages = [k for k, v in self.master.views['Data Upload & Image Selection'].age_vars.items() if v.get()]
        selected_races = [k for k, v in self.master.views['Data Upload & Image Selection'].race_vars.items() if v.get()]
        selected_genders = [k for k, v in self.master.views['Data Upload & Image Selection'].gender_vars.items() if v.get()]

        
        col_offset = 2

        def create_and_bind_combobox(feature, selections):
            nonlocal col_offset
            if feature in tag_data and selections:
                current_value = tag_data.get(feature)
                combobox = self.create_combobox(frame, selections, current_value, col_offset)
                combobox.bind("<<ComboboxSelected>>", lambda event, f=feature: self.update_tag(idx, combobox, f))
                col_offset += 1

        # Create comboboxes with width specific to their selections
        create_and_bind_combobox('emotion', selected_emotions)
        create_and_bind_combobox('age', selected_ages)
        create_and_bind_combobox('race', selected_races)
        create_and_bind_combobox('gender', selected_genders)

        # Update current row width and column
        self.current_row_width += image_width_with_padding
        self.current_col += 1
    
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
   
    '''
    Creating/modifying Tag Comboboxes
    '''
    def create_combobox(self, parent_frame, options, default_value, col_offset):
        """Helper function to create a Combobox."""
        max_option_length = max([len(option) for option in options])

        combobox = ttk.Combobox(parent_frame, values=options, width=max_option_length, state="readonly", style="noArrow.TCombobox")
        combobox.set(default_value)
        combobox.grid(row=0, column=col_offset, sticky="ne")

        return combobox

    def update_tag(self, idx, combobox, feature):
        """Update the image tag mappings."""
        if idx in self.master.views["Gallery"].image_tag_mappings:
            self.master.views["Gallery"].image_tag_mappings[idx][feature] = combobox.get()
        else:
            self.master.views["Gallery"].image_tag_mappings[idx] = {feature: combobox.get()}
        new_width = len(combobox.get())
        combobox.config(width=new_width)
    
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
        new_photo_images = []
        for idx, selected in list(self.selected_images.items()):
            if accept and selected:
                self.accepted_images.append(self.photo_images[idx])
                self.accepted_count += 1
            elif not selected:
                new_photo_images.append(self.photo_images[idx])

        self.show_images(new_photo_images)  # Refresh the view with remaining images
        self.accepted_count_label.config(text=f"Accepted Images: {self.accepted_count}")

    
        
