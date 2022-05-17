# -*- coding: utf-8 -*-
"""
Created on Mon May 16 11:27:48 2022

This script calculates spectrograms for different sleep stages,
excluding the segments that were denoted has having artefacts

@author: Simon
"""
import os
import yasa
import mne
import pandas as pd
import sleep_utils
import utils # must be executed in the same folder as the utils.py
from tqdm import tqdm

#%% SETTINGS

data_dir = 'Z:/Exercise_Sleep_Project/EDF Export EEG'

window_length = 10 # time window for the artefact detection, e.g. 10 seconds

channels = ['Pz'] # channel(s) that the artefact detection should be performed on
reference = ['M1', 'M2'] # list of channels used to construct a reference


#%%