# -*- coding: utf-8 -*-
"""
Created on Mon Mar 21 11:03:47 2022

utils for spindle analysis. Code mostly copied from other projects such as 
sleep_utils etc etc.

@author: Simon
"""
import sys
import os
import subprocess
import warnings
from io import StringIO
from tkinter.filedialog import askopenfilenames, askdirectory
from tkinter import simpledialog
from tkinter import  Tk
import matplotlib
import matplotlib.pyplot as plt



stages_dict = {'WAKE':0, 'N1': 1, 'N2': 2, 'N3': 3, 'REM': 4, **{i:i for i in range(5, 10)}}
stages_dict = {v: k for k, v in stages_dict.items()}


def install(package, options):
    if isinstance(package, str):
        package = [package]
    if isinstance(options, str):
        options = [options]    
    with subprocess.Popen([sys.executable, "-m", "pip", "install", *package, *options], stdout=subprocess.PIPE, bufsize=0) as p:
        char = p.stdout.read(1)
        while char != b'':
            print(char.decode('UTF-8'), end='', flush=True)
            char = p.stdout.read(1)
    if p.returncode: 
        raise Exception(f'\t!!! Could not install {package}\n')


def choose_files(default_dir=None, exts='txt', title='Choose file(s)'):
    """
    Open a file chooser dialoge with tkinter.
    
    :param default_dir: Where to open the dir, if set to None, will start at wdir
    :param exts: A string or list of strings with extensions etc: 'txt' or ['txt','csv']
    :returns: the chosen file
    """
    root = Tk()
    root.iconify()
    root.update()
    if isinstance(exts, str): exts = [exts]
    files = askopenfilenames(initialdir=None,
                           parent=root,
                           title = title,
                           filetypes =(*[("File", "*.{}".format(ext)) for ext in exts],
                                       ("All Files","*.*")))
    root.update()
    root.destroy()

    return files
    
    
def infer_hypno_file(filename):
    folder, filename = os.path.split(filename)
    possible_names = [filename + '.txt']
    possible_names += [filename + '.csv']
    possible_names += [os.path.splitext(filename)[0] + '.txt']
    possible_names += [os.path.splitext(filename)[0] + '.csv']


    for file in possible_names:  
        if os.path.exists(os.path.join(folder, file)):
            return os.path.join(folder, file)
    warnings.warn(f'No Hypnogram found for {filename}, looked for: {possible_names}')
    return False


