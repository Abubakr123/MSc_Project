#!/usr/bin/python

# written in python2.7

import argparse
import os
import sys
import numpy as np
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt

last_modified = "07 July 2021"

def calc_structure_function(MJD, DM, DMunc=None, verbosity=0, tau_zero=7, tau_incr=1.2):
    """
    calculate structure function for given DM time series
    derive uncertainties from propagated DM uncertainties when given
    """
    Nobs = len(MJD)
    Npair = (Nobs*Nobs - Nobs) / 2
    length = np.max(MJD) - np.min(MJD)
    if verbosity > -1:
        print("total length of dataset:         %d days" % int(length))
        print("total number of DM measurements: %d" % Nobs)
        print("total number of pairs:           %d" % Npair)
        print("")

    # prepare pre-allocated arrays, much faster than np.append,
    # and slightly faster than creating a list and converting afterwards
    DeltaMJD = np.zeros(Npair)
    DeltaDMsq = np.zeros(Npair)
    if not DMunc is None: DeltaDMw = np.zeros(Npair)

    # calculate pairs
    ipair = 0
    for ii in range(Nobs):
        for jj in range(ii+1,Nobs):
            DeltaMJD[ipair] = MJD[jj] - MJD[ii]
            DeltaDMsq[ipair] = (DM[jj] - DM[ii]) ** 2
            if not DMunc is None: DeltaDMw[ipair] = 1/(DMunc[ii]*DMunc[ii] + DMunc[jj]*DMunc[jj])
            ipair += 1

    # calculate sf values
    result_tau = []
    result_sf = []
    if not DMunc is None: result_sfunc = []
    result_npair = []
    tau = tau_zero
    while tau < length:
        # calculate the binning range
        tau_min = tau / np.sqrt(tau_incr)
        tau_max = tau * np.sqrt(tau_incr)
        # get relevant measurements
        indices = np.logical_and(DeltaMJD >= tau_min, DeltaMJD < tau_max)
        npair = np.count_nonzero(indices)
        if npair == 0:
            tau *= tau_incr
            continue
        # calculate sf value for tau (weighted average of DeltaDM^2)
        if not DMunc is None:
            sf, sum_weights = np.average(DeltaDMsq[indices], weights=DeltaDMw[indices], returned=True)
            # gaussian error propagation, including choice of weights:
            sf_unc = 2 * np.sqrt(sf / sum_weights)
        else:
            sf = np.average(DeltaDMsq[indices])
    
        # save
        result_tau.append(tau)
        result_sf.append(sf)
        if not DMunc is None: result_sfunc.append(sf_unc)
        result_npair.append(npair)

        tau *= tau_incr

    # only transform to array now, because at start the final length is not known
    # (because for some tau values n_pair is zero)
    if not DMunc is None:
        return np.array(result_tau), np.array(result_sf), np.array(result_sfunc), np.array(result_npair)
    else:
        return np.array(result_tau), np.array(result_sf), None, np.array(result_npair)

def prewhiten_time_series(y, sig):
    rr = range(1,len(y))
    deltas = [y[ii] - y[ii-1] for ii in rr]
    if not sig is None:
        sigmas = [np.sqrt(sig[ii]**2 + sig[ii-1]**2) for ii in rr]
    else:
        sigmas = None
    return deltas, sigmas

def get_white_noise_structure_function_amplitude(MJD, DM, DMunc, plot=False):
    """
    calculate the structure function of the white noise of a DM time series
    applies pre-whitening by forming the difference between subsequent DM measurements
    """
    delta, sigma = prewhiten_time_series(DM, DMunc)
    tau, sf, sfunc, npair = calc_structure_function(MJD[1:], delta, DMunc=sigma, verbosity=-1)
    # sf can go up at long lags, only use half
    maxtau = len(sf) / 2
    # factor of 2 because we take the difference of the DM values, which increases the noise
    white = 10**np.average(np.log10(sf[:maxtau])) / 2
    #white = np.average(sf[:maxtau]) / 2
    # these weights overweight very low values, even with uncertainties greater than the value
    #white = np.average(sf[:maxtau],weights=1/sfunc[:maxtau]**2) / 2

    if plot:
        fig, ax = plt.subplots()
        plt.errorbar(tau,sf,yerr=sfunc,fmt="b+")
        ax.plot(tau[:maxtau],2*white*np.ones(maxtau),"b-")
        show_plot_sf("structure function of pre-whitened DM time series for white noise estimation")

    return white

def resample_data(x, y, xn):
    """
    resample the input data (e.g. time series) to different x samples
    by interpolating between the true DM values
    requires the data to be sorted in x
    """
    Nold = len(x)
    Nnew = len(xn)
    yn = np.zeros(Nnew)
    iold = 1
    for inew in range(Nnew): 
        while x[iold] < xn[inew] and iold < Nold - 1:
            iold += 1
        yn[inew] = y[iold-1] + (y[iold]-y[iold-1])/(x[iold]-x[iold-1]) * (xn[inew]-x[iold-1])

    return yn

def resample_data_regular(x, y, sampling=3.5):
    """
    resample the input data (e.g. time series) to regularly spaced samples
    by interpolating between the y values
    useful to calculate a power spectrum as FFT requires regular samples
    requires the data to be sorted in x
    """
    xn = np.arange(x[0], x[-1], sampling)
    yn = resample_data(x, y, xn)
    return xn, yn

def calc_DM_power_spectrum(MJD, DM, sampling=3.5):
    """
    calculate the power spectrum for a given DM time series
    requires the data to be sorted by MJD
    """
    mjd, dm = resample_data_regular(MJD, DM, sampling=sampling)
    mjdfft = np.fft.fftfreq(len(mjd)) / sampling
    dmfft = np.fft.fft(dm)
    power = np.real(dmfft)**2 + np.imag(dmfft)**2

    # element 0 is for zero frequency, and the latter half is for negative frequencies (symmertic around 0)
    maxfreq = len(mjdfft) / 2

    return mjdfft[1:maxfreq], power[1:maxfreq]

def get_white_noise_power_spectrum_amplitude(DMunc):
    """
    calculate the white noise of the power spectrum from simulations based on the DM uncertainties
    """
    Nsim = 10
    results = np.zeros(Nsim)
    for ii in range(Nsim):
        N = len(DMunc)
        fft = np.fft.fft(DMunc * np.random.randn(N))
        power = np.real(fft)**2 + np.imag(fft)**2
        mean = np.average(power[1:N/2])
        results[ii] = mean / N
    return np.median(results)

def power_law(x, ampl, power, white, prewhitened=False):
    if prewhitened:
        return ampl * x ** (power+2) + white * x ** 2
    else:
        return ampl * x ** power + white

def fit_power_spectrum(freqs, powers, expo=None, white=None, prewhitened=False):
    """
    fit a model to a power spectrum
    if no exponent is given, it will be fit for
    if no white noise level is given, it will be fit for

    fitting to log10 of the powers, because of the large dynamic range
    """
    # weight by 1/freq, because sampling increases linearly in log(freqs), sigma = 1/sqrt(weight)
    #sigmas = freqs**.5
    # put uniform weights on the frequencies
    sigmas = np.ones(len(powers))
    # weight by another factor of 2**log10(powers),
    # i.e. double weight for 1 order of magnitude more power
    sigmas /= np.sqrt(2**np.log10(powers))
    with np.errstate(invalid='ignore'): # ignore invalid values for log10 in curve_fit
        if not expo is None and not white is None:
            popt, pcov = curve_fit(lambda x,a: np.log10(power_law(x,a,expo,white,prewhitened=prewhitened)),
                                   freqs, np.log10(powers), sigma=sigmas, p0 = [1e-10])
        elif expo is None and not white is None:
            popt, pcov = curve_fit(lambda x,a,e: np.log10(power_law(x,a,e,white,prewhitened=prewhitened)),
                                   freqs, np.log10(powers), sigma=sigmas, p0 = [1e-10, -1])
            expo = popt[1]
        elif expo is not None and white is None:
            popt, pcov = curve_fit(lambda x,a,w: np.log10(power_law(x,a,expo,w,prewhitened=prewhitened)),
                                   freqs, np.log10(powers), sigma=sigmas, p0 = [1e-10, 1e-5])
            white = popt[1]
        else:
            popt, pcov = curve_fit(lambda x,a,e,w: np.log10(power_law(x,a,e,w,prewhitened=prewhitened)),
                                   freqs, np.log10(powers), sigma=sigmas, p0 = [1e-10, -1, 1e-5])
            expo = popt[1]
            white = popt[2]
        ampl = popt[0]

    return ampl, expo, white

def show_plot_DM(title):
    plt.grid()
    plt.title(title)
    plt.xlabel('MJD')
    plt.ylabel('DM (pc/cm^3)')
    plt.show()

def show_plot_sf(title):
    plt.grid()
    plt.xscale('log')
    plt.yscale('log')
    plt.title(title)
    plt.xlabel('time lag tau (days)')
    plt.ylabel('structure function D_DM(tau) (pc^2/cm^6)')
    plt.show()

def show_plot_ps(title):
    plt.grid()
    plt.xscale('log')
    plt.yscale('log')
    plt.title(title)
    plt.xlabel('spectral frequency (1/days)')
    plt.ylabel('power spectral density (pc^2/cm^6)')
    plt.show()

def calc_sf_monte_carlo(MJD, DM, DMunc=None, sampling=3.5, n_iter=100, tau_zero=7, tau_incr=1.2, prewhiten=True,
                        verbosity=0, plot=False, model="kolm+white", amodel="fit_sf", sim_white=False):
    """
    calculate the structure function of a DM time series
    estimate uncertainties of the SF red noise via simulations
    requires the data to be sorted by MJD
    """
    # overwrite options
    if sim_white and amodel == "fit_sf": amodel="int_power"
    if DMunc is None: sim_white = False

    # calculate "true" structure function first
    tau, sf, sfunc, npair = calc_structure_function(MJD, DM, DMunc=DMunc, verbosity=verbosity,
                                                    tau_zero=tau_zero, tau_incr=tau_incr)
    # get power spectrum of resampled DM time series
    mjd, dm = resample_data_regular(MJD, DM, sampling=sampling)
    if prewhiten:
        # apply a first difference filter to the time series, discard last mjd to get len(mjd) = len(dm) again
        mjd = mjd[:-1]
        dm = np.diff(dm)
    Nsample = len(mjd)
    mjdfft = np.fft.fftfreq(Nsample) / sampling
    dmfft = np.fft.fft(dm)
    power = np.real(dmfft)**2 + np.imag(dmfft)**2
    # as highest frequencies are oversampled(!!), ignore them in fit to not corrupt white noise estimate
    # highest frequency in mjdfft corresponds to 2*sampling
    # (currently not actually fitting white noise)
    Ndata = len(MJD)
    sampling_data = (MJD[-1] - MJD[0]) / Ndata
    maxfitfreq = int((Nsample/2) * np.min([.5,2*sampling / sampling_data]))
    fitrange = range(1,maxfitfreq)
    if verbosity > 0:
        print("total number of re-sampled DM measurements: %d" % Nsample)
        print("data are sampled on average every %.2f days. resampled to %.2f days" % (sampling_data, sampling))
        print("maximum spectral frequency in power spectrum fit: 1 / %.2f" % (1 / mjdfft[maxfitfreq]))
        print("")

        # test if DM time series can be recovered
        if plot:
            fig, ax = plt.subplots()
            if prewhiten:
                plotDM, plotDMunc = prewhiten_time_series(DM,DMunc)
                ax.errorbar(MJD[:-1],plotDM,yerr=plotDMunc,fmt="b+")
            else:
                ax.errorbar(MJD,DM,yerr=DMunc,fmt="b+")
            ax.plot(mjd,dm,"r-")
            show_plot_DM("comparison of true DM time series and resampled DM time series")

    if prewhiten:
        # now post-darken/redden the spectrum
        # the first difference filter has a power transfer function of 4(sin pi f)^2
        # *sampling because frequencies were divided by sampling
        power_transfer_function = 4*np.sin(np.pi * mjdfft[1:]*sampling)**2
        power[1:] /= power_transfer_function
        if False and verbosity > 0 and plot:
            plt.plot(mjdfft[1:Nsample/2],power_transfer_function[:Nsample/2 - 1])
            show_plot_ps("power transfer function")

    ################################
    ### model the power spectrum ###
    ################################
    # calculate white noise from DM uncertainties
    # fitting could cause significant misestimation, e.g. because of low power in overampled regime
    if not DMunc is None:
        white_true = get_white_noise_power_spectrum_amplitude(DMunc) * Nsample
    else:
        white_true = 0
    if verbosity > 0:
        print("simulating white noise from DM uncertainties (if given)")
        print("simulated white noise power spectrum amplitude: %.2e" % white_true)
        print("")
    
    # now fit the power spectrum
    white = 0 if model == "kolm" or model == "power" else white_true
    expo = -8./3 if model == "kolm" or model == "kolm+white" else None
    if amodel == "fit_power" or model == "power" or model == "power+white":
        ampl, expo, white = fit_power_spectrum(mjdfft[fitrange], power[fitrange], expo=expo, white=white)
    if amodel == "int_power" or amodel == "fit_sf":
        # sum entire power in power spectrum and make fit match it
        # in the case of fit_sf, this is just used as an initial estimate
        ampl = (np.sum(power[fitrange]) - len(fitrange)*white) / np.sum(mjdfft[fitrange]**expo)
        if ampl < 0:
            ampl, expo, white = fit_power_spectrum(mjdfft[fitrange], power[fitrange], expo=expo, white=white)
            if verbosity > -1:
                print("warning: calculated power spectrum amplitude was below 0, fitting instead ...")
                print("")
    if amodel == "match_lowest_freq":
        ampl = (power[1] - white) / mjdfft[1]**expo
    if ampl < 0:
        if verbosity > -1:
            print("warning: final power spectrum amplitude was below 0, taking its absolute value instead ...")
            print("")
        ampl = -ampl
    if verbosity > 0:
        power_fit = power_law(mjdfft[fitrange], ampl, expo, white)
        print("power spectrum fit (amplitude model = %s):" % ("int_power (later fit_sf)" if amodel == "fit_sf" else amodel))
        print("power = %.2e * freq ^ %.2f + %.2e" % (ampl,expo,white))
        print("integrated power: %.2e" % np.sum(power[fitrange]))
        print("model int power:  %.2e (%.2e of which is white noise)" % (np.sum(power_fit), len(fitrange)*white))
        print("")
        if plot:
            fig, ax = plt.subplots()
            ax.plot(mjdfft[1:Nsample/2],power[1:Nsample/2],"b-",
                    mjdfft[fitrange],power_fit,"r-",
                    mjdfft[fitrange],white_true * np.ones(len(fitrange)),"k-")
            ax.axvline(x=1/365.25,c="k",linestyle="--")
            show_plot_ps('fit of the power spectral density')

    # extend power spectrum to get extended DM time series (n_iter times longer)
    # rescale amplitude: N times more power when dataset is N times as long
    # ignore white noise as it does not properly simulate into the SF anyways (resampling...)
    ampl *= n_iter
    white *= n_iter
    fmin = mjdfft[1] / n_iter
    freqs = np.array([fmin*ii for ii in range(1,1 + n_iter*Nsample/2)])
    fouriers = power_law(freqs, ampl, expo, 0)**.5 * np.exp(1j * 2*np.pi * np.random.rand(n_iter*Nsample/2))
    #freqs_full = np.concatenate(([0],freqs,-freqs[::-1])) # not used
    fouriers_full = np.concatenate(([0],fouriers,fouriers[::-1]))

    # now produce extended DM time series (n_iter times longer)
    # THIS STEP CAN TAKE VERY MUCH TIME DEPENDING ON NUMER OF SAMPLES
    # (this could be fixed by intelligently increasing the length of the fake dataset)
    DMfake_long = np.real(np.fft.ifft(fouriers_full))
    if verbosity > 0:
        print("total number of simulated DM samples: %d" % len(DMfake_long))
        print("")
        if plot:
            plt.plot(sampling * np.arange(2*Nsample), DMfake_long[:2*Nsample], "b-")
            show_plot_DM("simulated DM time series (twice as long as initial)")

    # now use fake time series to calculate simulated structure functions
    sffake = np.zeros((n_iter,len(tau)))
    for ii in range(n_iter):
        DMfake = resample_data(mjd, DMfake_long[ii*Nsample:(ii+1)*Nsample], MJD)
        if sim_white:
            DMfake += DMunc * np.random.randn(Ndata)
        # jN: junk (unused information)
        j1, sffake[ii], j2, j3 = calc_structure_function(MJD, DMfake, verbosity=-1,
                                                         tau_zero=tau_zero, tau_incr=tau_incr)
        if verbosity > -1 and ii in [0,1,2,4,9,49,99,499,999,4999,n_iter-1]:
            print("finished simulation %d out of %d" % (ii+1,n_iter))
            if verbosity > 0 and plot:
                plt.plot(MJD,DMfake - np.average(DMfake))
                show_plot_DM("simulated DM time series #%d" % (ii+1))
                fig, ax = plt.subplots()
                ax.errorbar(tau,sf,yerr=sfunc,fmt="b+")
                ax.plot(tau,sffake[ii],"r-")
                show_plot_sf("structure function of the simulated DM time series #%d" % (ii+1))

    if verbosity > -1:
        print("")
        print("finished all simulations!")
        print("")

    # now calculate range of sf
    sffake_sort = np.sort(sffake,axis=0)
    sf_sim = sffake_sort[n_iter / 2]
    sf_sim_up = sffake_sort[n_iter * 84 / 100]
    sf_sim_low = sffake_sort[n_iter * 16 / 100]

    if not sim_white:
        # calculate sf white noise
        # from median DM uncertainty
        if not DMunc is None:
            w1 = 2*np.median(DMunc)**2
        else:
            w1 = 0
        # from prwhitened DM time series SF
        w2 = get_white_noise_structure_function_amplitude(MJD,DM,DMunc,plot=(plot and verbosity > 0))
        # from fit to SF (fit in log space)
        # --- only fit up to the point where the sf is defenitely increasing (i.e. in power law regime)
        n_subsequent = 0
        for itau in range(1,len(tau)):
            if (sfunc is None and sf[itau] > sf[itau-1]) or (not sfunc is None and (sf[itau] - sf[itau-1]) / sfunc[itau] > 3):
                n_subsequent += 1
                if n_subsequent >= 3:
                    break
            else:
                n_subsequent = 0
        with np.errstate(invalid='ignore'): # ignore invalid values for log10 in curve_fit
            popt, pcov = curve_fit(lambda x,a,c: np.log10(a*x**(-1-expo)+c),
                                   tau[:itau], np.log10(sf[:itau]), p0 = [1e-10, 1e-8])
        w3 = popt[1]
        if verbosity > 0 and plot:
            fig, ax = plt.subplots()
            ax.plot(tau,sf,"b-",tau,popt[0]*tau**(5./3)+popt[1],"g-",
                    tau,w3*np.ones(len(tau)),"k-")
            ax.axvline(x=tau[itau],c="k",linestyle="--")
            show_plot_sf("fit of the sf noise level (up to the dashed line)")

        # choice of sf white noise estimation method: if fit went wrong, use DM uncertainties
        if w3 < 0:
            w = w1
        else:
            w = w3

    # if requested, fit amplitude of structure function
    # -- disabled when simulating white noise as well because that would make the fitting more difficult
    if amodel == "fit_sf":
        # uncertainties in log space
        sigmas_red = (np.log10(sf_sim_up/sf_sim) + np.log10(sf_sim/sf_sim_low))/2
        if not DMunc is None:
            sigmas_white = np.log10((sf+sfunc)/sf) # don't consider lower boundary because it can go below 0
        else:
            sigmas_white = 0
        with np.errstate(invalid='ignore'): # ignore invalid values for log10 in curve_fit
            # fit power law to model (no white noise)
            popt, pcov = curve_fit(lambda x,a: np.log10(a*x**(-1-expo)), tau, np.log10(sf_sim), p0 = [1e-10],
                                   sigma=sigmas_red)
            # fit power law + white noise to data
            model_ampl = popt[0]
            popt, pcov = curve_fit(lambda x,a: np.log10(a*x**(-1-expo)+w), tau, np.log10(sf), p0 = [1e-10],
                                   sigma=(sigmas_red**2 + sigmas_white**2)**.5)
            data_ampl = popt[0]
        if verbosity > 0:
            print("fit of the structure function red noise amplitude (to rescale the model)")
            print("data:  %.2e" % data_ampl)
            print("model: %.2e" % model_ampl)
            print("")
            if plot:
                fig, ax = plt.subplots()
                ax.errorbar(tau,sf,yerr=sfunc,fmt="b+")
                ax.plot(tau,sf_sim,"g-",
                        tau,model_ampl * tau ** (-1-expo),"k-",
                        tau,data_ampl * tau ** (-1-expo) + w,"k-")
                show_plot_sf("red noise amplitude fits to data and model")
        if data_ampl < 0:
            ddm1 = model_ampl
            if verbosity > -1:
                print("warning: not rescaling structure function amplitude to negative value from fit!")
                print("")
        else:
            ddm1 = data_ampl
            sf_sim *= data_ampl / model_ampl
            sf_sim_low *= data_ampl / model_ampl
            sf_sim_up *= data_ampl / model_ampl

        if verbosity > 0:
            print("estimated white noise level...")
            print(" ... from median DM uncertainty:           %.2e" % w1)
            print(" ... from prewhitened DM time series SF:   %.2e" % w2)
            print(" ... from fit to log(SF) up to %d days:   %.2e" % (int(tau[itau]), w3))
            print("using white noise level = %.2e" % w)
            print("")

    if sim_white:
        return tau, sf, sfunc, npair, sf_sim, sf_sim_low, sf_sim_up, ddm1
    else:
        return tau, sf, sfunc, npair, sf_sim + w, sf_sim_low + w, sf_sim_up + w, ddm1, w

def detrend_time_series(MJD, DM, DMunc=None):
    popt, pcov = curve_fit(lambda x,a,b: a*(x-MJD[0])+b, MJD, DM,
                           sigma=DMunc, p0 = [1e-6, DM[0]])
    return DM - popt[0]*(MJD-MJD[0]) - popt[1]

def existing_file(filename):
    """
    check if 'filename' is an existing file (use for argparse: type=existing_file)
    """
    if not(os.path.exists(filename) and os.path.isfile(filename)):
        raise argparse.ArgumentTypeError(filename+" is not an existing file!")
    return filename

def pos_int(i):
    val = int(i)
    if val <= 0:
        raise argparse.ArgumentTypeError("%s is not a positive integer!" % i)
    return val

def pos_float(f):
    val = float(f)
    if val <= 0:
        raise argparse.ArgumentTypeError("%s is not a positive float!" % f)
    return val

def incr_float(f):
    val = float(f)
    if val <= 1:
        raise argparse.ArgumentTypeError("%s is not greater than 1!" % f)
    return val

def parse_cmdl():
    """
    parse the command line arguments when this code is used directly from the command line
    """
    parser = argparse.ArgumentParser(description='Calculate the structure function of a DM time series.\n'+
                                     'Written by Julian Donner. Last modified: ' + last_modified + '.\n' +
                                     'Note: The FFT before the simulation can sometimes very long, ' + 
                                     'in cases with very unlucky numbers of samples.',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    verbosity_group = parser.add_mutually_exclusive_group()
    verbosity_group.add_argument('-v','--verbose',help='print more stuff (and show more plots with "-p")',
                                 action='store_true')
    verbosity_group.add_argument('-q','--quiet',  help='print less stuff',action='store_true')
    parser.add_argument('DMfile',help='File that contains the DM time series.',type=existing_file)
    parser.add_argument('-o','--outfile',help='print result to file')
    parser.add_argument('-p','--plot',help='plot up results',action='store_true')
    parser.add_argument('-M','--mjdcol',help='specify MJD column',type=pos_int,default='1')
    parser.add_argument('-D','--dmcol',help='specify DM column',type=pos_int,default='2')
    parser.add_argument('-U','--dmunccol',help='specify DM uncertainty column',type=pos_int)
    parser.add_argument('-t','--tau_zero',help='minimum time lag tau',type=pos_float,default='7')
    parser.add_argument('-i','--tau_incr',help='multiplicative increment of time lag tau',type=incr_float,
                        default='1.2')
    parser.add_argument('-d','--detrend',help='subtract linear trend from input time series',
                        action='store_true')
    sim_group = parser.add_argument_group('red-noise uncertainty simulation')
    sim_group.add_argument('-s','--simulate',help='simulate red noise uncertainty',action='store_true')
    sim_group.add_argument('-m','--model',help='specify power-spectrum model for simulations',type=str,
                        choices=["kolm","power","kolm+white","power+white"],default='kolm+white')
    sim_group.add_argument('-a','--amplitude',help='specify how to estimate SF amplitude',type=str,
                        choices=["fit_power","int_power","fit_sf","match_lowest_freq"],default='fit_sf')
    sim_group.add_argument('-w','--sim_white',help='simulate DM white noise in SF simulations.\n'+
                        'Replaces "-a fit_sf" by "-a int_power".',action='store_true')
    sim_group.add_argument('-n','--n_iter',help='number of simulation iterations',type=pos_int,default=100)
    sim_group.add_argument('--no-prewhiten',help='do not pre-whiten DM time series',action='store_true')
    parser.add_argument('--demo',help='demonstrate a few effects and exit',action='store_true')

    args = parser.parse_args()
    args.verbosity = args.verbose - args.quiet

    return args

if __name__ == "__main__":
    # parse the command line
    args = parse_cmdl()

    # demo mode -- run demo and exit
    if args.demo:
        import jd_calc_sf_demo
        jd_calc_sf_demo.demonstrate_spectral_leakage()
        sys.exit()

    # read in data
    if args.dmunccol:
        Data = np.loadtxt(args.DMfile, comments="#", usecols=(args.mjdcol-1,args.dmcol-1,args.dmunccol-1))
    else:
        Data = np.loadtxt(args.DMfile, comments="#", usecols=(args.mjdcol-1,args.dmcol-1))
        DMunc = None
    nDMload = Data.shape[0]
    Data = Data[Data[:,0].argsort()] # (sort by MJD)
    MJD = Data[:,0]
    DM = Data[:,1]
    if args.dmunccol:
        DMunc = Data[:,2]
        med_DM_unc = np.median(Data[:,2])
        Data = Data[Data[:,2] < 3*med_DM_unc] # (reject uncertain points)
    nDM = Data.shape[0]
    if args.verbosity > -1:
        print("")
        print("rejected %d out of %d DM measurements because of high uncertainty" %
              (nDMload - nDM, nDMload))
        print("")

    # detrend if requested
    if args.detrend:
        DM = detrend_time_series(MJD, DM, DMunc)

    if args.simulate:
        # calculate structure function with simulated red noise uncertainties
        tau, sf, sfunc, npair, sim, sim_low, sim_up, ddm1, w = calc_sf_monte_carlo(
            MJD, DM, DMunc=DMunc,
            model=args.model,
            amodel=args.amplitude,
            sim_white=args.sim_white,
            n_iter=args.n_iter,
            verbosity=args.verbosity,
            plot=args.plot,
            tau_zero=args.tau_zero,
            tau_incr=args.tau_incr,
            prewhiten=not(args.no_prewhiten)
        )
        
        # print to file
        if args.outfile != None:
            f = open(args.outfile,"w")
            if not args.sim_white and not sfunc is None:
                f.write("# simulations contain red noise only, the white noise is added as a constant\n")
                f.write("# white noise level: %.10e\n" % w)
            f.write("# model DDM(tau = 1d) = %.2e\n" % ddm1)
            f.write("#_tau D_DM sig(D_DM) n_pair sim sim_low sim_up\n")
            for ii in range(len(tau)):
                if not sfunc is None:
                    f.write("%.2f %.5e %.5e %d %.5e %.5e %.5e\n" %
                            (tau[ii], sf[ii], sfunc[ii], npair[ii], sim[ii], sim_low[ii], sim_up[ii]))
                else:
                    f.write("%.2f %.5e nan %d %.5e %.5e %.5e\n" %
                            (tau[ii], sf[ii], npair[ii], sim[ii], sim_low[ii], sim_up[ii]))
                    
        # plot
        if args.plot:
            fig, ax = plt.subplots()
            ax.errorbar(tau,sf,yerr=sfunc,fmt="b+")
            ax.plot(tau,sim,"k-",tau,sim_low,"k-",tau,sim_up,"k-")
            ax.axvline(x=365.25,c="k",linestyle="--")
            plt.savefig("SF_Kolm_%s.png" % args.DMfile)
            show_plot_sf("structure function of the DM time series and Kolmogorov simulation")

    else:
        # calculate structure function from DM time series only
        tau, sf, sfunc, npair = calc_structure_function(MJD, DM, DMunc=DMunc,
                                                        verbosity=args.verbosity,
                                                        tau_zero=args.tau_zero,
                                                        tau_incr=args.tau_incr)
        # print to file
        if args.outfile != None:
            f = open(args.outfile,"w")
            f.write("#_tau D_DM sig(D_DM) n_pair\n")
            for ii in range(len(tau)):
                if not sfunc is None:
                    f.write("%.2f %.5e %.5e %d\n" % (tau[ii], sf[ii], sfunc[ii], npair[ii]))
                else:
                    f.write("%.2f %.5e nan %d\n" % (tau[ii], sf[ii], npair[ii]))
        
        # plot
        if args.plot:
            plt.errorbar(tau,sf,fmt='+',yerr=sfunc)
            plt.savefig("SF_%s.png" % args.DMfile)
            show_plot_sf("structure function of the DM time series %s" % args.DMfile)
