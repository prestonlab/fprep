#!/usr/bin/env python

from fprep.subjutil import *
from fprep import heuristic


parser = SubjParser()
args = parser.parse_args()
sp = SubjPath(args.subject, args.study_dir)
log = sp.init_log("rename", "preproc", args)

log.start()
heuristic.rename_bold(sp, log)
heuristic.rename_anat(sp, log)
log.finish()
