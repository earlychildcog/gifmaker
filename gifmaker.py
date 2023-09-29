import os
import subprocess
from tkinter import *
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk, ExifTags, ImageSequence

class App:
    def __init__(self, root):
        # preset directory
        self.output_dir = 'gifs'
        self.folder_path = None
        self.img = None
        self.image_data = None
        self.path_thumbnail = 'images/thumbnail.jpg'
        self.path_thumbnail_original = None
        # ffmpeg parameters
        self.slider_brightness_value = 0
        self.slider_contrast_value = 1
        self.slider_fps_value = 30
        self.slider_skipframes_value = 0
        # main window
        root.title("Image to GIF converter")
        root.geometry('1600x1000')

        # Create a frame for the listbox and pack it on the left
        self.listbox_frame = Frame(root)
        self.listbox_frame.grid(row=0, column=0)
        self.listbox = Listbox(self.listbox_frame)
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

        # Create a frame for the canvas and pack it in the middle
        self.canvas_frame = Frame(root)
        self.canvas_frame.grid(row=0, column=1)
        self.canvas = Canvas(self.canvas_frame, width=500, height=500)
        self.canvas.pack()

        # Create a frame for the GIF label and pack it on the right
        self.gif_frame = Frame(root)
        self.gif_frame.grid(row=0, column=2)

        # buttons
        self.setting_frame = Frame(root)
        self.setting_frame.grid(row=1, column=1)
        create_button = Button(self.setting_frame, text="Create GIF", command=self.create_gif)
        create_button.pack()

        # sliders: brightness
        self.title_slider_brightness = Label(self.setting_frame, text="Adjust Brightness")
        self.title_slider_brightness.pack()
        self.slider_brightness = Scale(self.setting_frame, from_=-100, to=100, resolution=1, orient='horizontal', length=500, command=self.update_brightness)
        self.slider_brightness.pack()
        # sliders: contrast
        self.title_slider_contrast = Label(self.setting_frame, text="Adjust Contrast")
        self.title_slider_contrast.pack()
        self.slider_contrast = Scale(self.setting_frame, from_=-5, to=6, resolution=0.01, orient='horizontal', length=500, command=self.update_contrast)
        self.slider_contrast.set(self.slider_contrast_value)
        self.slider_contrast.pack()

        # sliders: fps
        self.title_slider_fps = Label(self.setting_frame, text="Adjust FPS")
        self.title_slider_fps.pack()
        self.slider_fps = Scale(self.setting_frame, from_=1, to=100, resolution=1, orient='horizontal', length=500, command=self.update_fps)
        self.slider_fps.set(self.slider_fps_value)
        self.slider_fps.pack()

        # sliders: skip frames
        self.title_slider_skipframes = Label(self.setting_frame, text="Adjust skip frames")
        self.title_slider_skipframes.pack()
        self.slider_skipframes = Scale(self.setting_frame, from_=0, to=10, resolution=1, orient='horizontal', length=500, command=self.update_skipframes)
        self.slider_skipframes.set(self.slider_skipframes_value)
        self.slider_skipframes.pack()

        # skip frames every
    def update_skipframes(self, value):
        self.slider_skipframes_value = int(value)

    def update_brightness(self, value):
        self.slider_brightness_value = int(value) / 100  # remember to divide back by 10
        if self.path_thumbnail_original is not None:
            self.load_img(self.path_thumbnail_original)
    def update_contrast(self, value):
        self.slider_contrast_value = value
        if self.path_thumbnail_original is not None:
            self.load_img(self.path_thumbnail_original)

    def update_fps(self, value):
        self.slider_fps_value = int(value)

    def load_img(self, path):
        
        cmd_thumbnail = 'ffmpeg -y -i {}  -i palette.png -filter_complex "scale=720:-1:flags=lanczos,split[s0][s1];[s0]palettegen=max_colors=128[p];[s1][p]paletteuse,eq=brightness={}:contrast={}" -frames:v 1 {}'.format(path,self.slider_brightness_value,self.slider_contrast_value,self.path_thumbnail)
        
        print(cmd_thumbnail)
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
        width = 500
        height = int((width / image.width) * image.height)
        image = image.resize((width, height), Image.Resampling.LANCZOS)     # rescale image
        self.image_data = image
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
        self.create_gif

    def create_gif(self):
        if self.folder_path is None:
            messagebox.showerror("Error", "No folder selected.")
            return
        gif_path = '{}/{}.gif'.format(self.output_dir, self.listbox.get(ACTIVE))
        fix_ = 0
        if self.slider_skipframes_value == 1:
            fix_ = 1

       # cmd = 'ffmpeg -y -framerate {} -pattern_type glob -i "{}/*.jpg" -i palette.png -filter_complex "scale=720:-1:flags=lanczos,split[s0][s1];[s0]palettegen=max_colors=128[p];[s1][p]paletteuse,eq=brightness={}:contrast={}" {}'.format(self.slider_fps_value, self.folder_path, self.slider_brightness_value, self.slider_contrast_value, gif_path)
       # cmd = 'ffmpeg -y -framerate {} -pattern_type glob -i "{}/*.jpg" -i palette.png -filter_complex "select=\'mod(n,{})\',scale=720:-1:flags=lanczos,split[s0][s1];[s0]palettegen=max_colors=256[p];[s1][p]paletteuse,eq=brightness={}:contrast={}" {}'.format(self.slider_fps_value, self.folder_path, self.slider_skipframes_value, self.slider_brightness_value, self.slider_contrast_value, gif_path)
       # cmd = 'ffmpeg -y -framerate {} -pattern_type glob -i "{}/*.jpg" -vf "select=\'mod(n,{})\',scale=720:-1:flags=lanczos,eq=brightness={}:contrast={},format=gray,palettegen=max_colors=128" -c:v gif {}'.format(self.slider_fps_value, self.folder_path, self.slider_skipframes_value, self.slider_brightness_value, self.slider_contrast_value, gif_path)
        # cmd = 'ffmpeg -y -framerate {} -pattern_type glob -i "{}/*.jpg" -vf "select=\'mod(n,{})\',scale=720:-1:flags=lanczos,eq=brightness={}:contrast={}" -c:v gif {}'.format(self.slider_fps_value, self.folder_path, self.slider_skipframes_value+fix_, self.slider_brightness_value, self.slider_contrast_value, gif_path)
        if self.image_data.width > self.image_data.height:
            cmd = 'ffmpeg -y -framerate {} -pattern_type glob -i "{}/*.jpg" -vf "select=\'mod(n,{})\',scale=720:-1:flags=lanczos,eq=brightness={}:contrast={}" -c:v gif {}'.format(self.slider_fps_value, self.folder_path, self.slider_skipframes_value+fix_, self.slider_brightness_value, self.slider_contrast_value, gif_path)
        else:
            cmd = 'ffmpeg -y -framerate {} -pattern_type glob -i "{}/*.jpg" -vf "select=\'mod(n,{})\',scale=-1:720:flags=lanczos,eq=brightness={}:contrast={}" -c:v gif {}'.format(self.slider_fps_value, self.folder_path, self.slider_skipframes_value+fix_, self.slider_brightness_value, self.slider_contrast_value, gif_path)

        try:
            subprocess.run(cmd, shell=True, check=True)
            print("gif done\n")
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Error", str(e))

        if os.path.exists(gif_path):
            gif = Image.open(gif_path)
            frames = [frame.copy() for frame in ImageSequence.Iterator(gif)]
            self.gif_frames = [ImageTk.PhotoImage(frame.resize((500, 500), Image.Resampling.LANCZOS)) for frame in frames]

            # Create a label to display the animation
            if hasattr(self, 'gif_label'):
                self.gif_label.destroy()
            self.gif_label = Label(self.gif_frame)
            self.gif_label.pack()
            self.gif_frame_num = 0
            # Cancel the previous GIF update
            if hasattr(self, 'gif_update_id'):
                root.after_cancel(self.gif_update_id)
            self.update_gif()

    def update_gif(self):

        # Schedule the next frame update
        self.gif_update_id = root.after(int(1000/self.slider_fps_value), self.update_gif)
        # Update the current frame of the GIF
        self.gif_label.config(image=self.gif_frames[self.gif_frame_num])
        self.gif_frame_num = (self.gif_frame_num + 1) % len(self.gif_frames)
# main loop
root = Tk()
app = App(root)
root.mainloop()

