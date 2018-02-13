import numpy as np

class Grid():
    """This class handles conversion from regular latlon to COSMO rotated latlon grid.
    Example usage:
    from COSMOPythonLib.proj import RotatedGrid
    import numpy as np

    g = RotatedGrid.Grid(pollat=43, pollon=-170)
    lons = np.array([8,9,10])
    lats = np.array([45,45.5,46])
    rlons, rlats = g.transformToRot(lons, lats)
    g.transformToReg(rlons,rlats)

    (array([ 8.00000155,  9.00000018, 10.        ]),
    array([ 44.99874097,  45.49960289,  46.        ]))

    """
    def __init__(self, pollon, pollat):
        self._pollambda = np.deg2rad(pollon)
        self._polphi = np.deg2rad(pollat)

    def getPole(self):
        return np.rad2deg(self._pollambda), np.rad2deg(self._polphi)
    
    def transformToRot(self, lons, lats):
        self._lats = np.deg2rad(lats)
        self._lons = np.deg2rad(lons)
        if self._lats.shape != self._lons.shape:
            raise ValueError("Dims of lats and lons have to be the same......")
        self._rlats = []
        self._rlons = []
        for element in zip(self._lons, self._lats):
            self._rlats.append(self.latToRlat(element[0], element[1]))
            self._rlons.append(self.lonToRlon(element[0], element[1]))
        return np.array(np.rad2deg(self._rlons)), np.rad2deg(np.array(self._rlats))

    def transformToReg(self, rlons, rlats):
        self._rlats = np.deg2rad(rlats)
        self._rlons = np.deg2rad(rlons)
        if self._lats.shape != self._lons.shape:
            raise ValueError("Dims of lats and lons have to be the same......")
        self._lats = []
        self._lons = []
        for element in zip(self._rlons, self._rlats):
            self._lats.append(self.rlatToLat(element[0], element[1]))
            self._lons.append(self.rlonToLon(element[0], element[1]))
        return np.array(np.rad2deg(self._lons)), np.array(np.rad2deg(self._lats))
        
    def rlonToLon(self, rlambda, rphi):
        s1 = np.sin(self._phi)
        c1 = np.cos(self._phi)
        s2 = np.sin(self._pollambda)
        c2 = np.cos(self._pollambda)
        tmp1 = s2 * (-s1 * np.cos(rlambda) * np.cos(rphi) + c1 * np.sin(rphi)) - c2 * np.sin(rlambda) * np.cos(rphi)
        tmp2 = c2 * (-s1 * np.cos(rlambda) * np.cos(rphi) + c1 * np.sin(rphi)) + s2 * np.sin(rlambda) * np.cos(rphi)
        self._lambda = np.arctan(tmp1/tmp2)
        return self._lambda

    def rlatToLat(self, rlambda, rphi):
        self._phi = np.arcsin(np.sin(rphi) * np.sin(self._polphi) + np.cos(rphi) * np.cos(rlambda) * np.cos(self._polphi))
        return self._phi

    def lonToRlon(self, _lambda, phi):
        self._rlambda = np.arctan((np.cos(self._polphi) * np.sin(_lambda - self._pollambda)) / \
                       (np.cos(phi) * np.sin(self._polphi) * np.cos(_lambda - self._pollambda) - np.sin(phi) * np.cos(self._polphi)))
        return self._rlambda

    def latToRlat(self, _lambda, phi):
        self._rphi = np.arcsin(np.sin(phi) * np.sin(self._polphi) + np.cos(phi) * np.cos(self._polphi) * np.cos(_lambda - self._pollambda))
        return self._rphi
