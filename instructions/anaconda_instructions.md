# Get conda environment for BrainFlow in Python

## Download anaconda/miniconda (if you don't already have it)
Choose between installing anaconda or miniconda. Both will give you access to the package manager `conda` and python, but anaconda contains ~250 pre-installed python packages (~4GB), while miniconda is simply `conda` with a minimal amount of dependencies. I personally would recommend miniconda, since it's quicker to install and does not contain packages you may not need. If you go through with the miniconda installer, you can always change your mind later and acquire the equivalent packages of anaconda by running `conda install anaconda`.

Download links:
 - [Anaconda](https://www.anaconda.com/products/individual)
 - [Miniconda](https://docs.conda.io/en/latest/miniconda.html)

Installation instructions anaconda/miniconda:
 - [Linux](https://docs.conda.io/projects/continuumio-conda/en/latest/user-guide/install/linux.html)
 - [MacOS](https://conda.io/projects/conda/en/latest/user-guide/install/macos.html)
 - [Windows](https://docs.conda.io/projects/continuumio-conda/en/latest/user-guide/install/windows.html)
 
The install process basically boils down to this:
 1. Download the appropriate installer.
 2. Optional, but recommended: [Verify installer hash](https://conda.io/projects/conda/en/latest/user-guide/install/download.html#hash-verification).
	- Linux: `echo "<SHA256 hash> <installer>" | sha256sum --check`

	- MacOS: `echo "<SHA256 hash> <installer>" | shasum -a 256 --check`

	- Windows: `Get-FileHash <installer> -Algorithm SHA256`

	**Note!** Replace `<installer>` and `<SHA256 hash>` with the installer file and the appropriate hash found next to where you downloaded the installer. Example:
	```bash
	elias@xps13:~/Downloads$ echo "1ea2f885b4dbc3098662845560bc64271eb17085387a70c2ba3f29fff6f8d52f Miniconda3-latest-Linux-x86_64.sh" | sha256sum --check
	Miniconda3-latest-Linux-x86_64.sh: OK
	```

 3. Install:
	 - Linux: Navigate to the installer and run in your terminal:
	```
	bash <installer>.sh
	```
	 - MacOS: For anaconda, double-click the `.pkg` file. For miniconda, navigate to the installer and run in your terminal:
	```
	bash <installer>.sh
	```
	 - Windows: Double click the `.exe` file.

 4. Follow the prompts on the installer screens.

	If you are unsure about any setting, accept the defaults. You can change them later.

 5. Reopen your terminal to make the changes take effect.
 
 6. Test your installation by running `conda list` in your terminal or in the anaconda prompt, a list of all installed packages should show up.

 7. Optional: If you don't want conda to automatically activate the base environment at startup, run the following line:
	```bash
	conda config --set auto_activate_base false
	```

## Create a new envionment
 - `conda create --name braingame` och answer yes if you want to save the environment at the default location.
 - `conda activate braingame`

## Get the BrainFlow library in your conda environment

 - Install pip in your environment: `conda install pip` 
 - Run `which pip` (Linux/MacOS) or `where pip` (Windows) to verify that when the command `pip` is executed, the version of pip installed in your conda environment `braingame` is used. E.g.: 
```bash
(braingame) elias@xps13:~/Documents/brain-game$ which pip
/home/elias/anaconda3/envs/braingame/bin/pip 
```
 - Install brainflow: `python -m pip install brainflow`
 - Optional: Install more useful python packages in your conda environment like NumPy, SciPy, SciKit-Learn, Matplotlib and so on. E.g.: `conda install numpy scipy matplotlib scikit-learn`.
 
 - Verify that brainflow can be accessed in python. Start python by running `python` and try to import brainflow by running `import brainflow as bf`. If you do not get any error message, everything should be working as intended.

## Jupyter notebook support
Optionally, one can work with a jupyter notebook during the development phase, instead of executing python scripts via command line. To download and install Jupyter-Lab (the official successor to the classical Jupyter Notebook) within the conda environment, run the command:
```bash
conda install -c conda-forge jupyterlab
```
Start Jupyter-Lab by running:
```bash
jupyter-lab
```
Select ipykernel as the active kernel for the notebook, and all libraries we installed earlier should be available.

That's it, good luck coding! 

## Graphical real-time plotting in Python
In order to run the PyQtGraph-based scripts `main.py` and `real_time_plot.py`, the `pyqtgraph`-package needs to be installed:
 - `conda install -c conda-forge pyqtgraph`

Not neccessary for the above scripts, but required for 3D-graphics in pyqtgraph:
 - `pip install PyOpenGL PyOpenGL_accelerate`

