import tkinter as tk
from tkinter import ttk
from collections import defaultdict
from PIL import Image, ImageTk
import tkinter.messagebox as messagebox

class AugmentationView(ttk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)
        self.current_row = 0
        self.current_col = 0
        self.current_row_width = 0
        self.photo_images = []
        self.selected_images = defaultdict(bool)
        self.image_frames = {}
        self.changed_images = set()
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
        self.master.views['Dataset Export Options'].receive_images(self.photo_images)
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
        # Calculate the width of the image with padding and checkbutton
        image_width_with_padding = photo.width() + 10 + 20  # 10 for padding and 20 for checkbutton
        
        # Check if adding this image would exceed the max frame width
        if self.current_row_width + image_width_with_padding > self.canvas.winfo_width():
            # Reset for a new row
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
        img_label.grid(row=0, column=1, sticky="ne")
        img_label.bind("<Button-1>", lambda event, idx=idx, var=check_var: self.image_click(idx, var))
        img_label.bind("<MouseWheel>", self._on_mousewheel)
        
        self.selected_images[idx] = False

        # Update current row width and column
        self.current_row_width += image_width_with_padding
        self.current_col += 1
        
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def image_click(self, idx, var):
        # Toggle checkbox state
        var.set(1 - var.get())
        # Update the selection
        self.toggle_selection(idx, var)

    def toggle_selection(self, idx, var):
        self.selected_images[idx] = bool(var.get())          
        
    # Augmentation Window and Functions
    def augment_images(self):
        # Initialize counters and make them instance variables
        self.current_image = 0
        selected_indices = [idx for idx, selected in self.selected_images.items() if selected]
        self.total_images = len(selected_indices)
        self.selected_indices_queue = selected_indices
        
        if self.total_images == 0:
            messagebox.showinfo("No Images Selected", "Please select at least one image to process.")
            return 
        
        augment_window = tk.Toplevel(self)
        augment_window.title("Augmentation")
        
        # Set column weights (relative widths)
        # Set column and row weights for augment_window
        augment_window.grid_columnconfigure(0, weight=1)
        augment_window.grid_columnconfigure(1, weight=3)  # Give image frame more space
        augment_window.grid_rowconfigure(0, weight=1)
    
        option_frame = ttk.Frame(augment_window)
        option_frame.grid(row=0, column=0, sticky="nsew")
    
        # Set column and row weights for option_frame
        option_frame.grid_columnconfigure(0, weight=1)
        option_frame.grid_rowconfigure((0, 1), weight=1)

        option_label = ttk.Label(option_frame, text="Add augmentation options here")
        option_label.grid(row=0, column=0, sticky="n", pady=10)  
    
        change_button = ttk.Button(option_frame, text="Mark as Changed", command=self.mark_as_changed)
        change_button.grid(row=1, column=0, pady=5)  

        image_frame = ttk.Frame(augment_window)
        image_frame.grid(row=0, column=1, sticky="nsew")
    
        # Set column and row weights for image_frame
        image_frame.grid_columnconfigure((0, 1, 2), weight=1)  # Allow all columns to expand
        image_frame.grid_rowconfigure(0, weight=1)  # Allow image row to expand
    
        img_label = ttk.Label(image_frame)
        img_label.grid(row=0, column=1, columnspan=3, sticky="") 


        button_frame = ttk.Frame(image_frame)
        button_frame.grid(row=1, column=1, columnspan=3, sticky="", pady=5)   
    
        # Label to display "image x of x"
        label_text = tk.StringVar()
        progress_label = ttk.Label(button_frame, textvariable=label_text)
        progress_label.grid(row=1, column=1)
        label_text.set(f"Image {self.current_image + 1} of {self.total_images}")

        reject_button = ttk.Button(button_frame, text="Cancel", command=lambda: self.cancel_augment(img_label, augment_window, label_text))
        reject_button.grid(row=1, column=0, padx=(0, 5))
        
        accept_button = ttk.Button(button_frame, text="Accept", command=lambda: self.accept_augment(img_label, augment_window, label_text))
        accept_button.grid(row=1, column=2, padx=5)

        self.reject_button = reject_button
        self.accept_button = accept_button
        
        # Show the first image if there is any selected
        if self.selected_indices_queue:
            first_idx = self.selected_indices_queue.pop(0)
            self.show_next_image(first_idx, img_label, augment_window)
            
        self.update_buttons()
            
    def mark_as_changed(self):
            # Mark the current image as changed
            self.changed_images.add(self.current_image)
            # Update the button texts and states
            self.update_buttons()
            
    def update_buttons(self):
        # No arguments are needed as we saved button references as instance variables
        if self.current_image in self.changed_images:
            self.reject_button['state'] = tk.NORMAL
            self.accept_button['text'] = "Accept"
        else:
            self.reject_button['state'] = tk.DISABLED
            self.accept_button['text'] = "Skip" 
            
    def accept_augment(self, img_label, augment_window, label_text):
        if self.current_image < self.total_images:
            label_text.set(f"Image {self.current_image + 1} of {self.total_images}")

            augmented_image_pil = self.original_images[self.current_image - 1]  # Replace with actual augmented image
            augmented_image = ImageTk.PhotoImage(image=augmented_image_pil)

            # Update the photo_images list with the augmented image
            self.photo_images[self.current_image - 1] = augmented_image

            # Display the next image if any are left
            if self.selected_indices_queue:
                next_idx = self.selected_indices_queue.pop(0)
                self.show_next_image(next_idx, img_label, augment_window)
                self.update_buttons()
            else:
                augment_window.destroy()
        else:
            # No more images to process, destroy the window
            augment_window.destroy()
            

    def cancel_augment(self, img_label, augment_window, label_text):
        # Restore the original image from the stored dictionary
        original_pil_image = self.original_images[self.current_image - 1]
        original_tk_image = ImageTk.PhotoImage(image=original_pil_image)
        self.photo_images[self.current_image - 1] = original_tk_image
        self.changed_images.remove(self.current_image)
        self.update_buttons()

            
    def show_next_image(self, idx, img_label, augment_window):
        # Display next image and apply augmentation here
        # For demonstration, just displaying the image
        self.current_image += 1
        img_label.config(image=self.photo_images[idx])
        img_label.image = self.photo_images[idx]
        
        self.update_buttons()
