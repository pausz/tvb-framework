# -*- coding: utf-8 -*-
#
#
# TheVirtualBrain-Framework Package. This package holds all Data Management, and 
# Web-UI helpful to run brain-simulations. To use it, you also need do download
# TheVirtualBrain-Scientific Package (for simulators). See content of the
# documentation-folder for more details. See also http://www.thevirtualbrain.org
#
# (c) 2012-2013, Baycrest Centre for Geriatric Care ("Baycrest")
#
# This program is free software; you can redistribute it and/or modify it under 
# the terms of the GNU General Public License version 2 as published by the Free
# Software Foundation. This program is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of 
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public
# License for more details. You should have received a copy of the GNU General 
# Public License along with this program; if not, you can download it here
# http://www.gnu.org/licenses/old-licenses/gpl-2.0
#
#
#   CITATION:
# When using The Virtual Brain for scientific publications, please cite it as follows:
#
#   Paula Sanz Leon, Stuart A. Knock, M. Marmaduke Woodman, Lia Domide,
#   Jochen Mersmann, Anthony R. McIntosh, Viktor Jirsa (2013)
#       The Virtual Brain: a simulator of primate brain network dynamics.
#   Frontiers in Neuroinformatics (7:10. doi: 10.3389/fninf.2013.00010)
#
#

"""
Adapter that uses the traits module to generate interfaces for FFT Analyzer.

.. moduleauthor:: Lia Domide <lia.domide@codemart.ro>
.. moduleauthor:: Stuart A. Knock <Stuart@tvb.invalid>

"""
import psutil
import numpy
import math
from tvb.basic.config.settings import TVBSettings
import tvb.analyzers.fft as fft
import tvb.core.adapters.abcadapter as abcadapter
import tvb.basic.filters.chain as entities_filter
import tvb.datatypes.time_series as datatypes_time_series
import tvb.datatypes.spectral as spectral
from tvb.basic.logger.builder import get_logger

LOG = get_logger(__name__)


class FourierAdapter(abcadapter.ABCAsynchronous):
    """ TVB adapter for calling the FFT algorithm. """
    
    _ui_name = "Fourier Spectral Analysis"
    _ui_description = "Calculate the FFT of a TimeSeries entity."
    _ui_subsection = "fourier"
    
    def get_input_tree(self):
        """
        Return a list of lists describing the interface to the analyzer. This
        is used by the GUI to generate the menus and fields necessary for
        defining a simulation.
        """
        algorithm = fft.FFT()
        algorithm.trait.bound = self.INTERFACE_ATTRIBUTES_ONLY
        tree = algorithm.interface[self.INTERFACE_ATTRIBUTES]
        for node in tree:
            if node['name'] == 'time_series':
                node['conditions'] = entities_filter.FilterChain(
                    fields=[entities_filter.FilterChain.datatype + '._nr_dimensions'],
                    operations=["=="], values=[4])
        return tree
    
    
    def get_output(self):
        return [spectral.FourierSpectrum]


    def __init__(self):
        super(FourierAdapter, self).__init__()
        self.algorithm = fft.FFT()
        self.memory_factor = 1
        
    
    def configure(self, time_series, segment_length=None, window_function=None):
        """
        Do any configuration needed before launching.

        :param time_series: the input time series to which the fft is to be applied
        :param segment_length: the block size which determines the frequency resolution \
                               of the resulting power spectra
        :param window_function: windowing functions can be applied before the FFT is performed
        :type  window_function: None; ‘hamming’; ‘bartlett’; ‘blackman’; ‘hanning’
        """
        shape = time_series.read_data_shape()
        LOG.debug("time_series shape is %s" % (str(shape)))
        LOG.debug("Provided segment_length is %s" % (str(segment_length)))
        LOG.debug("Provided window_function is %s" % (str(window_function)))
        ##-------------------- Fill Algorithm for Analysis -------------------##
        if segment_length is not None:
            self.algorithm.segment_length = segment_length

        self.algorithm.window_function = window_function
        self.algorithm.time_series = time_series
        LOG.debug("Using segment_length is %s" % (str(self.algorithm.segment_length)))
        LOG.debug("Using window_function  is %s" % (str(self.algorithm.window_function)))
    
    def get_required_memory_size(self, **kwargs):
        """
        Returns the required memory to be able to run the adapter.
        """
        input_shape = self.algorithm.time_series.read_data_shape()
        input_size = numpy.prod(input_shape) * 8.0
        output_size = self.algorithm.result_size(input_shape, self.algorithm.segment_length,
                                                 self.algorithm.time_series.sample_period)
        total_free_memory = psutil.virtual_memory().free + psutil.swap_memory().free
        total_required_memory = input_size + output_size
        while total_required_memory / self.memory_factor / total_free_memory > 0.8:
            self.memory_factor += 1
        return total_required_memory / self.memory_factor


    def get_required_disk_size(self, **kwargs):
        """
        Returns the required disk size to be able to run the adapter (in kB).
        """
        input_shape = self.algorithm.time_series.read_data_shape()
        output_size = self.algorithm.result_size(input_shape, self.algorithm.segment_length,
                                                 self.algorithm.time_series.sample_period)
        return output_size * TVBSettings.MAGIC_NUMBER / 8 / 2 ** 10


    def launch(self, time_series, segment_length=None, window_function=None):
        """
        Launch algorithm and build results.

        :param time_series: the input time series to which the fft is to be applied
        :param segment_length: the block size which determines the frequency resolution \
                               of the resulting power spectra
        :param window_function: windowing functions can be applied before the FFT is performed
        :type  window_function: None; ‘hamming’; ‘bartlett’; ‘blackman’; ‘hanning’
        :returns: the fourier spectrum for the specified time series
        :rtype: `FourierSpectrum`

        """
        shape = time_series.read_data_shape()
        block_size = int(math.floor(time_series.read_data_shape()[2]
                                    / self.memory_factor))
        blocks = int(math.ceil(time_series.read_data_shape()[2] / block_size))
        
        ##----------- Prepare a FourierSpectrum object for result ------------##
        spectra = spectral.FourierSpectrum(source=time_series,
                                           segment_length=self.algorithm.segment_length,
                                           windowing_function=str(window_function),
                                           storage_path=self.storage_path)
        
        ##------------- NOTE: Assumes 4D, Simulator timeSeries. --------------##
        node_slice = [slice(shape[0]), slice(shape[1]), None, slice(shape[3])]
        
        ##---------- Iterate over slices and compose final result ------------##
        small_ts = datatypes_time_series.TimeSeries(use_storage=False)
        small_ts.sample_period = time_series.sample_period
        for block in range(blocks):
            node_slice[2] = slice(block * block_size, min([(block+1) * block_size, shape[2]]), 1)
            small_ts.data = time_series.read_data_slice(tuple(node_slice))
            self.algorithm.time_series = small_ts
            partial_result = self.algorithm.evaluate()
            spectra.write_data_slice(partial_result)
        
        LOG.debug("partial segment_length is %s" % (str(partial_result.segment_length)))
        spectra.segment_length = partial_result.segment_length
        spectra.close_file()
        return spectra


