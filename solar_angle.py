from astropy.coordinates import EarthLocation, SkyCoord, get_sun, AltAz, ICRS
from astropy.time import Time
import astropy.units as u
import astropy.coordinates
import psrchive
import numpy as np
import sys
import matplotlib.pyplot as plt

def itrf_to_lle(observatory_x, observatory_y, observatory_z, wgs84=True, degrees=True):
    """Translate ITRF coordinates (X, Y, Z; e.g. from TEMPO2) to GRS80/WGS84. Taken
       from Vermeille, H. Journal of Geodesy (2002) 76: 451 (https://doi.org/10.1007/s00190-002-0273-6)
       Vermeille, H. Journal of Geodesy (2004) 78: 94 (https://doi.org/10.1007/s00190-004-0375-4).
    Input:
        observatory_x: observatory position on x-axis in meters.
        observatory_y: observatory position on y-axis in meters.
        observatory_z: observatory position on z-axis in meters.
        wgs84: use WGS84/GRS80 system (default: True)
        degrees: return positions in degrees
    Output:
        observatory_latitude: latitude of observatory in radians.
        observatory_latitude: longitude of observatory in radians.
        observatory_elevation: elevation of observatory above sea level in meters.
    """
    semi_major_axis = 6378137.0
    if wgs84:
        flattening_factor = 1.0 / 298.257223563  # WGS84 flattening_factor of the Earth
    else:
        flattening_factor = 1.0 / 298.257222101  # GRS80 flattening_factor of the Earth
    if isinstance(observatory_x, list) and isinstance(observatory_y, list) and isinstance(observatory_z, list):
        longitude = np.zeros(len(observatory_x))
        latitude = np.zeros(len(observatory_x))
        height = np.zeros(len(observatory_x))
        observatory_x = np.asarray(observatory_x, dtype=np.float)
        observatory_y = np.asarray(observatory_y, dtype=np.float)
        observatory_z = np.asarray(observatory_z, dtype=np.float)
    p = (observatory_x * observatory_x + observatory_y * observatory_y) / (semi_major_axis * semi_major_axis)
    esq = flattening_factor * (2.0 - flattening_factor)
    q = (1.0 - esq) / (semi_major_axis * semi_major_axis) * observatory_z * observatory_z
    r = (p + q - esq * esq) / 6.0
    s = esq * esq * p * q / (4 * r * r * r)
    t = np.power(1.0 + s + np.sqrt(s * (2.0 + s)), 1.0 / 3.0)
    u = r * (1.0 + t + 1.0 / t)
    v = np.sqrt(u * u + esq * esq * q)
    w = esq * (u + v - q) / (2.0 * v)
    k = np.sqrt(u + v + w * w) - w
    D = k * np.sqrt(observatory_x * observatory_x + observatory_y * observatory_y) / (k + esq)
    height = (k + esq - 1.0) / k * np.sqrt(D * D + observatory_z * observatory_z)
    latitude = 2.0 * np.arctan2(observatory_z, D + np.sqrt(D * D + observatory_z * observatory_z))
    if isinstance(observatory_x, list) and isinstance(observatory_y, list) and isinstance(observatory_z, list):
        if observatory_y.any() >= 0.0:
            longitude = 0.5 * np.pi - 2.0 * np.arctan2(observatory_x, np.sqrt(observatory_x * observatory_x + observatory_y * observatory_y) + observatory_y)
        else:
            longitude = -0.5 * np.pi + 2.0 * np.arctan2(observatory_x, np.sqrt(observatory_x * observatory_x + observatory_y * observatory_y) - observatory_y)
    elif isinstance(observatory_x, np.ndarray) and isinstance(observatory_y, np.ndarray) and isinstance(observatory_z, np.ndarray):
        if np.any(observatory_y) >= 0.0:
            longitude = 0.5 * np.pi - 2.0 * np.arctan2(observatory_x, np.sqrt(observatory_x * observatory_x + observatory_y * observatory_y) + observatory_y)
        else:
            longitude = -0.5 * np.pi + 2.0 * np.arctan2(observatory_x, np.sqrt(observatory_x * observatory_x + observatory_y * observatory_y) - observatory_y)
    else:
        if observatory_y >= 0.0:
            longitude = 0.5 * np.pi - 2.0 * np.arctan2(observatory_x, np.sqrt(observatory_x * observatory_x + observatory_y * observatory_y) + observatory_y)
        else:
            longitude = -0.5 * np.pi + 2.0 * np.arctan2(observatory_x, np.sqrt(observatory_x * observatory_x + observatory_y * observatory_y) - observatory_y)
    if degrees:
        longitude = np.rad2deg(longitude)
        latitude = np.rad2deg(latitude)
    return longitude, latitude, height




observation_no = sys.argv[1]
archive = psrchive.Archive_load(observation_no)
# the observations time and change it to utc format
mjd = archive.get_first_Integration().get_epoch().in_days()

time_utc = Time(mjd, format='mjd', scale='utc')
time_iso = time_utc.iso
observation_time = Time(time_iso)

#print time_iso, time_utc

#=======================================================================
# the source's coordinates
RA = archive.get_coordinates().ra().getRadians()
DEC = archive.get_coordinates().dec().getRadians()
source_coord = SkyCoord(RA, DEC, unit='rad', frame="icrs")
#print("The source coordinates", source_coord)


#========================================================================
# observatory information and coordinates

observatory_site = {'FR606': '4324017.054 165545.160 4670271.072',
'SE607': '3370272.092 712125.596 5349990.934',
'DE601': '4034101.901 487012.401 4900230.210',
'DE602': '4152568.416 828788.802 4754361.926',
'DE603': '3940296.126 816722.532 4932394.152',
'DE604': '3796380.254 877613.809 5032712.272',
'DE605': '4005681.407 450968.304 4926457.940',
'DE609': '3727218.128 655108.821 5117002.847'}

site = archive.get_telescope()
site_keys = observatory_site.keys()

if site in site_keys:
     site_x = float(observatory_site[site].split(' ')[0])
     site_y = float(observatory_site[site].split(' ')[1])
     site_z = float(observatory_site[site].split(' ')[2])


lon, lat, elev = itrf_to_lle(site_x, site_y, site_z, degrees=False)
#print lon, lat, elev

#======================================================
# get the sun coordinates and transfer it to ICRS
sun_coord_GCRS = astropy.coordinates.get_sun(observation_time)
#print("The sun coordinates in GCRS", sun_coord_GCRS)
#sun_coord_ICRS = sun_coord_GCRS.transform_to("icrs")
#print("The sun coordinates in ICRS", sun_coord_ICRS)

#=======================================================
#calculate the seperation between two frames, but not sure if this is the correct value of the solar angle
angle1 = sun_coord_GCRS.separation(source_coord)
angle = angle1.degree
print mjd , angle

