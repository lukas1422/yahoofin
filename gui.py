import tkinter as tk
from tkinter import ttk

win = tk.Tk()
win.title('GUI')
aLabel = ttk.Label(win, text='a label')
aLabel.grid(column=0, row=0)

def clickme():
    action.configure(text='clicked')
    aLabel.configure(foreground='red')
    aLabel.configure(text='a red label')

action = ttk.Button(win, text='click me', command=clickme)
action.grid(column=1, row=0)

win.mainloop()
