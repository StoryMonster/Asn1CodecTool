from tkinter import Tk
from main_window import MainWindow
import json


def initial():
    import os
    ## read configuration information
    context = {}
    with open("config.ini", "r") as fd:
        context = json.loads(fd.read(-1))
    ## initial output dir, to save generated python file
    output_dir = os.path.join(os.getcwd(), "output")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    return context


if __name__ == "__main__":
    context = initial()
    window = Tk()
    mainWindow = MainWindow(window, context)
    window.mainloop()