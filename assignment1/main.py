from tkinter import *
import tkinter.messagebox as tkMessageBox
from PIL import Image, ImageTk
filename = "movie.Mjpeg"
file = open(filename, 'rb')
print(int(file.read(5)))
