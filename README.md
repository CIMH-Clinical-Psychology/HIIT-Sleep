# Sleep Spindle Analysis using YASA and Python for Absolute Beginners

This README will explain to you how to perform spindle analysis in Python using [YASA (Yet Another Spindle Algorithm)](https://github.com/raphaelvallat/yasa) and is focused at people that do not have (a lot of) programming experience. 

YASA has the advantage of having lots of examples for running it, which should make it easier to understand and adapt for individual purposes. The YASA examples use Jupyter Notebook, which are a beginner-friendly way of executing Python code. 

### 1. Prerequisite

To run the analysis you need to run the following steps and install the following software

1. Python 3 installed. I recommend installing the latest version of [Anaconda](https://www.anaconda.com) into your user folder. Anaconda automatically includes the latest version of Python and many other packages that are useful for getting started (i.e. Jupyter notebook)

2. Install YASA inside the Python environment by
   
   1. opening the Anaconda Prompt (which appears in your start menu after installing anaconda)
   
   2. use the pip package manager to install YASA by typing `pip install yasa`

3. Download the contents of this GitHub repository to your local computer inside your home directory (e.g. by clicking on the green `Code` button and then `download ZIP`)

![](https://raw.githubusercontent.com/CIMH-Clinical-Psychology/HIIT-Sleep/main/md_assets/2022-03-09-15-23-15-image.png)

### 2. Using Jupyter Notebooks

Start the Jupyter Notebook application by either directly running`Jupyter Notebook` from the [start menu](https://raw.githubusercontent.com/CIMH-Clinical-Psychology/HIIT-Sleep/main/md_assets/2022-03-09-11-16-30-image.png) or typing `jupyter notebook` into the [Anaconda Prompt](https://raw.githubusercontent.com/CIMH-Clinical-Psychology/HIIT-Sleep/main/md_assets/2022-03-09-11-18-03-image.png). A browser will open automatically. Within the browser, browse to the folder where your notebooks are located. Be aware that by default, the Jupyter Notebook browser only has access to your user folder, so you need to place the notebook files somewhere there (e.g. your Desktop or Documents). The EEG data does not need to be there necessarily, just the notebook files.

Excursion: What is Jupyter Notebooks?

> Jupyter Notebook has the advantage of combining code and documentation/explanation into one file

> Notebook documents (or “notebooks”, all lower case) are documents produced by the [Jupyter Notebook App](https://jupyter-notebook-beginner-guide.readthedocs.io/en/latest/what_is_jupyter.html#notebook-app), which contain both computer code (e.g. python) and rich text elements (paragraph, equations, figures, links, etc…). Notebook documents are both human-readable documents containing the analysis description and the results (figures, tables, etc..) as well as executable documents which can be run to perform data analysis.

Jupyter Notebooks have the file ending `.ipynb`. Inside they are subdivided into so called "cells". Each cell can either contain Python code or human readable explanations. 

If you want to get a bit more familiar with Jupyter Notebooks first, there are many great tutorials on the internet, e.g. this [German tutorial](https://www.youtube.com/watch?v=1S4Cgtkxqhs) which is quite beginner friendly.


### 3. Start the tutorial for analysing a single subject


For now, using the Jupyter Notebook browser, open the tutorial file on your local computer with the name `1-basic-sleep-spindle-analysis.ipynb` that you downloaded from this website. There you will find instructions on how to perform a first, simple sleep spindle analysis on a single subject.
