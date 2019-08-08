'''
This scripts aims at testing Tritium specific processors.
Author: A. Ziegler, C. Claessens
Date: Aug 31 2019
'''

import unittest

from morpho.utilities import morphologging
logger = morphologging.getLogger(__name__)

from mermithid.processors.TritiumSpectrum import DistortedTritiumSpectrumLikelihoodSampler
from morpho.processors.plots import Histogram
from mermithid.misc.Constants import seconds_per_year, tritium_endpoint
from mermithid.misc import Constants

from ROOT import TH1F
from ROOT import TMath

from morpho.processors.sampling.PyStanSamplingProcessor import PyStanSamplingProcessor
from mermithid.processors.misc.EfficiencyCorrector import EfficiencyCorrector
from morpho.processors.plots.APosterioriDistribution import APosterioriDistribution

import matplotlib.pyplot as plt

def ProduceData(counts=10000):


    specGen_config = {
        "volume": 7e-6*1e-2, # [m3]
        "density": 3e17, # [1/m3]
        "duration": 1.*seconds_per_year()/12.*1, # [s]
        "neutrino_mass" :0, # [eV]
        "energy_window": [tritium_endpoint()-1e3,tritium_endpoint()+1e3], # [KEmin,KEmax]
        "frequency_window": [-100e6, +100e6], #[Fmin, Fmax]
        "energy_or_frequency": "frequency",
        # "energy_window": [0.,tritium_endpoint()+1e3], # [KEmin,KEmax]
        "background": 1e-6, # [counts/eV/s]
        "energy_resolution": 5,# [eV]
        "frequency_resolution": 50e3,# [Hz]
        "mode": "generate",
        "varName": "F",
        "iter": counts,
        "interestParams": ["F"],
        "fixedParams": {"m_nu": 0},
        "options": {"snr_efficiency": True, "channel_efficiency":False, "smearing": True},
        "snr_efficiency_coefficients": [-265.03357206889626, 6.693200670990694e-07, -5.795611253664308e-16, 1.5928835520798478e-25, 2.892234977030861e-35, -1.566210147698845e-44], #[-451719.97479592788, 5.2434404146607557e-05, -2.0285859980859651e-15, 2.6157820559434323e-26],
        "channel_central_frequency": 1400e6,
        "mixing_frequency": 24.5e9
    }
    """

    histo_plot = {
        "variables": ["F"],
        "n_bins_x": 100,
        "title": "spectrum",
        "range": [1320e6, 1480e6]
    }

    """
    specGen = DistortedTritiumSpectrumLikelihoodSampler("specGen")
    #histo = Histogram("histo")

    specGen.Configure(specGen_config)
    #histo.Configure(histo_plot)

    specGen.Run()
    tritium_data = specGen.data
    print('Number of events: {}'.format(len(tritium_data["F"])))
    #result_E = {"KE": specGen.Energy(tritium_data["F"])}
    #result_E["is_sample"] = tritium_data["is_sample"]


    #result_mixed = tritium_data
    #result_mixed["F"] = [f-24.5e9 for f in result_mixed["F"]]
    #histo.data = result_mixed
    #histo.Run()

    return tritium_data

def CorrectData(input_data, nbins = 100, F_min = 24.5e9 + 1320e6, F_max = 24.5e9 + 1480e6):

    effCorr_config = {
        "variables": "F",
        "range": [F_min, F_max],
        "n_bins_x": nbins,
        "title": "corrected_spectrum",
        "efficiency": "-265.03357206889626 + 6.693200670990694e-07*(x-24.5e9) + -5.795611253664308e-16*(x-24.5e9)^2 + 1.5928835520798478e-25*(x-24.5e9)^3 + 2.892234977030861e-35*(x-24.5e9)^4 + -1.566210147698845e-44*(x-24.5e9)^5",
        "mode": "binned",
        "asInteger": True

    }

    effCorr = EfficiencyCorrector("effCorr")
    effCorr.Configure(effCorr_config)

    histo = TH1F("histo", "histo", nbins, F_min, F_max)

    for val in input_data["F"]:
        histo.Fill(val)

    bin_centers = []
    counts = []

    for i in range(nbins):
        counts.append(int(histo.GetBinContent(i)))
        bin_centers.append(histo.GetBinCenter(i))

    binned_data = {"counts": counts, "bin_centers": bin_centers, "F": input_data["F"]}

    effCorr.data = binned_data
    effCorr.Run()

    corrected_E_data = {"KE": Energy(effCorr.corrected_data["bin_centers"])}
    corrected_E_data["N"] = effCorr.corrected_data["counts"]

    return corrected_E_data

def AnalyzeData(tritium_data, nbins=100, iterations=100, f_min = 24.5e9+1320e6, f_max = 24.5e9+1480e6, make_plots=False):

    KE_min = Energy(f_max)
    KE_max = Energy(f_min)

    energy_resolution_precision = 0.01
    energy_resolution = 10
    meanSigma = energy_resolution

    nCounts = len(tritium_data["KE"])
    #nbins_eff = len(efficiency_data["f"])

    # Gamma function: param alpha and beta
    # alpha and beta aren't the mean and std
    # mu = alpha/beta**2
    # sig = sqrt(alpha)/beta
    pystan_config = {
        "model_code": "/Users/ziegler/docker_share/stan_models/tritium_phase_II_analyzer.stan",
        "input_data": {
            "runtime": 1.*seconds_per_year()/12.,
            "KEmin": KE_min,
            "KEmax": KE_max,
            "sigma_alpha": 1./(energy_resolution_precision**2),
            "sigma_beta": 1/(energy_resolution_precision**2*meanSigma),
            "Q_ctr": tritium_endpoint(),
            "Q_std": 80.,
            # "A_s_alpha": 0.1,
            # "A_s_beta": 12000.,
            # "A_b_log_ctr": -16.1181,
            # "A_b_log_std": 1.1749,
            #        bkgd_frac_b: 3.3567
            "Nbins": nbins,
            "KE": tritium_data["KE"],
            "N": tritium_data["N"]
        },
        "iter": max(iterations, 10000),
        "warmup": 5000,
        "n_jobs": 1,
        "interestParams": ['Q', 'sigma', 'A', 'A_s', 'A_b'],
        "function_files_location": "/Users/ziegler/docker_share/stan_models"
    }

    pystanProcessor = PyStanSamplingProcessor("pystanProcessor")
    pystanProcessor.Configure(pystan_config)
    #pystanProcessor.data = tritium_data
    pystanProcessor.Run()
    sampling_result = pystanProcessor.results
    print(sampling_result.keys())

    if make_plots:
        plot_name = 'aposteriori_distribution_{}_{}_{}'.format(
            nCounts, energy_resolution, energy_resolution_precision)
        plot_Sampling(sampling_result, plot_name)

def Energy(f, B=None, Theta=None):
    #print(type(F))
    if B==None:
        B = 0.95777194923080811
    emass_kg = Constants.m_electron()*Constants.e()/(Constants.c()**2)
    if isinstance(f, list):
        gamma = [(Constants.e()*B)/(2.0*TMath.Pi()*emass_kg) * 1/(F) for F in f]
        return [(g -1)*Constants.m_electron() for g in gamma]
    else:
        gamma = (Constants.e()*B)/(2.0*TMath.Pi()*emass_kg) * 1/(f)
        return (gamma -1)*Constants.m_electron()


def plot_Sampling(data, name='aposteriori_distribution'):
    aposteriori_config = {
        "n_bins_x": 100,
        "n_bins_y": 100,
        "variables": ['Q', 'sigma', 'A', 'A_s', 'A_b'],
        "title": name,
        "output_path": "results"
    }
    aposterioriPlotter = APosterioriDistribution("posterioriDistrib")
    aposterioriPlotter.Configure(aposteriori_config)
    aposterioriPlotter.data = data
    aposterioriPlotter.Run()

def DoCombinedAnalysis():
    print("Generate fake distorted tritium data and test efficiency correction.")
    tritium_data = ProduceData()
    corrected_tritium_data = CorrectData(tritium_data)
    AnalyzeData(corrected_tritium_data, make_plots=True)
if __name__ == '__main__':

    DoCombinedAnalysis()