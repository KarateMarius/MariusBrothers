import tkinter as tk
from itertools import cycle
from PIL import ImageTk

images = ["cwr1.png", "cwr2.png", "cwr3.png", "cwr4.png"]
photos = cycle(ImageTk.PhotoImage(file=image) for image in images)

def slideShow():
  img = next(photos)
  displayCanvas.config(image=img)
  root.after(100, slideShow) # 0.1 seconds

root = tk.Tk()
#root.overrideredirect(True)
root.geometry("300x600")
displayCanvas = tk.Label(root)
displayCanvas.pack()
root.after(10, lambda: slideShow())
root.mainloop()