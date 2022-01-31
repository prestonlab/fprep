# fPrep

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.5904032.svg)](https://doi.org/10.5281/zenodo.5904032)

Preprocessing of fMRI data.


## Installation on TACC resources

On TACC clusters (e.g., Lonestar 6), use the module system to load dependencies. 
Version numbers of dependencies list below are what have been previously tested.
Newer versions will generally also work, though look at the release notes for each package to be sure.
```bash
module use /work/03206/mortonne/software/modules
module load fsl/5.0.11  # earlier versions do not support Python 3
module load ants/2.1.0
module load matlab
module load freesurfer/6.0.0  # 5.3 will likely also work
module load fprepcore/1.0.0  # utilities needed for the pipeline
module load python3/3.9.7  # most versions of Python 3 should work
```

Set up a Python 3 environment to run the scripts (this only has to be done once):
```bash
python3 -m venv $WORK/fprep  # create environment directory
. $WORK/fprep/bin/activate  # activate the environment
pip install git+https://github.com/prestonlab/fprep.git
pip install ezlaunch  # utilities for submitting jobs
```

After Python 3 packages have been installed, for later sessions you only need to activate the environment.


## Procedure

See the [tutorial](https://github.com/prestonlab/fprep/wiki/Introduction-and-Setup)
for instructions for running on a sample dataset on TACC.


## Related code

The quality assurance code is adapted from [fmriqa](https://github.com/poldrack/fmriqa) by Russ Poldrack.
The `epi_reg_ants` script is adapted from `epi_reg` from FSL 5. 


## Citation

If you use fPrep, please cite the following:

Morton NW, Schlichting ML, Preston AR. 2020. 
Events with common structure become organized within a hierarchical cognitive map in hippocampus and frontoparietal cortex. 
Proceedings of the National Academy of Sciences.
117(47): 29338-29345. https://doi.org/10.1073/pnas.1912338117.

The zenodo [archive](https://doi.org/10.5281/zenodo.5904032).
Use the DOI corresponding to the version you used.
