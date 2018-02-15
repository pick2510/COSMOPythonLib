import glob
import os
import re
import datetime

import netCDF4
import numpy as np
import pandas as pd


class COSMOnetCDFDataset(object):
    def __init__(self, path_to_files, analysis_file = "lfff00000000c.nc"):
        self._date_time_regex = re.compile("(\d{4})-(\d{2})-(\d{2}) (\d{2}):(\d{2}):(\d{2})")
        self._variables = None
        self._init_time = None
        self._history_interval = None
        self._lats = None
        self._lons = None
        self._rlats = None
        self._rlons = None
        self._xshape = None
        self._yshape = None
        self._last_time = None
        self._analysis_file = analysis_file
        self._cosmo_file_path = os.path.join(path_to_files, '')
        self._files_in_path = list(set(glob.glob(self._cosmo_file_path + "lfff*")) - \
        set(glob.glob(self._cosmo_file_path + self._analysis_file)))
        self._files_in_path.sort()
        self._num_of_files = len(self._files_in_path)
        if self._num_of_files < 1:
            raise ValueError("COSMOPython Lib: No COSMO netCDF dataset found. Check the path")
        self.__create_meta_data()

    def __create_meta_data(self):
        first_file = self._files_in_path[0]
        last_file = self._files_in_path[-1]
        try:
            self._first_file = netCDF4.Dataset(first_file)
        except:
            raise ValueError("COSMOPythonLib: File {} could not be opened. Corrupt file?".format(first_file))
        self._variables = self._first_file.variables.keys()
        __init_string = self._first_file['time'].units
        __date_match = self._date_time_regex.findall(__init_string)
        self._init_time = datetime.datetime(int(__date_match[0][0]), int(__date_match[0][1]), int(__date_match[0][2]), 
        int(__date_match[0][3]), int(__date_match[0][4]), int(__date_match[0][5]))
        self.__extract_coordinates(self._first_file)
        self._first_file.close()
        second_file = self._files_in_path[1]
        try:
            self._second_file = netCDF4.Dataset(second_file)
        except:
            raise ValueError("COSMOPythonLib: File {} could not be opened. Corrupt file?".format(second_file))
        __delta_T = self._second_file['time'][:]
        self._history_interval = datetime.timedelta(seconds=int(__delta_T))
        self._second_file.close()
        try:
            self._last_file = netCDF4.Dataset(last_file)
        except:
            raise ValueError("COSMOPythonLib: File {} could not be opened. Corrupt file?".format(last_file))
        __delta_T = self._last_file['time'][:]
        __delta_T_timedelta = datetime.timedelta(seconds=int(__delta_T))
        self._last_time = self._init_time + __delta_T_timedelta
        self._last_file.close()

        
    def __extract_coordinates(self, firstfile):
        self._lons = firstfile['lon'][:]
        self._lats = firstfile['lat'][:]
        self._rlats = firstfile['rlat'][:]
        self._rlons = firstfile['rlon'][:]
        self._xshape = len(self._rlons)
        self._yshape = len(self._rlats)
    
    def get_variables(self,  vars, start=None, end=None, order_by = 'date'):
        if vars is None:
            raise ValueError("Please choose variables")
        if not isinstance(vars, list):
            vars = [vars]
        if start is None:
            start = self._init_time
        if end is None:
            end = self._last_time
        if start > end:
            raise ValueError("start {} > end {}, choose a correct date range".format(start, end))
            return
        __res_dict = {}
        if order_by == 'date':
            for f in self._files_in_path:
                try:
                    ncdf = netCDF4.Dataset(f)
                except:
                    raise ValueError("Could not open needed file {}. Corrupt file?".format(f))
                    return
                _delta_t = datetime.timedelta(seconds=int(ncdf['time'][:]))
                _file_date = self._init_time + _delta_t
                if _file_date >= start and _file_date <= end:
                    __res_dict[_file_date] = {}
                    for arg in vars:
                        try:
                            __res_dict[_file_date][arg] = ncdf[arg][:]
                        except: 
                            ncdf.close()
                            raise ValueError("Could not load variable {}. Is it available?".format(arg))
                ncdf.close()
        elif  order_by == 'variable':
            for arg in vars:
                __res_dict[arg] = {}
            for f in self._files_in_path:
                try:
                    ncdf = netCDF4.Dataset(f)
                except:
                    raise ValueError("Could not open needed file {}. Corrupt file?".format(f))
                _delta_t = datetime.timedelta(seconds=int(ncdf['time'][:]))
                _file_date = self._init_time + _delta_t
                if _file_date >= start and _file_date <= end:
                    for arg in vars:
                        try:
                            __res_dict[arg][_file_date] = ncdf[arg][:]
                        except: 
                            ncdf.close()
                            raise ValueError("Could not load variable {}. Is it available?".format(arg))
                ncdf.close()
        return __res_dict

    @property
    def variables(self):
        return self._variables

    @property
    def num_of_files(self):
        return self._num_of_files

    @property
    def init_time(self):
        return self._init_time

    @property
    def rotated_coordinates(self):
        return np.array([self._rlons, self._rlats])

    @property
    def regular_meshgrid(self):
        return np.array([self._lons, self._lats])

    @property
    def last_date(self):
        return self._last_time

    @property
    def history_interval(self):
        return self._history_interval





dat = COSMOnetCDFDataset("/media/pick/Data/cosmoBasel/")
print(dat.variables)
print(dat.get_variables(["TD_2M", "T_2M"]))
print("-----------------------------------------------------")
print(dat.get_variables(["T_2M", "TD_2M"], order_by = 'variable'))

print(dat.get_variables(start=datetime.datetime(2015,7,3), end=datetime.datetime(2015,7,2), vars="T_2M"))
