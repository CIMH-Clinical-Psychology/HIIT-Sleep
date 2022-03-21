# -*- coding: utf-8 -*-
"""
Created on Mon Mar 21 11:03:47 2022

utils for spindle analysis. Code mostly copied from other projects such as 
sleep_utils etc etc.

@author: Simon
"""
import os
import warnings
import numpy as np
from io import StringIO
from natsort import natsort_key
from tkinter.filedialog import askopenfilenames, askdirectory
from tkinter import simpledialog
from tkinter import  Tk

stages_dict = {'WAKE':0, 'N1': 1, 'N2': 2, 'N3': 3, 'REM': 4, **{i:i for i in range(5, 10)}}
stages_dict = {v: k for k, v in stages_dict.items()}


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



  
def read_hypno(hypno_file, epochlen = 30, epochlen_infile=None, mode='auto', 
               exp_seconds=None, conf_dict=None, verbose=True):
    """
    reads a hypnogram file as created by VisBrain or as CSV type 
    (or also some custom cases like the Dreams database)
    
    :param hypno_file: a path to the hypnogram
    :param epochlen: how many seconds per label in output
    :param epochlen_infile: how many seconds per label in original file
    :param mode: 'auto', 'time' or 'csv', see SleepDev/docs/hypnogram.md
    :param exp_seconds: How many seconds does the matching recording have?
    """
    assert str(type(epochlen)()) == '0'
    assert epochlen_infile is None or str(type(epochlen_infile)()) == '0'
    
    if isinstance(hypno_file, str):
        with open(hypno_file, 'r') as file:
            content = file.read()
            content = content.replace('\r', '') # remove windows style \r\n
    elif isinstance(hypno_file, StringIO):
        content = hypno_file.read()
        content = content.replace('\r', '') # remove windows style \r\n
            
    #conversion dictionary
    if conf_dict is None:
        conv_dict = {'W':0, 'WAKE':0, 'N1': 1, 'N2': 2, 'N3': 3, 'R':4, 'REM': 4, 'ART': 9,
                     -1:9, '-1':9, **{i:i for i in range(0, 10)}, **{f'{i}':i for i in range(0, 10)}}
    
    lines = content.split('\n')
    if mode=='auto':
        if lines[0].startswith('*'): # if there is a star, we assume it's the visbrain type
            mode = 'time'
        elif lines[0].replace('-', '')[0].isnumeric():
            mode = 'csv'
        elif lines[0].startswith('[HypnogramAASM]'):
            mode = 'dreams'
        elif lines[0].startswith(' Epoch Number ,Start Time ,Sleep Stage'):
            mode = 'alice'
        elif lines[0].startswith('EPOCH=') and lines[1].startswith('START='):
            mode = 'csv'
            lines = [l.upper() for l in lines[2:]]
        else:
            known_stage = [l.upper() in conv_dict for l in lines]
            if all(known_stage):
                mode='csv'
            else:
                mode=None
            
    if mode=='time':
        if epochlen_infile is not None:
            warnings.warn('epochlen_infile has been supplied, but hypnogram is time based,'
                          'will be ignored')
        stages = []
        prev_t = 0
        for line in lines:
            if len(line.strip())==0:   continue
            if line[0] in '*#%/\\"\'': continue # this line seems to be a comment
            s, t = line.split('\t')
            t = float(t)
            s = conv_dict[s]
            l = int(np.round((t-prev_t))) # length of this stage
            stages.extend([s]*l)
            prev_t = t
            
    elif mode=='csv':
        if exp_seconds and not epochlen_infile:
            epochlen_infile=exp_seconds//len(lines)
            if verbose: print('[INFO]Assuming csv annotations with one entry per {} seconds'.format(epochlen_infile))

        elif epochlen_infile is None: 
            if len(lines) < 2400: # we assume no recording is longer than 20 hours
                epochlen_infile = 30
                if verbose: print('[INFO] Assuming csv annotations are per epoch')
            else:
                epochlen_infile = 1 
                if verbose: print('[INFO] Assuming csv annotations are per second')
        lines = [line.split('\t')[0] if '\t' in line else line for line in lines]
        lines = [conv_dict[l]  if l in conv_dict else l for l in lines if len(l)>0]
        lines = [[line]*epochlen_infile for line in lines]
        stages = np.array([conv_dict[l] for l in np.array(lines).flatten()])
    
    # for the Dreams Database    
    elif mode=='dreams':
        epochlen_infile = 5
        conv_dict = {-2:5,-1:5, 0:5, 1:3, 2:2, 3:1, 4:4, 5:0}    
        lines = [[int(line)] for line in lines[1:] if len(line)>0]
        lines = [[line]*epochlen_infile for line in lines]
        stages = np.array([conv_dict[l] for l in np.array(lines).flatten()])
        
    elif mode=='alice':
        epochlen_infile = 30
        conv_dict = {'WK':0,'N1':1, 'N2':2, 'N3':3, 'REM':4}  
        lines = [line.split(',')[-1] for line in lines[1:] if len(line)>0]
        lines = [[line]*epochlen_infile for line in lines]
        try: stages = np.array([conv_dict[l] for l in np.array(lines).flatten()])
        except KeyError as e:
            print('Unknown sleep stage in file')
            raise e
    else:
        raise ValueError('This is not a recognized hypnogram: {}'.format(hypno_file))
        
    stages = stages[::epochlen]
    if len(stages)==0:
        warnings.warn('hypnogram loading failed, len == 0')
        
    return np.array(stages)