#!/usr/bin/env python
#
# Convert DICOM files to NIfTI format.

from fprep.subjutil import *
from fprep import heuristic

parser = SubjParser()
args = parser.parse_args()

sp = SubjPath(args.subject, args.study_dir)
log = sp.init_log('dcm2nii', 'preproc', args)

# make sure standard directories exist
sp.make_std_dirs()
log.start()

heuristic.dicom2nifti(sp, log)

log.finish()
