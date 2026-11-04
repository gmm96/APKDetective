"""
Probe for the scrollbar thumb: shows the thumb fill drawn in five different ways, each in red.
Run it and note which columns show a solid red bar (the label says what each one is).
"""

import tkinter as tk

import ttkbootstrap as ttkb

root = ttkb.Window(themename="nord-dark")  # use your theme
root.geometry("640x300")
style = ttkb.Style()
RED = "#ff0000"
TROUGH = "#2e3440"

red_pixel = tk.PhotoImage(master=root, width=1, height=1)
red_pixel.put(RED)
spacer = tk.PhotoImage(master=root, width=8, height=1)  # gives the bar its thickness
spacer.put(TROUGH, to=(0, 0, 8, 1))

# label -> (how the fill element is created, style options)
variants = {
    "A: field (default)": (("from", "default", "field"), {"fieldbackground": RED, "borderwidth": 0}),
    "B: border (default)": (("from", "default", "border"), {"background": RED, "borderwidth": 0, "relief": "flat"}),
    "C: field (clam)": (("from", "clam", "field"), {"fieldbackground": RED, "borderwidth": 0}),
    "D: thumb (clam)": (("from", "clam", "Scrollbar.thumb"), {"background": RED, "borderwidth": 0, "relief": "flat"}),
    "E: image": (("image", red_pixel), {"borderwidth": 0}),
}

for index, (label, (element_args, options)) in enumerate(variants.items()):
    key = f"Probe{index}"
    style_name = f"{key}.Vertical.TScrollbar"
    style.element_create(f"{key}.fill", *element_args)
    style.element_create(f"{key}.spacer", "image", spacer)
    style.configure(style_name, troughcolor=TROUGH, arrowsize=0, **options)
    style.layout(style_name, [("Vertical.Scrollbar.trough", {"sticky": "ns", "children": [
        (f"{key}.spacer", {"side": "top", "sticky": "we"}),
        (f"{key}.fill", {"sticky": "nswe"}),
    ]})])
    frame = ttkb.Frame(root)
    frame.pack(side="left", fill="y", padx=8, pady=8)
    bar = ttkb.Scrollbar(frame, orient="vertical", style=style_name)
    bar.pack(side="left", fill="y")
    bar.set(0.2, 0.7)
    ttkb.Label(frame, text=label, wraplength=70).pack(side="left", anchor="n")

root.update_idletasks()
print("ttkbootstrap", ttkb.__version__, "| Tk", root.tk.call("info", "patchlevel"),
      "| windowing", root.tk.call("tk", "windowingsystem"), "| scaling", root.tk.call("tk", "scaling"))
root.mainloop()
