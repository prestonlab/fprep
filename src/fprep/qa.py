"""Quality assurance tools from fmriqa."""

import os
import time
import numpy as np
import matplotlib.pyplot as plt
import statsmodels.api as sm
from reportlab.pdfgen import canvas


def compute_fd(motpars):
    # compute absolute displacement
    dmotpars = np.zeros(motpars.shape)

    dmotpars[1:, :] = np.abs(motpars[1:, :] - motpars[:-1, :])

    # convert rotation to displacement on a 50 mm sphere
    # mcflirt returns rotation in radians
    # from Jonathan Power:
    # The conversion is simple - you just want the length of an arc that a rotational
    # displacement causes at some radius. Circumference is pi*diameter, and we used a 5
    # 0 mm radius. Multiply that circumference by (degrees/360) or (radians/2*pi) to get the
    # length of the arc produced by a rotation.

    headradius = 50
    disp = dmotpars.copy()
    disp[:, 0:3] = np.pi * headradius * 2 * (disp[:, 0:3] / (2 * np.pi))

    FD = np.sum(disp, 1)
    return FD


def mk_slice_mosaic(
    imgdata, outfile, title, contourdata=None, ncols=6, colorbar=True, verbose=False
):
    if imgdata.shape[0] == imgdata.shape[1] == imgdata.shape[2]:
        min_dim = 2
    else:
        min_dim = np.where(np.min(imgdata.shape[0:3]) == imgdata.shape[0:3])[0][0]
        slice_dims = np.where(np.min(imgdata.shape[0:3]) != imgdata.shape[0:3])[0]
        if verbose:
            print("min_dim:", min_dim)
            print("slice_dim:", slice_dims)

    nrows = int(np.ceil(np.float(imgdata.shape[min_dim]) / ncols))
    mosaic = np.zeros(
        (nrows * imgdata.shape[slice_dims[0]], ncols * imgdata.shape[slice_dims[1]])
    )
    if contourdata is not None:
        contourmosaic = np.zeros(
            (nrows * imgdata.shape[slice_dims[0]], ncols * imgdata.shape[slice_dims[1]])
        )
    ctr = 0
    if verbose:
        print(mosaic.shape)

    for row in range(nrows):
        rowstart = row * imgdata.shape[slice_dims[0]]
        rowend = (row + 1) * imgdata.shape[slice_dims[0]]
        for col in range(ncols):
            if ctr < imgdata.shape[min_dim]:
                colstart = col * imgdata.shape[slice_dims[1]]
                colend = (col + 1) * imgdata.shape[slice_dims[1]]
                if verbose:
                    print(rowstart, rowend, colstart, colend)
                if min_dim == 0:
                    imgslice = imgdata[ctr, :, ::-1].T
                    if contourdata is not None:
                        contourslice = contourdata[ctr, :, ::-1].T
                elif min_dim == 1:
                    imgslice = imgdata[:, ctr, ::-1].T
                    if contourdata is not None:
                        contourslice = contourdata[:, ctr, ::-1].T
                elif min_dim == 2:
                    imgslice = imgdata[:, ::-1, ctr].T
                    if contourdata is not None:
                        contourslice = contourdata[:, ::-1, ctr].T
                if verbose:
                    print(imgslice.shape)
                try:
                    mosaic[rowstart:rowend, colstart:colend] = imgslice
                except:
                    mosaic[rowstart:rowend, colstart:colend] = imgslice.T

                if contourdata is not None:
                    try:
                        contourmosaic[rowstart:rowend, colstart:colend] = contourslice
                    except:
                        contourmosaic[rowstart:rowend, colstart:colend] = contourslice.T
                ctr += 1

    plt.figure(figsize=(8, 8))
    plt.imshow(mosaic, cmap=plt.cm.gray)
    if not title == "":
        plt.title(title)
    if colorbar:
        plt.colorbar()
    if contourdata is not None:
        plt.contour(contourmosaic, colors="red")
    plt.savefig(outfile, bbox_inches="tight")
    plt.close()


def plot_timeseries(
    data,
    title,
    outfile,
    markers=None,
    markername=None,
    plottrend=False,
    ylims=None,
    plotline=None,
    xlabel="timepoints",
    ylabel=None,
):
    fig = plt.figure(figsize=[10, 3])
    fig.subplots_adjust(bottom=0.15)
    plt.plot(data)
    datarange = np.abs(np.max(data) - np.min(data))
    ntp = len(data)

    if ylims is None:
        axislims = [
            0,
            ntp + 1,
            np.min(data) - datarange * 0.1,
            np.max(data) + datarange * 0.1,
        ]
    else:
        axislims = [0, ntp - 1, ylims[0], ylims[1]]

    if plottrend:
        X = np.vstack(
            (
                np.ones(ntp),
                np.arange(ntp) - np.mean(np.arange(ntp)),
                np.arange(ntp) ** 2 - np.mean(np.arange(ntp) ** 2),
            )
        ).T
        model = sm.OLS(data, X)
        results = model.fit()

    plt.axis(axislims)
    if markers is not None:
        for s in markers:
            (lp,) = plt.plot([s, s], axislims[2:4], linewidth=2, color="red")
        plt.legend([lp], [markername])
    if plottrend:
        plt.plot(np.dot(X, results.params), color="black")
    if plotline:
        plt.plot([0, ntp], [plotline, plotline])

    if title is not None:
        plt.title(title)
    if xlabel is not None:
        plt.xlabel(xlabel)
    if ylabel is not None:
        plt.ylabel(ylabel)
    plt.savefig(outfile, bbox_inches="tight")
    plt.close()

    if plottrend:
        return results
    else:
        return []


def MAD(a, c=0.6745, axis=0):
    """
    Median Absolute Deviation along given axis of an array:

    median(abs(a - median(a))) / c

    c = 0.6745 is the constant to convert from MAD to std; it is used by
    default

    from http://code.google.com/p/agpy/source/browse/trunk/agpy/mad.py?r=206
    """
    good = a == a
    a = np.asarray(a, np.float64)
    if a.ndim == 1:
        d = np.median(a[good])
        m = np.median(np.fabs(a[good] - d) / c)
    else:
        d = np.median(a[good], axis=axis)
        # I don't want the array to change so I have to copy it?
        if axis > 0:
            aswp = np.swapaxes(a[good], 0, axis)
        else:
            aswp = a[good]
        m = np.median(np.fabs(aswp - d) / c, axis=0)
    return m


def mk_report(infile, qadir, datavars):
    timestamp = time.strftime("%B %d, %Y: %H:%M:%S")

    report_header = []
    report_header.append("QA Report: %s" % timestamp)
    report_header.append("infile: %s" % infile)
    report_header.append("Mean SNR: %f" % np.mean(datavars["imgsnr"]))
    report_header.append("Mean SFNR (in brain mask): %f" % datavars["meansfnr"])
    report_header.append(
        "Drift term: %f (p=%f)"
        % (datavars["trend"].params[1], datavars["trend"].pvalues[1])
    )
    report_header.append("# potential spikes: %d" % len(datavars["spikes"]))
    report_header.append(
        "# timepoints exceeding FD threshold: %d" % len(datavars["badvols"])
    )

    c = canvas.Canvas(os.path.join(qadir, "QA_report.pdf"))
    yloc = 820
    stepsize = 16
    for line in report_header:
        c.drawString(10, yloc, line)
        yloc = yloc - stepsize

    timeseries_to_draw = [
        "maskmean.png",
        "meanpsd.png",
        "mad.png",
        "DVARS.png",
        "fd.png",
    ]

    tsfiles = [os.path.join(qadir, t) for t in timeseries_to_draw]

    ts_img_size = [467, 140]
    yloc = yloc - ts_img_size[1]

    for imfile in tsfiles:
        c.drawImage(imfile, 45, yloc, width=ts_img_size[0], height=ts_img_size[1])
        yloc = yloc - ts_img_size[1]

    c.showPage()

    yloc = 650
    c.drawImage(os.path.join(qadir, "spike.png"), 20, yloc, width=500, height=133)
    yloc = 330
    images_to_draw = ["voxmean.png", "voxsfnr.png", "voxcv.png"]
    imfiles = [os.path.join(qadir, t) for t in images_to_draw]
    c.drawImage(imfiles[0], 0, yloc, width=300, height=300)
    c.drawImage(imfiles[1], 300, yloc, width=300, height=300)
    yloc = 20
    c.drawImage(imfiles[2], 0, yloc, width=325, height=325)

    c.save()
