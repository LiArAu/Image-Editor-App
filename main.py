from tkinter import ttk, Tk, PhotoImage, RIDGE, GROOVE, ROUND, Canvas, filedialog, Scale, HORIZONTAL
import cv2
import numpy as np
from PIL import Image, ImageTk
from scipy.interpolate import UnivariateSpline

class Editor:
    def __init__(self,master):
        # Set up window size and title
        self.master = master
        self.master.geometry('1500x1260+250+10')
        self.master.title('Quick Edit')

        # Add Header: Logo and Slogan
        self.frame_header = ttk.Frame(self.master)
        self.frame_header.pack()
        self.logo = PhotoImage(file = 'images/mylogo.png').subsample(5,5)
        mylabel = ttk.Label(self.frame_header,image = self.logo).grid(row=0,column=0)
        ttk.Label(self.frame_header,text = 'Transform the way you like.').grid(row=0,column=1)

        # Create the main Frame
        self.frame_main = ttk.Frame(self.master)
        self.frame_main.pack()
        self.frame_main.config(relief=RIDGE,padding = (50,15))

        # Create action buttons on the left of the main frame
        buttons = ['Upload','Crop','Adjust','Filters','Add Sticker','Save As']
        functions = {'Upload':self.upload,'Crop':self.crop,'Adjust':self.adjust,
        'Filters':self.filter,'Add Sticker':self.sticker,'Save As':self.save}
        for i,b in enumerate(buttons):
            ttk.Button(self.frame_main, text = b, command = functions[b]).grid(row=i+1,column=1,padx=5,pady=5,sticky='sw')

        # Create a canvas in the middle of the main frame
        self.canvas = Canvas(self.frame_main,bg = 'white',width = 600, height = 800)
        self.canvas.grid(row=1,column=2,rowspan=10,columnspan=3) # if rowspan = 8, gap btw buttons will increase to fit. canvas size won't change.

        # Create edit action buttons at the bottom of the main frame, below the canvas
        edit_buttons = ['Apply','Cancel','Revert All Changes']
        edit_functions = {'Apply':self.apply,'Cancel':self.cancel,'Revert All Changes':self.revert}
        for j,b in enumerate(edit_buttons):
            ttk.Button(self.frame_main, text = b, command = edit_functions[b]).grid(row=11,column=j+2)


# -------------------------------------- Helpers ---------------------------------------

    # refresh_side_frame() is a function for reconstructing a blank inner frame,
    # which contains sub options or instructions;
    # also unbind the action on canvas.
    def refresh_side_frame(self):
        try:
            self.frame_second.grid_forget()
        except:
            pass

        self.canvas.unbind("<ButtonPress>")
        self.canvas.unbind("<B1-Motion>")
        self.canvas.unbind("<ButtonRelease>")
        self.frame_second = ttk.Frame(self.frame_main)
        self.frame_second.grid(row=0,column=5,rowspan=10)
        self.frame_second.config(relief = GROOVE,padding = (30,15))

    # display_image() is a function to display the image after each processing (whenever you want it).
    # This step also helps resize the image if it is larger than our canvas.
    def display_image(self, image = None):
        # Delete the canvas (also image on it)
        self.canvas.delete('all')

        # If None, print the previous edited image.
        # Else, use the new input image.
        if image is None:
            image = self.edited_image.copy()
        else:
            image = image

        # Convert back to RGB color
        image = cv2.cvtColor(image,cv2.COLOR_BGR2RGB)

        # Calculate the acceptable size if out of limitation.
        height,width,channels = image.shape
        hw_ratio = height/width
        prev_height = height
        if height > 800 or width > 600:
            if hw_ratio<1:
                width = 600
                height = int(600*hw_ratio)
            else:
                height = 800
                width = int(800/hw_ratio)
        # self.ratio will be used later in cropping and adding sticker
        self.ratio = prev_height/height

        # Resize the image and transfer to a canvas friendly format.
        self.new_image = cv2.resize(image,(width,height))
        self.new_image = ImageTk.PhotoImage(Image.fromarray(self.new_image))

        # Resize the canvas and add image on it
        self.canvas.config(width = width,height = height)
        self.canvas.create_image(width/2,height/2,image = self.new_image)


# -------------------------------------- FrontEnd Button Functions --------------------------------------

    # Upload a new image and save in three different names.
    def upload(self):
        self.canvas.delete('all')
        self.filename = filedialog.askopenfilename()
        # imread will lead to GBR color
        # Save the original copy
        self.original_image = cv2.imread(self.filename)
        # The edited image will change when users confirm to apply
        self.edited_image = cv2.imread(self.filename)
        # The filtered image will change when users want to have a look at the effect before applying it.
        self.filtered_image = cv2.imread(self.filename)
        self.refresh_side_frame()
        ttk.Label(self.frame_second,text='Start working on your new photo!').grid(row=0,column=4)
        self.display_image(self.filtered_image)

    # Set up crop action, relate mouse movements with backend functions.
    def crop(self):
        self.rectangle_id = 0
        self.refresh_side_frame()
        ttk.Label(self.frame_second,text='Please click and drag.').grid(row=0,column=0)
        self.display_image(self.edited_image)
        self.canvas.bind("<ButtonPress>",self.start_crop)
        self.canvas.bind("<B1-Motion>",self.during_crop)
        self.canvas.bind("<ButtonRelease>",self.end_crop)

    # Set up adjust function, relate sliders with backend functions, display option of adjusting with sliders in the inner frame.
    def adjust(self):
        self.refresh_side_frame()
        ttk.Label(self.frame_second, text = 'Smooth').grid(row=0,column=0,sticky='sw')
        self.average_slider = Scale(self.frame_second,from_=0,to_=100,orient = HORIZONTAL, command = self.average_action)
        self.average_slider.grid(row=0, column=2, padx=5, sticky='sw')
        self.average_slider.set(0)

        ttk.Label(self.frame_second, text = 'Brightness').grid(row = 1,column=0,sticky='sw')
        self.bright_slider = Scale(self.frame_second,from_=0.5,to_=2,resolution=0.1,orient=HORIZONTAL,command=self.bright_action)
        self.bright_slider.grid(row=1,column=2,padx=5,sticky='sw')
        self.bright_slider.set(1)

        ttk.Label(self.frame_second, text = 'Contrast').grid(row = 2,column=0,sticky='sw')
        self.contrast_slider = Scale(self.frame_second,from_=-100,to_=100,resolution=0.1,orient=HORIZONTAL,command=self.contrast_action)
        self.contrast_slider.grid(row=2,column=2,padx=5,sticky='sw')
        self.contrast_slider.set(0)

        ttk.Label(self.frame_second,text='Don\'t forget to apply your changes!').grid(row=3,column=1,pady=20,sticky='sw')

    # Set up filter function, relate buttons with different chioces of filters, display buttons in the inner frame.
    def filter(self):
        self.refresh_side_frame()
        self.display_image(self.edited_image)
        buttons = ['Natural','Sunshine','Modern','Chill','B&W','Vintage Film','Pencil Sketch']
        functions = {'Natural':self.natural,'Sunshine':self.sunshine,'Modern':self.modern,
        'Chill':self.chill,'B&W':self.bw,'Vintage Film':self.film,'Pencil Sketch':self.paint}
        for i in range(len(buttons)):
            ttk.Button(self.frame_second, text = buttons[i], command = functions[buttons[i]]).grid(row=i,column=1,padx=5,pady=5,sticky='sw')

    # Set up sticker function, take a new sticker image and resize the sticker smaller, related the mouse movement with backend put_sticker function.
    def sticker(self):
        self.refresh_side_frame()
        ttk.Label(self.frame_second,text='Please click where you want to put the sticker.').grid(row=0,column=0)
        self.display_image(self.edited_image)
        self.stickername = filedialog.askopenfilename()
        # imread will lead to GBR color
        image = cv2.imread(self.stickername)
        height,width,channels = image.shape
        hw_ratio = height/width
        max_height,max_width,_ = self.edited_image.shape
        if hw_ratio>1:
            new_height, new_width = int(max_height*0.2), int(max_height*0.2/hw_ratio)
        else:
            new_height, new_width = int(max_width*0.2*hw_ratio), int(max_width*0.2)

        self.new_sticker = cv2.resize(image,(new_width,new_height))
        self.canvas.bind("<ButtonPress>", self.put_sticker)

    # Save the edited image to local computer, with original file type.
    def save(self):
        original_file_type = self.filename.split('.')[-1]
        filename = filedialog.asksaveasfilename()
        filename = filename + "." + original_file_type
        save_as_image = self.edited_image
        cv2.imwrite(filename, save_as_image)
        self.filename = filename
        self.refresh_side_frame()
        ttk.Label(self.frame_second, text = 'Congrats! You have successfully saved your photo.').grid(row=0,column=4)

    # Apply the changes so far.
    def apply(self):
        self.edited_image = self.filtered_image
        self.display_image(self.edited_image)

    # Go back to the most recent version.
    def cancel(self):
        self.display_image(self.edited_image)

    # Revert to the original copy.
    def revert(self):
        self.edited_image = self.original_image.copy()
        self.display_image(self.edited_image)

# -------------------------------------- BackEnd Crop, Add sticker and Adjust --------------------------------------

    # Save position of the start point
    def start_crop(self,event):
        self.crop_start_x, self.crop_start_y = event.x,event.y
    # Save position and create a rectangle as the user's mouse moves.
    def during_crop(self,event):
        if self.rectangle_id:
            self.canvas.delete(self.rectangle_id)
        self.crop_end_x, self.crop_end_y = event.x, event.y
        self.rectangle_id = self.canvas.create_rectangle(self.crop_start_x, self.crop_start_y, self.crop_end_x, self.crop_end_y, width=1)
    # Use the start and final end points to crop the image.
    def end_crop(self,event):
        self.crop_end_x, self.crop_end_y = event.x, event.y
        # Use self.ratio to resize the start and end position.
        start_x = int(self.crop_start_x*self.ratio)
        end_x = int(self.crop_end_x*self.ratio)
        start_y = int(self.crop_start_y*self.ratio)
        end_y = int(self.crop_end_y*self.ratio)
        # Make 'end point' always larger than 'start point' because of slice() later.
        if start_x>end_x:
            start_x, end_x = end_x, start_x
        if start_y>end_y:
            start_y, end_y = end_y, start_y
        x = slice(start_x, end_x,1)
        y = slice(start_y, end_y,1)
        # Update the filtered_image and display.
        self.filtered_image = self.edited_image[y,x]
        self.display_image(self.filtered_image)
        ttk.Label(self.frame_second,text='Don\'t forget to apply your changes!').grid(row=1,column=0)

    # Put the sticker where the user wants, but need to deal with the situation when the sticker is at the boundary of the image.
    def put_sticker(self,event):
        height,width,_ = self.new_sticker.shape
        max_height,max_width,_ = self.edited_image.shape
        self.filtered_image = self.edited_image.copy()
        self.put_start_x, self.put_start_y = int(event.x*self.ratio),int(event.y*self.ratio)
        if self.put_start_x+width<=max_width and self.put_start_y+height<=max_height:
            self.filtered_image[self.put_start_y:(self.put_start_y+height),self.put_start_x:(self.put_start_x+width),:] = self.new_sticker
        elif self.put_start_x+width>max_width and self.put_start_y+height<=max_height:
            self.filtered_image[self.put_start_y:(self.put_start_y+height),self.put_start_x:max_width,:] = self.new_sticker[:,:(max_width-self.put_start_x),:]
        elif self.put_start_x+width<=max_width and self.put_start_y+height>max_height:
            self.filtered_image[self.put_start_y:max_height,self.put_start_x:(self.put_start_x+width),:] = self.new_sticker[:(max_height-self.put_start_y),:,:]
        else:
            self.filtered_image[self.put_start_y:max_height,self.put_start_x:max_width,:] = self.new_sticker[:max_height-self.put_start_y,:max_width-self.put_start_x,:]
        self.display_image(self.filtered_image)
        ttk.Label(self.frame_second,text='Don\'t forget to apply your changes!').grid(row=1,column=0)

    # Smooth
    def average_action(self,value):
        value = int(value)
        if value % 2 == 0:
            value += 1
        self.filtered_image = cv2.blur(self.edited_image,(value,value))
        self.display_image(self.filtered_image)

    # Brightness
    def bright_action(self,value):
        self.filtered_image = cv2.convertScaleAbs(self.edited_image,alpha=self.bright_slider.get())
        self.display_image(self.filtered_image)

    # Contrast
    def contrast_action(self,value):
        self.filtered_image = cv2.convertScaleAbs(self.edited_image,alpha=1,beta=-self.contrast_slider.get())
        self.display_image(self.filtered_image)

# -------------------------------------- BackEnd Filter Chioces --------------------------------------
    # A function to help create lookup tables
    def _create_LUT_8UC1(self,x, y):
        spl = UnivariateSpline(x, y)
        return spl(range(256))

    # Create filter making image cooler
    def cooler(self, img_rgb):
        # Create lookup tables for increasing and decreaing tone
        self.incr_ch_lut = self._create_LUT_8UC1([0, 64, 128, 192, 256],[0, 68, 132, 200, 256])
        self.decr_ch_lut = self._create_LUT_8UC1([0, 64, 128, 192, 256],[0, 40,  100, 150, 200])
        c_r, c_g, c_b = cv2.split(img_rgb)
        c_r = cv2.LUT(c_r, self.incr_ch_lut).astype(np.uint8)
        c_b = cv2.LUT(c_b, self.decr_ch_lut).astype(np.uint8)
        img_rgb = cv2.merge((c_r, c_g, c_b))
        c_h, c_s, c_v = cv2.split(cv2.cvtColor(img_rgb, cv2.COLOR_RGB2HSV))
        c_s = cv2.LUT(c_s, self.incr_ch_lut).astype(np.uint8)
        return cv2.cvtColor(cv2.merge((c_h, c_s, c_v)), cv2.COLOR_HSV2RGB)

    # Create filter making image warmer
    def warmer(self, img_rgb):
        # Create lookup tables for increasing and decreaing tone
        self.incr_ch_lut = self._create_LUT_8UC1([0, 64, 128, 192, 256],[0, 68, 132, 200, 256])
        self.decr_ch_lut = self._create_LUT_8UC1([0, 64, 128, 192, 256],[0, 40,  100, 150, 200])
        c_r, c_g, c_b = cv2.split(img_rgb)
        c_r = cv2.LUT(c_r, self.decr_ch_lut).astype(np.uint8)
        c_b = cv2.LUT(c_b, self.incr_ch_lut).astype(np.uint8)
        img_rgb = cv2.merge((c_r, c_g, c_b))
        c_h, c_s, c_v = cv2.split(cv2.cvtColor(img_rgb, cv2.COLOR_RGB2HSV))
        c_s = cv2.LUT(c_s, self.decr_ch_lut).astype(np.uint8)
        return cv2.cvtColor(cv2.merge((c_h, c_s, c_v)), cv2.COLOR_HSV2RGB)

    # Create filter making image looks better and natural
    def natural(self):
        #self.filtered_image = cv2.bitwise_not(self.edited_image)
        self.filtered_image = cv2.convertScaleAbs(self.edited_image,alpha=1.2,beta=10)
        self.filtered_image = cv2.blur(self.filtered_image,(3,3))
        kernel = np.ones((3, 3), np.uint8)
        self.filtered_image = cv2.erode(self.filtered_image, kernel, iterations=1)
        self.display_image(self.filtered_image)
        ttk.Label(self.frame_second,text='Don\'t forget to apply your changes!').grid(row=7,column=1, sticky = 'sw')

    # Create filter making image much brighter
    def sunshine(self):
        #self.filtered_image = cv2.stylization(self.edited_image, sigma_s=150, sigma_r=0.25)
        self.filtered_image = cv2.convertScaleAbs(self.edited_image,alpha=1.5,beta=10)
        self.display_image(self.filtered_image)
        ttk.Label(self.frame_second,text='Don\'t forget to apply your changes!').grid(row=7,column=1, sticky = 'sw')

    # Create filter making image looks like modern art
    def modern(self):
        ret, self.filtered_image = cv2.threshold(self.edited_image, 120, 180, cv2.THRESH_BINARY)
        self.display_image(self.filtered_image)
        ttk.Label(self.frame_second,text='Don\'t forget to apply your changes!').grid(row=7,column=1, sticky = 'sw')

    # Create filter making image looks chill
    def chill(self):
        self.filtered_image = self.cooler(self.edited_image)
        self.display_image(self.filtered_image)
        ttk.Label(self.frame_second,text='Don\'t forget to apply your changes!').grid(row=7,column=1, sticky = 'sw')

    # Create filter making image black and white
    def bw(self):
        self.filtered_image = cv2.cvtColor(self.edited_image, cv2.COLOR_BGR2GRAY)
        self.filtered_image = cv2.cvtColor(self.filtered_image, cv2.COLOR_GRAY2BGR)
        self.display_image(self.filtered_image)
        ttk.Label(self.frame_second,text='Don\'t forget to apply your changes!').grid(row=7,column=1, sticky = 'sw')

    # Create filter making image looks like vintage film scene.
    def film(self):
        self.filtered_image = cv2.blur(self.edited_image,(5,5))
        kernel = np.ones((3, 3), np.uint8)
        self.filtered_image = cv2.erode(self.filtered_image, kernel, iterations=1)
        self.filtered_image = self.warmer(self.filtered_image)
        self.display_image(self.filtered_image)
        ttk.Label(self.frame_second,text='Don\'t forget to apply your changes!').grid(row=7,column=1, sticky = 'sw')

    # Create filter making image looks like pencil sketch
    def paint(self):
        #Just like other smoothing filters sigma_s controls the size of the neighborhood, and sigma_r (for sigma_range) controls the how dissimilar colors within the neighborhood will be averaged. A larger sigma_r results in large regions of constant color.
        ret, self.filtered_image = cv2.pencilSketch(self.edited_image, sigma_s=3, sigma_r=0.1, shade_factor=0.05)
        self.display_image(self.filtered_image)
        ttk.Label(self.frame_second,text='Don\'t forget to apply your changes!').grid(row=7,column=1, sticky = 'sw')


# -------------------------------------- Button Functions --------------------------------------

# Initialize interpreter and creates the root window.
root = Tk()
# Run the application.
Editor(root)
# End the application when the window closed.
root.mainloop()
