from tkinter import Tk
from main_window import MainWindow


def initial_output_dir():
    import os
    output_dir = os.path.join(os.getcwd(), "output")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)


if __name__ == "__main__":
    initial_output_dir()
    window = Tk()
    mainWindow = MainWindow(window)
    window.mainloop()