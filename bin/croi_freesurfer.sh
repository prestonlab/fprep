#!/bin/bash
#
# Create files for standard cortical ROIs based on FreeSurfer.

if [[ $# -eq 0 ]]; then
    echo "Create files for standard cortical ROIs based on Freesurfer"
    echo
    echo "Usage:"
    echo "croi_freesurfer.sh [parcfile] [outdir]"
    echo
    echo "Inputs:"
    echo "parcfile   path to Freesurfer aparc+aseg.nii.gz file"
    echo "outdir     directory in which to save ROI files"
    echo
    echo "See $FREESURFER_HOME/FreeSurferColorLUT.txt for all ROI"
    echo "codes and full ROI names. Cortical ROIs are 1XXX (left)"
    echo "and 2XXX (right)."
    echo
    exit 1
fi

parcfile=$1
outdir=$2

if [[ ! -f ${parcfile} ]]; then
    echo "Input parcel file does not exist: ${parcfile}" 1>&2
    exit 1
fi

if [[ ! -d ${outdir} ]]; then
    echo "Output directory does not exist: ${outdir}" 1>&2
    exit 1
fi

if [[ ! -e ${outdir}/parcels.nii.gz ]]; then
    cp "${parcfile}" "${outdir}/parcels.nii.gz"
fi
cd "${outdir}" || exit

fscroi parcels . 2 cac
fscroi parcels . 3 cmf
fscroi parcels . 5 cun
fscroi parcels . 6 erc
fscroi parcels . 7 fus
fscroi parcels . 8 ip
fscroi parcels . 9 it
fscroi parcels . 10 imc
fscroi parcels . 11 lo
fscroi parcels . 12 lofc
fscroi parcels . 13 ling
fscroi parcels . 14 mofc
fscroi parcels . 15 mt
fscroi parcels . 16 phc
fscroi parcels . 17 paracent
fscroi parcels . 18 oper
fscroi parcels . 19 orbi
fscroi parcels . 20 tria
fscroi parcels . 21 peric
fscroi parcels . 22 postcent
fscroi parcels . 23 pc
fscroi parcels . 24 precent
fscroi parcels . 25 precun
fscroi parcels . 26 rac
fscroi parcels . 27 rmf
fscroi parcels . 28 sf
fscroi parcels . 29 sp
fscroi parcels . 30 st
fscroi parcels . 31 supram
fscroi parcels . 32 fpo
fscroi parcels . 33 tpo
fscroi parcels . 34 tt
fscroi parcels . 35 insula
