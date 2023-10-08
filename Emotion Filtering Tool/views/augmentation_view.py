import tkinter as tk
from tkinter import ttk
from collections import defaultdict
from PIL import Image, ImageTk

class AugmentationView(ttk.Frame):
    def __init__(self, parent, shared_data, **kwargs):
        super().__init__(parent, **kwargs)
        self.shared_data = shared_data
        self.photo_images = []
        self.selected_images = defaultdict(bool)
        self.image_frames = {}
        self.current_row = 0
        self.current_col = 0
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)
        self.original_images = {} 
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

        self.augment_button = ttk.Button(self, text="Process Selected", command=self.augment_images)
        self.augment_button.grid(row=1, column=0, padx=10, pady=10, sticky="w")
        
        self.export_button = ttk.Button(self, text="Export All", command=self.save_augmented_images)
        self.export_button.grid(row=1, column=1, padx=10, pady=10, sticky="e")

    def on_frame_configure(self, event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(-1*(event.delta//120), "units")

    def save_augmented_images(self):
        self.shared_data['augmented_images'] = self.photo_images
        self.photo_images = []
        self.master.change_view('Dataset Export Options')
            
    def show_images(self, photo_images):
        self.photo_images = photo_images
        self.original_images = {idx: ImageTk.getimage(img) for idx, img in enumerate(self.photo_images)}  # Store original PIL images
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
        augment_window = tk.Toplevel(self)
        augment_window.title("Augmentation")
    
        option_frame = ttk.Frame(augment_window)
        option_frame.grid(row=0, column=0, sticky="nsew")
    
        option_label = ttk.Label(option_frame, text="Add augmentation options here")
        option_label.pack(pady=10)
    
        image_frame = ttk.Frame(augment_window)
        image_frame.grid(row=0, column=1, sticky="nsew")
    
        img_label = ttk.Label(image_frame)
        img_label.pack()
    
        button_frame = ttk.Frame(image_frame)
        button_frame.pack(pady=5)
    
    
        # Label to display "image x of x"
        label_text = tk.StringVar()
        progress_label = ttk.Label(button_frame, textvariable=label_text)
        progress_label.grid(row=0, column=1)
    
        # Add accept and reject buttons
        accept_button = ttk.Button(button_frame, text="Accept", command=lambda: self.accept_augment(img_label, augment_window, label_text))
        accept_button.grid(row=0, column=0)

        reject_button = ttk.Button(button_frame, text="Cancel", command=lambda: self.cancel_augment(img_label, augment_window, label_text))
        reject_button.grid(row=0, column=2)

    
        selected_indices = [idx for idx, selected in self.selected_images.items() if selected]
    
        # Initialize counters and make them instance variables
        self.current_image = 1
        self.total_images = len(selected_indices)
        self.selected_indices_queue = selected_indices
    
        # Update the label text
        label_text.set(f"Image {self.current_image} of {self.total_images}")

        # Show the first image if there is any selected
        if self.selected_indices_queue:
            first_idx = self.selected_indices_queue.pop(0)
            self.show_next_image(first_idx, img_label, augment_window)
            
        
    def accept_augment(self, img_label, augment_window, label_text):
        # Increment the counter for the currently processed image
        self.current_image += 1
        # Update the label text
        label_text.set(f"Image {self.current_image} of {self.total_images}")

        augmented_image_pil = self.original_images[self.current_image - 1]  # Replace with actual augmented image
        augmented_image = ImageTk.PhotoImage(image=augmented_image_pil)

        # Update the photo_images list with the augmented image
        self.photo_images[self.current_image - 1] = augmented_image

        # Update the photo_images list with the augmented image
        self.photo_images[self.current_image - 1] = augmented_image

        # Display the next image if any are left
        if self.selected_indices_queue:
            next_idx = self.selected_indices_queue.pop(0)
            self.show_next_image(next_idx, img_label, augment_window)
        else:
            augment_window.destroy()


    def cancel_augment(self, img_label, augment_window, label_text):
        # Increment the counter for the currently processed image
        self.current_image += 1
        # Update the label text
        label_text.set(f"Image {self.current_image} of {self.total_images}")

        # Restore the original image from the stored dictionary
        original_pil_image = self.original_images[self.current_image - 1]
        original_tk_image = ImageTk.PhotoImage(image=original_pil_image)
        self.photo_images[self.current_image - 1] = original_tk_image

        # Display the next image if any are left
        if self.selected_indices_queue:
            next_idx = self.selected_indices_queue.pop(0)
            self.show_next_image(next_idx, img_label, augment_window)
        else:
            augment_window.destroy()

            
    def show_next_image(self, idx, img_label, augment_window):
        # Display next image and apply augmentation here
        # For demonstration, just displaying the image
        img_label.config(image=self.photo_images[idx])
        img_label.image = self.photo_images[idx]
