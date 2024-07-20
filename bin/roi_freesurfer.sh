#!/bin/bash
#
# Create masks for standard ROIs based on FreeSurfer.

if [[ $# -eq 0 ]]; then
    echo "Create files for standard ROIs based on Freesurfer"
    echo
    echo "Usage:"
    echo "roi_freesurfer.sh [parcfile] [outdir]"
    echo
    echo "Inputs:"
    echo "parcfile   path to Freesurfer aparc+aseg file"
    echo "outdir     directory in which to save ROI files"
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

if [[ ! -e ${outdir}/parcels ]]; then
    cp "${parcfile}" "${outdir}/parcels.nii.gz"
fi
cd "${outdir}" || exit

# erc   entorhinal cortex
# fus   fusiform gyrus
# it    inferior temporal cortex
# phc   parahippocampal cortex
# hip   hippocampus
# lofc  lateral orbitofrontal cortex
# lo    lateral occipital
# oper  pars opercularis
# tria  pars triangularis
# orbi  pars orbitalis
# mofc  medial orbitofrontal cortex
# fropo frontal pole
# sfg   superior frontal gyrus
# rmfg  rostral middle frontal gyrus
# cmfg  caudal middle frontal gyrus
# vidc  ventral diencephalon
# tpo   temporal pole

fslmaths parcels -thr 1006 -uthr 1006 -bin l_erc
fslmaths parcels -thr 2006 -uthr 2006 -bin r_erc
fslmaths parcels -thr 1007 -uthr 1007 -bin l_fus
fslmaths parcels -thr 2007 -uthr 2007 -bin r_fus
fslmaths parcels -thr 1009 -uthr 1009 -bin l_it
fslmaths parcels -thr 2009 -uthr 2009 -bin r_it
fslmaths parcels -thr 1033 -uthr 1033 -bin l_tpo
fslmaths parcels -thr 2033 -uthr 2033 -bin r_tpo
fslmaths parcels -thr 1016 -uthr 1016 -bin l_phc
fslmaths parcels -thr 2016 -uthr 2016 -bin r_phc
fslmaths parcels -thr 17 -uthr 17 -bin l_hip
fslmaths parcels -thr 53 -uthr 53 -bin r_hip
fslmaths parcels -thr 1012 -uthr 1012 -bin l_lofc
fslmaths parcels -thr 2012 -uthr 2012 -bin r_lofc
fslmaths parcels -thr 1011 -uthr 1011 -bin l_lo
fslmaths parcels -thr 2011 -uthr 2011 -bin r_lo
fslmaths parcels -thr 1018 -uthr 1018 -bin l_oper
fslmaths parcels -thr 2018 -uthr 2018 -bin r_oper
fslmaths parcels -thr 1019 -uthr 1019 -bin l_orbi
fslmaths parcels -thr 2019 -uthr 2019 -bin r_orbi
fslmaths parcels -thr 1020 -uthr 1020 -bin l_tria
fslmaths parcels -thr 2020 -uthr 2020 -bin r_tria
fslmaths parcels -thr 1014 -uthr 1014 -bin l_mofc
fslmaths parcels -thr 2014 -uthr 2014 -bin r_mofc
fslmaths parcels -thr 1032 -uthr 1032 -bin l_fropo
fslmaths parcels -thr 2032 -uthr 2032 -bin r_fropo
fslmaths parcels -thr 1028 -uthr 1028 -bin l_sfg
fslmaths parcels -thr 2028 -uthr 2028 -bin r_sfg
fslmaths parcels -thr 1027 -uthr 1027 -bin l_rmfg
fslmaths parcels -thr 2027 -uthr 2027 -bin r_rmfg
fslmaths parcels -thr 1003 -uthr 1003 -bin l_cmfg
fslmaths parcels -thr 2003 -uthr 2003 -bin r_cmfg
fslmaths parcels -thr 28 -uthr 28 -bin l_vidc
fslmaths parcels -thr 60 -uthr 60 -bin r_vidc

# ctx   all cortical regions
# subco all subcortical regions

fslmaths parcels -thr 1000 -uthr 1035 -bin l_ctx
fslmaths parcels -thr 2000 -uthr 2035 -bin r_ctx

fslmaths parcels -thr 9 -uthr 13 -bin l_subco
fslmaths parcels -thr 18 -uthr 18 -add l_subco -add l_hip -bin l_subco
fslmaths parcels -thr 48 -uthr 54 -bin r_subco

# bilateral ROIs

fslmaths l_lofc -add r_lofc b_lofc
fslmaths l_mofc -add r_mofc b_mofc
fslmaths l_lo -add r_lo b_lo
fslmaths l_oper -add r_oper b_oper
fslmaths l_orbi -add r_orbi b_orbi
fslmaths l_tria -add r_tria b_tria

# ifg   inferior frontal gyrus

fslmaths b_oper -add b_orbi -add b_tria b_ifg
fslmaths l_oper -add l_orbi -add l_tria l_ifg
fslmaths r_oper -add r_orbi -add r_tria r_ifg

fslmaths l_erc -add r_erc b_erc
fslmaths l_fus -add r_fus b_fus
fslmaths l_it -add r_it b_it
fslmaths l_phc -add r_phc b_phc
fslmaths l_hip -add r_hip b_hip
fslmaths l_vidc -add r_vidc b_vidc

fslmaths l_fropo -add r_fropo b_fropo
fslmaths l_sfg -add r_sfg b_sfg
fslmaths l_rmfg -add r_rmfg b_rmfg
fslmaths l_cmfg -add r_cmfg b_cmfg

# gray  cortical and subcortical gray matter

fslmaths l_ctx -add r_ctx b_ctx
fslmaths l_subco -add r_subco b_subco
fslmaths b_subco -add b_ctx b_gray

# ostemporal    temporal regions
# ostemporal_lo temporal and lateral occipital regions

fslmaths b_erc -add b_fus -add b_it -add b_phc ostemporal
fslmaths b_erc -add b_fus -add b_it -add b_phc -add b_lo ostemporal_lo
