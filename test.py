import datetime

from COSMOPythonLib.data import COSMOnetCDFDataset



dat = COSMOnetCDFDataset("/media/pick/Data/cosmoBasel/")
#print(dat.variables)
#print(dat.get_variables(["TD_2M", "T_2M"]))
#print("-----------------------------------------------------")
#print(dat.get_variables(["T_2M", "TD_2M"], order_by = 'variable'))

#print(dat.get_variables(start=datetime.datetime(2015,7,3), end=datetime.datetime(2015,7,2), vars="T_2M"))
print(dat.transformToRot(lats=47, lons=9))
print(dat.transformToReg(rlons=-0.73133352, rlats=0.0043532))
dat.get_timeseries_at_latlon(["T_2M", "TD_2M"], 47, 8.5)
