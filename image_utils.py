import os
import tkinter as tk
from tkinter import ttk

from PIL import Image, ImageTk


def load_logo(path, size):
    """Load and resize application logo image for login header."""
    image = Image.open(path)
    resized = image.resize(size, Image.LANCZOS)
    return ImageTk.PhotoImage(resized)


def resize_avatar(path, size=(60, 60)):
    """Load and resize user avatar image using thumbnail operation."""
    image = Image.open(path)
    image.thumbnail(size, Image.LANCZOS)
    return ImageTk.PhotoImage(image)


def attach_screenshot(ticket_id, source_path):
    """Resize and save ticket screenshot under assets/screenshots directory."""
    os.makedirs("assets/screenshots", exist_ok=True)
    destination = f"assets/screenshots/ticket_{ticket_id}.png"
    image = Image.open(source_path)
    image.thumbnail((400, 400), Image.LANCZOS)
    image.save(destination)
    return destination


def show_screenshot(path, parent_frame):
    """Return a ttk label widget that displays a resized screenshot image."""
    image = Image.open(path)
    resized = image.resize((380, 280), Image.LANCZOS)
    photo = ImageTk.PhotoImage(resized)
    label = ttk.Label(parent_frame, image=photo)
    label.image = photo
    return label
