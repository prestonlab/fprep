#!/usr/bin/env python
#
# Calculate quality assurance statistics for fMRI data.

"""
fMRI quality control
- adapted from fsld_raw.R and fBIRN QA tools

USAGE: fmriqa.py bold_mcf.nii.gz <TR>
"""

import ctypes
import sys
import os

flags = sys.getdlopenflags()
sys.setdlopenflags(flags | ctypes.RTLD_GLOBAL)

import matplotlib
matplotlib.use("Agg")
import numpy as np
import nibabel as nib
from fprep import qa
from statsmodels.tsa.tsatools import detrend
import matplotlib.pyplot as plt
import sklearn.model_selection
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.mlab import psd


sys.setdlopenflags(flags)

# thresholds for scrubbing and spike detection
FDthresh = 0.5
DVARSthresh = 0.5
AJKZ_thresh = 25

# number of timepoints forward and back to scrub
nback = 1
nforward = 2


def error_and_exit(msg):
    print(msg)
    sys.stdout.write(__doc__)
    sys.exit(2)


def main():
    verbose = True

    if len(sys.argv) > 2:
        infile = sys.argv[1]
        TR = float(sys.argv[2])
    else:
        error_and_exit("")

    fmriqa(infile, TR, verbose=verbose, plot_data=True)


def fmriqa(
    infile, TR, outdir=None, maskfile=None, motfile=None, verbose=False, plot_data=True
):
    save_sfnr = True

    if os.path.dirname(infile) == "":
        basedir = os.getcwd()
        infile = os.path.join(basedir, infile)
    elif os.path.dirname(infile) == ".":
        basedir = os.getcwd()
        infile = os.path.join(basedir, infile.replace("./", ""))
    else:
        basedir = os.path.dirname(infile)

    if outdir is None:
        outdir = basedir

    qadir = os.path.join(outdir, "QA")

    if not infile.find("mcf.nii.gz") > 0:
        error_and_exit("infile must be of form XXX_mcf.nii.gz")

    if not os.path.exists(infile):
        error_and_exit("%s does not exist!" % infile)

    if maskfile is None:
        maskfile = infile.replace("mcf.nii", "mcf_brain_mask.nii")

    if not os.path.exists(maskfile):
        error_and_exit("%s does not exist!" % maskfile)

    if motfile is None:
        motfile = infile.replace("mcf.nii.gz", "mcf.par")
    if not os.path.exists(motfile):
        error_and_exit("%s does not exist!" % motfile)

    if not os.path.exists(qadir):
        os.mkdir(qadir)
    else:
        print("QA dir already exists - overwriting!")

    if verbose:
        print("infile:", infile)
        print("maskfile:", maskfile)
        print("motfile:", motfile)
        print("outdir:", outdir)
        print("computing image stats")

    img = nib.load(infile)
    imgdata = img.get_fdata()

    nslices = imgdata.shape[2]
    ntp = imgdata.shape[3]

    maskimg = nib.load(maskfile)
    maskdata = maskimg.get_fdata()
    maskvox = np.where(maskdata > 0)
    nonmaskvox = np.where(maskdata == 0)
    if verbose:
        print("nmaskvox:", len(maskvox[0]))

    # load motion parameters and compute FD and identify bad vols for
    # potential scrubbing (ala Power et al.)
    motpars = np.loadtxt(motfile)
    fd = qa.compute_fd(motpars)
    np.savetxt(os.path.join(qadir, "fd.txt"), fd)

    voxmean = np.mean(imgdata, 3)
    voxstd = np.std(imgdata, 3)
    voxcv = voxstd / np.abs(voxmean)
    voxcv[np.isnan(voxcv)] = 0
    voxcv[voxcv > 1] = 1

    # compute timepoint statistics
    maskmedian = np.zeros(imgdata.shape[3])
    maskmean = np.zeros(imgdata.shape[3])
    maskmad = np.zeros(imgdata.shape[3])
    maskcv = np.zeros(imgdata.shape[3])
    imgsnr = np.zeros(imgdata.shape[3])

    for t in range(imgdata.shape[3]):
        tmp = imgdata[:, :, :, t]
        tmp_brain = tmp[maskvox]
        tmp_nonbrain = tmp[nonmaskvox]
        maskmad[t] = qa.MAD(tmp_brain)
        maskmedian[t] = np.median(tmp_brain)
        maskmean[t] = np.mean(tmp_brain)
        maskcv[t] = maskmad[t] / maskmedian[t]
        imgsnr[t] = maskmean[t] / np.std(tmp_nonbrain)

    # perform Greve et al./fBIRN spike detection
    # 1. Remove mean and temporal trend from each voxel.
    # 2. Compute temporal Z-score for each voxel.
    # 3. Average the absolute Z-score (AAZ) within a each slice and time point separately.
    # This gives a matrix with number of rows equal to the number of slices (nSlices)
    # and number of columns equal to the number of time points (nFrames).
    # 4. Compute new Z-scores using a jackknife across the slices (JKZ). For a given time point,
    # remove one of the slices, compute the average and standard deviation of the AAZ across
    # the remaining slices. Use these two numbers to compute a Z for the slice left out
    # (this is the JKZ). The final Spike Measure is the absolute value of the JKZ (AJKZ).
    # Repeat for all slices. This gives a new nSlices-by-nFrames matrix (see Figure 8).
    # This procedure tends to remove components that are common across slices and so rejects motion.
    if verbose:
        print("computing spike stats")

    detrended_zscore = np.zeros(imgdata.shape)
    detrended_data = np.zeros(imgdata.shape)

    for i in range(len(maskvox[0])):
        tmp = imgdata[maskvox[0][i], maskvox[1][i], maskvox[2][i], :]
        tmp_detrended = detrend(tmp)
        detrended_data[maskvox[0][i], maskvox[1][i], maskvox[2][i], :] = tmp_detrended
        detrended_zscore[maskvox[0][i], maskvox[1][i], maskvox[2][i], :] = (
            tmp_detrended - np.mean(tmp_detrended)
        ) / np.std(tmp_detrended)

    AAZ = np.zeros((nslices, ntp))
    for s in range(nslices):
        for t in range(ntp):
            AAZ[s, t] = np.mean(np.abs(detrended_zscore[:, :, s, t]))

    JKZ = np.zeros((nslices, ntp))
    if verbose:
        print("computing outliers")
    loo = sklearn.model_selection.LeaveOneOut()
    for train, test in loo.split(AAZ):
        for tp in range(ntp):
            train_mean = np.mean(AAZ[train, tp])
            train_std = np.std(AAZ[train, tp])
            JKZ[test, tp] = (AAZ[test, tp] - train_mean) / train_std
    AJKZ = np.abs(JKZ)
    spikes = []
    if np.max(AJKZ) > AJKZ_thresh:
        print("Possible spike: Max AJKZ = %f" % np.max(AJKZ))
        spikes = np.where(np.max(AJKZ, 0) > AJKZ_thresh)[0]
    if len(spikes) > 0:
        np.savetxt(os.path.join(qadir, "spikes.txt"), spikes)

    voxsfnr = voxmean / voxstd
    meansfnr = np.mean(voxsfnr[maskvox])

    # create plots
    if verbose:
        print("checking for bad volumes")
    mean_running_diff = (maskmean[1:] - maskmean[:-1]) / (
        (maskmean[1:] + maskmean[:-1]) / 2.0
    )
    DVARS = np.zeros(fd.shape)
    DVARS[1:] = np.sqrt(mean_running_diff ** 2) * 100.0
    np.savetxt(os.path.join(qadir, "dvars.txt"), DVARS)

    badvol_index_orig = np.where((fd > FDthresh) * (DVARS > DVARSthresh))[0]
    badvols = np.zeros(len(DVARS))
    badvols[badvol_index_orig] = 1
    badvols_expanded = badvols.copy()
    for i in badvol_index_orig:
        if i > (nback - 1):
            start = i - nback
        else:
            start = 0
        if i < (len(badvols) - nforward):
            end = i + nforward + 1
        else:
            end = len(badvols)
        badvols_expanded[start:end] = 1
    badvols_expanded_index = np.where(badvols_expanded > 0)[0]
    if len(badvols_expanded_index) > 0:
        if verbose:
            print("writing scrub volumes")
        np.savetxt(
            os.path.join(qadir, "scrubvols.txt"), badvols_expanded_index, fmt="%d"
        )

        # make scrubing design matrix - one colum per scrubbed timepoint
        scrubdes = np.zeros((len(DVARS), len(badvols_expanded_index)))
        for i in range(len(badvols_expanded_index)):
            scrubdes[badvols_expanded_index[i], i] = 1
        np.savetxt(os.path.join(qadir, "scrubdes.txt"), scrubdes, fmt="%d")
    else:
        scrubdes = None

    # save out complete confound file
    if verbose:
        print("writing confound file")
    confound_mtx = np.zeros((len(DVARS), 14))
    confound_mtx[:, 0:6] = motpars
    confound_mtx[1:, 6:12] = motpars[:-1, :] - motpars[1:, :]  # derivs
    confound_mtx[:, 12] = fd
    confound_mtx[:, 13] = DVARS
    if scrubdes is not None:
        confound_mtx = np.hstack((confound_mtx, scrubdes))

    np.savetxt(os.path.join(qadir, "confound.txt"), confound_mtx)

    # give 12 and 24 columns options
    motonly = confound_mtx[:, :12]
    motonly_squared = np.hstack((motonly, np.power(motonly, 2)))
    np.savetxt(os.path.join(qadir, "confound12.txt"), motonly)
    np.savetxt(os.path.join(qadir, "confound24.txt"), motonly_squared)

    datavars = {
        "imgsnr": imgsnr,
        "meansfnr": meansfnr,
        "spikes": spikes,
        "badvols": badvols_expanded_index,
    }

    if plot_data:
        if verbose:
            print("plotting timeseries data")
        trend = qa.plot_timeseries(
            maskmean,
            "Mean signal (unfiltered)",
            os.path.join(qadir, "maskmean.png"),
            plottrend=True,
            ylabel="Mean MR signal",
        )
        datavars["trend"] = trend
        qa.plot_timeseries(
            maskmad,
            "Median absolute deviation (robust SD)",
            os.path.join(qadir, "mad.png"),
            ylabel="MAD",
        )

        qa.plot_timeseries(
            DVARS,
            "DVARS (root mean squared signal derivative over brain mask)",
            os.path.join(qadir, "DVARS.png"),
            plotline=0.5,
            ylabel="DVARS",
        )

        qa.plot_timeseries(
            fd,
            "Framewise displacement",
            os.path.join(qadir, "fd.png"),
            markers=badvols_expanded_index,
            markername="Timepoints to scrub (%d total)" % len(badvols),
            plotline=0.5,
            ylims=[0, 1],
            ylabel="FD",
        )

        psd = matplotlib.mlab.psd(maskmean, NFFT=128, noverlap=96, Fs=1 / TR)

        plt.clf()
        fig = plt.figure(figsize=[10, 3])
        fig.subplots_adjust(bottom=0.15)
        plt.plot(psd[1][2:], np.log(psd[0][2:]))
        plt.title("Log power spectrum of mean signal across mask")
        plt.xlabel("frequency (secs)")
        plt.ylabel("log power")
        plt.savefig(os.path.join(qadir, "meanpsd.png"), bbox_inches="tight")
        plt.close()

        plt.clf()
        plt.imshow(AJKZ, vmin=0, vmax=AJKZ_thresh)
        plt.xlabel("timepoints")
        plt.ylabel("slices")
        plt.title("Spike measure (absolute jackknife Z)")
        plt.savefig(os.path.join(qadir, "spike.png"), bbox_inches="tight")
        plt.close()

        if verbose:
            print("plotting volume data")
        qa.mk_slice_mosaic(
            voxmean,
            os.path.join(qadir, "voxmean.png"),
            "Image mean (with mask)",
            contourdata=maskdata,
        )
        qa.mk_slice_mosaic(voxcv, os.path.join(qadir, "voxcv.png"), "Image CV")
        qa.mk_slice_mosaic(voxsfnr, os.path.join(qadir, "voxsfnr.png"), "Image SFNR")

        if verbose:
            print("creating report")
        qa.mk_report(infile, qadir, datavars)

    if verbose:
        print("writing QA data")
    datafile = os.path.join(qadir, "qadata.csv")
    f = open(datafile, "w")
    f.write("SNR,%f\n" % np.mean(datavars["imgsnr"]))
    f.write("SFNR,%f\n" % datavars["meansfnr"])
    f.write("nspikes,%d\n" % len(datavars["spikes"]))
    f.write("nscrub,%d\n" % len(datavars["badvols"]))
    f.close()

    if save_sfnr:
        print("writing sfnr image")
        sfnrimg = nib.Nifti1Image(voxsfnr, img.affine)
        sfnrimg.to_filename(os.path.join(qadir, "voxsfnr.nii.gz"))
    return qadir


if __name__ == "__main__":
    main()
