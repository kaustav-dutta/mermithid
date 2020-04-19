'''
Miscellaneous functions for CRES conversions
Author: C. Claessens
Date:4/19/2020
'''

from __future__ import absolute_import

import numpy as np

from morpho.utilities import morphologging
logger = morphologging.getLogger(__name__)

from mermithid.misc.Constants import *

def Frequency(E, B):
    """
    Conversion functions (e.g. energy to frequency)
    """
    emass = m_electron()*e()/(c()**2)#constants.electron_mass/constants.e*constants.c**2
    gamma = E/(m_electron())+1
    return (e()*B)/(2.0*np.pi*emass) * 1/gamma
