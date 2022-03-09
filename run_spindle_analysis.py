# -*- coding: utf-8 -*-
"""
Created on Wed Mar  9 10:03:10 2022

@author: Simon Kern
"""

import yasa # Yet Another Spindle Algorithm - https://github.com/raphaelvallat/yasa
import mne # MNE is a package to load EEG data (i.e. EDF files)



# Load the EDF file
raw = mne.io.read_raw_edf('MYEDFFILE.edf', preload=True)
# Downsample the data to 100 Hz
raw.resample(100)
# Apply a bandpass filter from 0.1 to 40 Hz
raw.filter(0.1, 40)
# Select a subset of EEG channels
raw.pick_channels(['C4-A1', 'C3-A2'])