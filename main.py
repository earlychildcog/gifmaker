import os
import subprocess
from tkinter import *
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk, ExifTags

class App:
    def __init__(self, root):
        # preset directory
        self.output_dir = 'gifs'
        self.folder_path = None
        self.img = None
        self.path_thumbnail = 'images/thumbnail.jpg'
        self.path_thumbnail_original = None
        # ffmpeg parameters
        self.slider_brightness_value = 0
        self.frame_rate = '20'
        # main window
        root.title("Image to GIF converter")
        root.geometry('1000x1000')

        # create listbox for subfolders
        self.listbox = Listbox(root)
        self.listbox.pack(side=LEFT, fill=BOTH)

        # populate listbox with subfolders of 'images' in the current directory
        images_dir = os.path.join(os.getcwd(), 'images')
        self.images_dir = images_dir
        if os.path.isdir(images_dir):
            subfolders = [f.path for f in os.scandir(images_dir) if f.is_dir()]
            subfolders.sort()
            for subfolder in subfolders:
                self.listbox.insert(END, os.path.basename(subfolder))

        self.listbox.bind('<Double-Button-1>', self.select_folder)
        # create canvas for image
        self.canvas = Canvas(root, width=800, height=800)
        self.canvas.pack()

        # buttons

        create_button = Button(root, text="Create GIF", command=self.create_gif)
        create_button.pack()

        # sliders
        self.title_slider_brightness = Label(root, text="Adjust Brightness")
        self.title_slider_brightness.pack()

        self.slider_brightness = Scale(root, from_=-100, to=100, resolution=1, orient='horizontal', length=500, command=self.update_brightness)
        self.slider_brightness.pack()

    def update_brightness(self, value):
        self.slider_brightness_value = int(value) / 100  # remember to divide back by 10
        if self.path_thumbnail_original is not None:
            self.load_img(self.path_thumbnail_original)

    def load_img(self, path):
        
        cmd_thumbnail = 'ffmpeg -y -i {}  -i palette.png -filter_complex "scale=720:-1:flags=lanczos,split[s0][s1];[s0]palettegen=max_colors=16[p];[s1][p]paletteuse,eq=brightness={}" -frames:v 1 {}'.format(path,self.slider_brightness_value,self.path_thumbnail)
        try:
            subprocess.run(cmd_thumbnail, shell=True, check=True)
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Error", str(e))
        image = Image.open(self.path_thumbnail)
        try:
            for orientation in ExifTags.TAGS.keys():
                if ExifTags.TAGS[orientation] == 'Orientation':
                    break
            exif = dict(image._getexif().items())

            if exif[orientation] == 3:
                image = image.rotate(180, expand=True)
            elif exif[orientation] == 6:
                image = image.rotate(270, expand=True)
            elif exif[orientation] == 8:
                image = image.rotate(90, expand=True)

        except (AttributeError, KeyError, IndexError):
            # cases: image don't have getexif
            pass
        # image = image.resize((500, 500), Image.Resampling.LANCZOS)  # rescale imagee
        self.img = ImageTk.PhotoImage(image)
        self.canvas.create_image(20, 20, anchor=NW, image=self.img)

    def select_folder(self, event):
        self.folder_path = os.path.join(self.images_dir,self.listbox.get(ACTIVE))
        jpg_files = [f for f in os.listdir(self.folder_path) if f.endswith('.jpg')]

        if not jpg_files:
            messagebox.showerror("Error", "The selected folder does not contain any JPG files.")
        else:
            self.path_thumbnail_original = os.path.join(self.folder_path, jpg_files[0])
            self.load_img(self.path_thumbnail_original)

    def create_gif(self):
        if self.folder_path is None:
            messagebox.showerror("Error", "No folder selected.")
            return

        # cmd = 'ffmpeg -framerate {} -pattern_type glob -i "{}/*.jpg" {}/{}.gif'.format(self.frame_rate, self.folder_path, self.output_dir, self.listbox.get(ACTIVE))
        cmd = 'ffmpeg  -framerate {} -pattern_type glob -i "{}/*.jpg" -i palette.png -filter_complex "scale=720:-1:flags=lanczos,split[s0][s1];[s0]palettegen=max_colors=16[p];[s1][p]paletteuse,eq=brightness=0.05" {}/{}.gif'.format(self.frame_rate, self.folder_path, self.output_dir, self.listbox.get(ACTIVE))
        try:
            subprocess.run(cmd, shell=True, check=True)
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Error", str(e))

# main loop
root = Tk()
app = App(root)
root.mainloop()

