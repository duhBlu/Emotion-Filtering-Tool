import tkinter as tk
from tkinter import ttk
from collections import defaultdict
from PIL import Image, ImageTk

class AugmentationView(ttk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.photo_images = []
        self.selected_images = defaultdict(bool)
        self.image_frames = {}
        self.current_row = 0
        self.current_col = 0
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)
        self.create_widgets()

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
        self.frame_images.bind("<Button-4>", self._on_mousewheel_up)
        self.frame_images.bind("<Button-5>", self._on_mousewheel_down)

        self.augment_button = ttk.Button(self, text="Process Selected", command=self.augment_images)
        self.augment_button.grid(row=1, column=0, padx=10, pady=10, sticky="w")

    def on_frame_configure(self, event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(-1*(event.delta//120), "units")

    def _on_mousewheel_up(self, event):
        self.canvas.yview_scroll(-1, "units")

    def _on_mousewheel_down(self, event):
        self.canvas.yview_scroll(1, "units")
        
    def show_images(self, photo_images):
        self.photo_images = photo_images
        self.current_row = 0
        self.current_col = 0
        self.selected_images.clear()

        for idx, photo in enumerate(self.photo_images):
            self.add_image_to_augment(idx, photo)

    def add_image_to_augment(self, idx, photo):
        frame = ttk.Frame(self.frame_images, relief="flat")
        frame.grid(row=self.current_row, column=self.current_col, sticky="nw", padx=5, pady=5)
        self.image_frames[idx] = frame

        check_var = tk.IntVar()
        checkbutton = ttk.Checkbutton(frame, variable=check_var)
        checkbutton.grid(row=0, column=0, sticky="nw")
        checkbutton['command'] = lambda idx=idx, var=check_var: self.toggle_selection(idx, var)

        img_label = ttk.Label(frame, image=photo)
        img_label.grid(row=0, column=1, sticky="ne")
        img_label.bind("<Button-1>", lambda event, idx=idx, var=check_var: self.image_click(idx, var))
        img_label.bind("<MouseWheel>", self._on_mousewheel)
        img_label.bind("<Button-4>", self._on_mousewheel_up)
        img_label.bind("<Button-5>", self._on_mousewheel_down)
        
        self.selected_images[idx] = False

        self.current_col += 1
        if self.current_col > 2:
            self.current_col = 0
            self.current_row += 1
        
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def image_click(self, idx, var):
        # Toggle checkbox state
        var.set(1 - var.get())
        # Update the selection
        self.toggle_selection(idx, var)

    def toggle_selection(self, idx, var):
        self.selected_images[idx] = bool(var.get())
        

    def augment_images(self):
        # Create Toplevel to show images one by one
        augment_window = tk.Toplevel(self)
        augment_window.title("Augmentation")
    
        # Frame for augmentation options on the left side
        option_frame = ttk.Frame(augment_window)
        option_frame.grid(row=0, column=0, sticky="nsew")
    
        # Add augmentation options (for demonstration, using a label)
        option_label = ttk.Label(option_frame, text="Add augmentation options here")
        option_label.pack(pady=10)
    
        # Frame for the image and accept/reject buttons in the center
        image_frame = ttk.Frame(augment_window)
        image_frame.grid(row=0, column=1, sticky="nsew")
    
        # Label to display the image
        img_label = ttk.Label(image_frame)
        img_label.pack()
    
        # Frame for accept/reject buttons below the image
        button_frame = ttk.Frame(image_frame)
        button_frame.pack(pady=5)
    
        # StringVar for the label text
        label_text = tk.StringVar()
    
        # Label to display "image x of x"
        progress_label = ttk.Label(button_frame, textvariable=label_text)
        progress_label.grid(row=0, column=1)
    
        # Add accept and reject buttons
        accept_button = ttk.Button(button_frame, text="Accept", command=lambda: self.accept_augment(current_idx, img_label, augment_window, label_text))
        accept_button.grid(row=0, column=0)
    
        reject_button = ttk.Button(button_frame, text="Reject", command=lambda: self.reject_augment(current_idx, img_label, augment_window, label_text))
        reject_button.grid(row=0, column=2)
    
        # Loop through selected images
        selected_indices = [idx for idx, selected in self.selected_images.items() if selected]
    
        # Initialize counters (you'd probably update these in your accept/reject functions)
        current_image = 0
        total_images = len(selected_indices)
    
        # Update the label text
        label_text.set(f"Image {current_image} of {total_images}")
    
        # Add other methods to actually display the images, etc.



        
        def show_next_image(idx):
            nonlocal img_label
            # Display image and apply augmentation here
            # For demonstration, just displaying the image
            img_label.config(image=self.photo_images[idx])
            img_label.image = self.photo_images[idx]
            
        if selected_indices:
            current_idx = selected_indices.pop(0)
            show_next_image(current_idx)
            
    def accept_augment(self, current_idx, img_label, augment_window):
        # Store the augmented image, update view etc.
        # Move to next image
        selected_indices = [idx for idx, selected in self.selected_images.items() if selected]
        if selected_indices:
            current_idx = selected_indices.pop(0)
            self.show_next_image(current_idx, img_label, augment_window)
        else:
            # Close the Toplevel when done
            augment_window.destroy()

        
    def reject_augment(self, current_idx, img_label, augment_window):
        # Skip this image, do not store
        # Move to next image
        selected_indices = [idx for idx, selected in self.selected_images.items() if selected]
        if selected_indices:
            current_idx = selected_indices.pop(0)
            self.show_next_image(current_idx, img_label, augment_window)
        else:
            # Close the Toplevel when done
            augment_window.destroy()
            
    def show_next_image(self, idx, img_label, augment_window):
        # Display next image and apply augmentation here
        # For demonstration, just displaying the image
        img_label.config(image=self.photo_images[idx])
        img_label.image = self.photo_images[idx]
