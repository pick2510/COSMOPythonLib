import glob
import os
import re
import datetime

import netCDF4
import numpy as np
import pandas as pd
from scipy.interpolate import interp2d, interpn


from .proj.grids import RotatedGrid


class COSMOnetCDFDataset(object):
    def __init__(self, path_to_files, analysis_file="lfff00000000c.nc"):
        self._date_time_regex = re.compile(
            "(\d{4})-(\d{2})-(\d{2}) (\d{2}):(\d{2}):(\d{2})")
        self._variables = None
        self._init_time = None
        self._history_interval = None
        self._timesteps = None
        self._lats = None
        self._lons = None
        self._rlats = None
        self._rlons = None
        self._xshape = None
        self._yshape = None
        self._last_time = None
        self._grid_north_pole_lat = None
        self._grid_north_pole_lon = None
        self._rotated_grid = None
        self._analysis_file = analysis_file
        self._cosmo_file_path = os.path.join(path_to_files, '')
        self._files_in_path = list(set(glob.glob(self._cosmo_file_path + "lfff*.nc")) -
                                   set(glob.glob(self._cosmo_file_path + self._analysis_file)))
        self._files_in_path.sort()
        self._num_of_files = len(self._files_in_path)
        if self._num_of_files < 1:
            raise ValueError(
                "COSMOPython Lib: No COSMO netCDF dataset found. Check the path")
        try:
            self._cosmo_multifile = netCDF4.MFDataset(self._files_in_path)
        except:
            raise ValueError(
                "COSMOPythonLib: netCDF File(s) could not be opened. Corrupt file(s)?")
        self.__create_meta_data()

    def __create_meta_data(self):
        self._variables = self._cosmo_multifile.variables.keys()
        __init_string = self._cosmo_multifile['time'].units
        __date_match = self._date_time_regex.findall(__init_string)
        self._init_time = datetime.datetime(int(__date_match[0][0]), int(__date_match[0][1]), int(__date_match[0][2]),
                                            int(__date_match[0][3]), int(__date_match[0][4]), int(__date_match[0][5]))
        self.__extract_coordinates(self._cosmo_multifile)
        __delta_T = self._cosmo_multifile['time'][:][1]
        self._history_interval = datetime.timedelta(seconds=int(__delta_T))
        __delta_T = self._cosmo_multifile['time'][:][-1]
        __delta_T_timedelta = datetime.timedelta(seconds=int(__delta_T))
        self._last_time = self._init_time + __delta_T_timedelta
        self._timesteps = len(self._cosmo_multifile['time'][:])
        self._initialize_Rotated_Grid()

    def __extract_coordinates(self, cosmofile):
        self._lons = cosmofile['lon'][:]
        self._lats = cosmofile['lat'][:]
        self._rlats = cosmofile['rlat'][:]
        self._rlons = cosmofile['rlon'][:]
        self._xshape = len(self._rlons)
        self._yshape = len(self._rlats)

    def get_variables(self,  vars, start=None, end=None, order_by='date'):
        if vars is None:
            raise ValueError("Please choose variables")
        if not isinstance(vars, list):
            vars = [vars]
        if start is None:
            start = self._init_time
        if end is None:
            end = self._last_time
        if start > end:
            raise ValueError(
                "start {} > end {}, choose a correct date range".format(start, end))
        __res_dict = {}
        if order_by == 'date':
           for i in range(0, self._timesteps):
                _delta_t = datetime.timedelta(seconds=int(
                    self._cosmo_multifile['time'][:][i]))
                _file_date = self._init_time + _delta_t
                if _file_date >= start and _file_date <= end:
                    __res_dict[_file_date] = {}
                    for arg in vars:
                        try:
                            __res_dict[_file_date][arg] = self._cosmo_multifile[arg][i][:]
                        except:
                            raise ValueError(
                                "Could not load variable {}. Is it available?".format(arg))
        elif order_by == 'variable':
            for arg in vars:
                __res_dict[arg] = {}
            for i in range(0, self._timesteps):
                _delta_t = datetime.timedelta(seconds=int(
                    self._cosmo_multifile['time'][:][i]))
                _file_date = self._init_time + _delta_t
                if _file_date >= start and _file_date <= end:
                    for arg in vars:
                        try:
                            __res_dict[arg][_file_date] = self._cosmo_multifile[arg][i][:]
                        except:
                            raise ValueError(
                                "Could not load variable {}. Is it available?".format(arg))
        else:
            raise ValueError("Please specify ordering...")
        return __res_dict

    def get_timeseries_at_latlon(self,  vars, lat, lon, typ='latlon', start=None, end=None):
        if vars is None:
            raise ValueError("Please choose variables")
        if not isinstance(vars, list):
            vars = [vars]
        if start is None:
            start = self._init_time
        if end is None:
            end = self._last_time
        if start > end:
            raise ValueError(
                    "start {} > end {}, choose a correct date range".format(start, end))
        if lat is None or lon is None:
            raise ValueError(
                    "lat or lon not given. PLease provide coordinates"
                )
        self.checkCoordinates(lat, lon)
        _dims = {}
        _columns = ['datetime']
        for var in vars:
            _columns.append(var)
            try:
                dim = self._cosmo_multifile[var].dimensions
            except:
                raise ValueError(
                        "Could not load variable {}. Is it available?".format(var))
            if len(dim) == 4:
                _dims[var] = "XYZT"
            elif len(dim) == 3:
                _dims[var] = "XYT"
            else:
                raise ValueError("Something is strange, dims not 4 or 3..")
        if typ == 'latlon':
            lat, lon = self._rotated_grid.transformToRot(lats=lat, lons=lon)
        __res_list = []
        for i in range(0, self._timesteps):
            _delta_t = datetime.timedelta(seconds=int(
                    self._cosmo_multifile['time'][:][i]))
            _file_date = self._init_time + _delta_t
            if _file_date >= start and _file_date <= end:
                __rec_list = []
                _delta_t = datetime.timedelta(seconds=int(
                    self._cosmo_multifile['time'][:][i]))
                _file_date = self._init_time + _delta_t
                __rec_list.append(_file_date)
                for arg in vars:
                    _raw = self._cosmo_multifile[arg][i][:]
                    _inteprolator = interp2d(
                            self._rlons, self._rlats, _raw)
                    _res = float(_inteprolator(lon, lat))
                    __rec_list.append(_res)
                __res_list.append(__rec_list)
        df = pd.DataFrame.from_records(__res_list, columns=_columns)
        df.index = df['datetime']
        df.drop('datetime', axis=1, inplace=True)
        print(df) 


    def checkCoordinates(self, lon, lat):
        if not -90 <= lat <= 90:
            raise ValueError(
                "Using latlon coordinates, lat not between -90 and 90N")
        if not -180 <= lon <= 180:
            raise ValueError(
                "Using latlon coordinates, lon not between -180 and 180W")
    
    def _initialize_Rotated_Grid(self):
        self._grid_north_pole_lat = self._cosmo_multifile['rotated_pole'].grid_north_pole_latitude
        self._grid_north_pole_lon = self._cosmo_multifile['rotated_pole'].grid_north_pole_longitude
        self._rotated_grid = RotatedGrid(pollon=self._grid_north_pole_lon, pollat=self._grid_north_pole_lat)

    def transformToRot(self, lats, lons):
        return self._rotated_grid.transformToRot(lons=lons, lats=lats)
    

    def transformToReg(self, rlats, rlons):
        return self._rotated_grid.transformToReg(rlons=rlons, rlats=rlats)

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


