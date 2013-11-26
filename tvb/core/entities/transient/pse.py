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
.. moduleauthor:: Lia Domide <lia.domide@codemart.ro>
.. moduleauthor:: Ionel Ortelecan <ionel.ortelecan@codemart.ro>
.. moduleauthor:: Bogdan Neacsa <bogdan.neacsa@codemart.ro>

Data for Parameter Space Exploration view will be defined here.
The purpose of this entities is to be used in Genshi UI, or for populating visualizer.
"""

import sys
import json
import math
from tvb.basic.config.settings import EnhancedDictionary
from tvb.core.entities import model


class ContextDiscretePSE(EnhancedDictionary):
    """
    Entity used for filling a PSE visualizer.
    """
    KEY_GID = "Gid"
    KEY_NODE_TYPE = "dataType"
    KEY_OPERATION_ID = "operationId"
    KEY_TOOLTIP = "tooltip"
    LINE_SEPARATOR = "<br/>"
    
    
    def __init__(self, datatype_group_gid, labels_x, labels_y, color_metric, size_metric, back_page):
        super(ContextDiscretePSE, self).__init__()
        self.datatype_group_gid = datatype_group_gid
        self.min_color = sys.float_info.max
        self.max_color = sys.float_info.min
        self.min_shape_size_weight = sys.float_info.max
        self.max_shape_size_weight = sys.float_info.min
        self.has_started_ops = False
        self.status = 'started'
        self.labels_x = labels_x
        self.labels_y = labels_y
        self.series_array, self.data, self.available_metrics = [], [], []
        self.datatypes_dict = {}
        self.color_metric = color_metric
        self.size_metric = size_metric
        self.pse_back_page = back_page
    
        
    def prepare_individual_jsons(self):
        """
        Apply JSON.dumps on all attributes which can not be passes as they are towards UI.
        """
        self.labels_x = json.dumps(self.labels_x)
        self.labels_y = json.dumps(self.labels_y)
        self.data = json.dumps(self.data)
    
    
    def prepare_full_json(self):
        """
        Apply JSON.dumps on full dictionary.
        """
        return json.dumps(self)
    

    def build_node_info(self, operation, datatype):
        """
        Build a dictionary with all the required information to be displayed for a given node.
        """
        node_info = {}
        if operation.status == model.STATUS_FINISHED and datatype is not None:
            ### Prepare attributes to be able to show overlay and launch further analysis.
            node_info[self.KEY_GID] = datatype.gid
            node_info[self.KEY_NODE_TYPE] = datatype.type
            node_info[self.KEY_OPERATION_ID] = operation.id
            ### Prepare tooltip for quick display.
            datatype_tooltip = str("Operation id: " + str(operation.id) + self.LINE_SEPARATOR +
                                   "Datatype gid: " + str(datatype.gid) + self.LINE_SEPARATOR +
                                   "Datatype type: " + str(datatype.type) + self.LINE_SEPARATOR +
                                   "Datatype subject: " + str(datatype.subject) + self.LINE_SEPARATOR +
                                   "Datatype invalid: " + str(datatype.invalid))
            ### Add scientific report to the quick details.
            if datatype.summary_info is not None:
                for key, value in datatype.summary_info.iteritems():
                    datatype_tooltip = datatype_tooltip + self.LINE_SEPARATOR + str(key) + ": " + str(value)
            node_info[self.KEY_TOOLTIP] = datatype_tooltip
        else:
            tooltip = "No result available. Operation is in status: %s" % operation.status.split('-')[1]
            node_info[self.KEY_TOOLTIP] = tooltip
        return node_info
    
    
    def prepare_metrics_datatype(self, measures, datatype):
        """
        Update attribute self.datatypes_dict with metric values for this DataType.
        """
        dt_info = {}
        if measures is not None and len(measures) > 0:
            measure = measures[0]
            self.available_metrics = measure.metrics.keys()

            # As default we have the first two metrics available is no metrics are passed from the UI
            if self.color_metric is None and self.size_metric is None:
                if len(self.available_metrics) >= 1:
                    self.color_metric = self.available_metrics[0]
                if len(self.available_metrics) >= 2:
                    self.size_metric = self.available_metrics[1]

            if self.color_metric is not None:
                color_value = measure.metrics[self.color_metric]
                if color_value < self.min_color:
                    self.min_color = color_value
                if color_value > self.max_color:
                    self.max_color = color_value
                dt_info[self.color_metric] = color_value

            if self.size_metric is not None:
                size_value = measure.metrics[self.size_metric]
                if size_value < self.min_shape_size_weight:
                    self.min_shape_size_weight = size_value
                if size_value > self.max_shape_size_weight:
                    self.max_shape_size_weight = size_value
                dt_info[self.size_metric] = size_value
        self.datatypes_dict[datatype.gid] = dt_info
        
    
    def fill_object(self, final_dict):
        """ Populate current entity with attributes required for visualizer"""
        
        ## Make sure that current form on MIN/MAX attributes is consistent
        ## MIN and MAX  should not be equal, to get a division by 0 (on their difference) after this step.
        if self.min_shape_size_weight == self.max_shape_size_weight:
            self.max_shape_size_weight += 1
        if self.min_color == self.max_color:
            self.max_color += 1
            
        all_series = []
        for i, key_1 in enumerate(self.labels_x):
            for j, key_2 in enumerate(self.labels_y):
                datatype_gid = None
                if self.KEY_GID in final_dict[key_1][key_2]:
                    #This means the operation was finished
                    datatype_gid = final_dict[key_1][key_2][self.KEY_GID]
                series_data = [[i, j]]
                color_weight, shape_type_1 = self.__get_color_weight(self.datatypes_dict, datatype_gid, 
                                                                     self.color_metric)
                if (shape_type_1 is not None) and (datatype_gid is not None):
                    final_dict[key_1][key_2][self.KEY_TOOLTIP] = (final_dict[key_1][key_2][self.KEY_TOOLTIP] +
                                                                  self.LINE_SEPARATOR + " Color metric has NaN values")
                shape_size, shape_type_2 = self.__get_node_size(self.datatypes_dict, datatype_gid, len(self.labels_x), 
                                                                len(self.labels_y), self.size_metric)
                if (shape_type_2 is not None) and (datatype_gid is not None):
                    final_dict[key_1][key_2][self.KEY_TOOLTIP] = (final_dict[key_1][key_2][self.KEY_TOOLTIP] +
                                                                  self.LINE_SEPARATOR + " Size metric has NaN values")
                #If either of the shape_types is not none use that
                shape_type = shape_type_1 or shape_type_2
                series = self.__get_node_json(series_data, shape_type, shape_size)
                final_dict[key_1][key_2]['color_weight'] = color_weight
                all_series.append(series)

        #each shape from the UI corresponds to a dataType. In this matrix we
        #keep information about those dataTypes.
        matrix = []
        for i, x_label in enumerate(self.labels_x):
            matrix.append([])
            for y_label in self.labels_y:
                matrix[i].append(final_dict[x_label][y_label])
        
        self.data = matrix
        self.series_array = self.__build_series_json(all_series)
        self.status = 'started' if self.has_started_ops else 'finished'
        
        
    @staticmethod
    def __build_series_json(list_of_series):
        """ Given a list with all the data points, build the final FLOT JSON. """
        final_json = "["
        for i, value in enumerate(list_of_series):
            if i:
                final_json += ","
            final_json += value
        final_json += "]"
        return final_json
    
    
    @staticmethod
    def __get_node_json(data, symbol, radius):
        """
        For each data point entry, build the FLOT specific JSON.
        """
        series = '{"data": ' + json.dumps(data) + ', "points": {'
        if symbol is not None:
            series += '"symbol": "' + symbol + '", '
        series += '"radius": ' + str(radius) + '} }'
        return series


    @staticmethod
    def __get_color_weight(datatype_indexes, datatype_gid, metric):
        """
        Returns the color weight of the shape used for representing the dataType with id equal to 'datatype_id'.

        :param: datatype_indexes -  a dictionary which contains as keys a dataType GID and as values
                            the index corresponding to the dataType into the list of
                            dataTypes resulted from the same operation group
        :param: datatype_gid - It should exists into the 'datatype_indexes' dictionary.
        :param: metric - current metric key.
        """
        if datatype_gid is None:
            return 0, "cross"
        node_info = datatype_indexes[datatype_gid]
        valid_metric = True

        if metric in node_info:
            try:
                if math.isnan(float(node_info[metric])) or math.isinf(float(node_info[metric])):
                    valid_metric = False
            except ValueError, _:
                valid_metric = False
            if valid_metric:
                return node_info[metric], None
            else:
                return 0, "cross"
        return 0, None


    def __get_node_size(self, datatype_indexes, datatype_gid, range1_length, range2_length, metric):
        """
        Computes the size of the shape used for representing the dataType with GID given.

        :param: datatype_indexes -  a dictionary which contains as keys a daTatype GID and as values
                            the index corresponding to the dataType into the list of
                            dataTypes resulted from the same operation group
        :param: datatype_gid - It should exists into the 'datatype_indexes' dict.
        
        """
        min_size, max_size = self.__get_boundaries(range1_length, range2_length)
        if datatype_gid is None:
            return max_size / 2.0, "cross"
        node_info = datatype_indexes[datatype_gid]

        if metric in node_info:
            valid_metric = True
            try:
                if math.isnan(float(node_info[metric])) or math.isinf(float(node_info[metric])):
                    valid_metric = False
            except ValueError, _:
                valid_metric = False

            if valid_metric:
                shape_weight = node_info[metric]
                return (min_size + ((shape_weight - self.min_shape_size_weight) /
                                    float((self.max_shape_size_weight - self.min_shape_size_weight))) *
                        (max_size - min_size)), None
            else:
                return max_size / 2.0, "cross"
        return max_size / 2.0, None


    @staticmethod
    def __get_boundaries(range1_length, range2_length):
        """
        Returns the MIN and the max values of the interval from
        which may be set the size of a certain shape.
        """
        #the arrays 'intervals' and 'values' should have the same size
        intervals = [0, 3, 5, 8, 10, 20, 30, 40, 50, 60, 90, 110, 120]
        values = [(10, 50), (10, 40), (10, 33), (8, 25), (5, 15), (4, 10),
                  (3, 8), (2, 6), (2, 5), (1, 4), (1, 3), (1, 2), (1, 2)]

        max_length = max([range1_length, range2_length])
        if max_length <= intervals[0]:
            return values[0]
        elif max_length >= intervals[len(intervals) - 1]:
            return values[len(values) - 1]
        else:
            for i, interval in enumerate(intervals):
                if max_length <= interval:
                    return values[i - 1]    
       
       
        
        