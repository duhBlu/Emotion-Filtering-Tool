import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
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
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)
        self.grid_rowconfigure(2, weight=0)
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

        self.accept_button = ttk.Button(self, text="Accept Selected", command=self.accept_images)
        self.accept_button.grid(row=1, column=0, padx=10, pady=10, sticky="w")
        
        self.accepted_count_label = ttk.Label(self, text=f"Accepted Images: {self.accepted_count}")
        self.accepted_count_label.grid(row=1, column=0, padx=10, pady=10, sticky="")

        self.reject_button = ttk.Button(self, text="Reject Selected", command=self.reject_images)
        self.reject_button.grid(row=1, column=0, padx=10, pady=10, sticky="e")
        
        self.send_to_augment_button = ttk.Button(self, text="Send Accepted to Augmentation", command=self.send_to_augment)
        self.send_to_augment_button.grid(row=2, column=0, padx=10, pady=10, sticky="")
        
    def send_to_augment(self):
        self.master.views['Image Augmentation'].show_images(self.accepted_images)
        self.master.change_view('Image Augmentation')
        self.accepted_images = []
        self.accepted_count = 0
        self.accepted_count_label.config(text=f"Accepted Images: {self.accepted_count}")

    def on_frame_configure(self, event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

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
            self.add_image_to_review(idx, photo)

    def add_image_to_review(self, idx, photo):
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
                self.image_frames[idx].destroy()  # Remove the frame from the grid
            elif not accept and selected:
                self.image_frames[idx].destroy()  # Remove the frame from the grid
            else:
                new_photo_images.append(self.photo_images[idx])
                
        self.show_images(new_photo_images)
        self.accepted_count_label.config(text=f"Accepted Images: {self.accepted_count}")