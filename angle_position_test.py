import astropy.units as u
from astropy.coordinates import EarthLocation, SkyCoord
from astropy.time import Time
from astroplan import Observer
from astroplan import FixedTarget
from pytz import timezone

# Set up Observer, Target and observation time objects.
longitude = "21.4438888892753"
latitude = "-30.7110555556117"
elevation = 1035 * u.m
location = EarthLocation.from_geodetic(longitude, latitude, elevation)
print location

observer = Observer(name='MeerKAT', location=location, pressure=0.0 * u.bar, relative_humidity=0.0, temperature=0 * u.deg_C, timezone=timezone('UTC'), description="MeerKAT")
coordinates = SkyCoord("08h35m20.61149s", "-45d10m34.8751s", frame="icrs")
vela = FixedTarget(name="PSR J0835-4510", coord=coordinates)
observe_time = Time(['2015-03-15 15:30:00'])
sun_coord = astropy.coordinates.get_sun(observe_time)

#===============================================================================
from astropy.coordinates import EarthLocation, SkyCoord, get_sun, AltAz
from astropy.time import Time
import astropy.coordinates as coord
import astropy.units as u
#from astroplan import Observer
from astroplan import FixedTarget
from pytz import timezone

#=====================================================
'''
# Set up Observer, Target and observation time objects.
longitude = "21.4438888892753"
latitude = "-30.7110555556117"
elevation = 1035 * u.m
location = EarthLocation.from_geodetic(longitude, latitude, elevation)
print location

observer = Observer(name='MeerKAT', location=location, pressure=0.0 * u.bar, relative_humidity=0.0, temperature=0 * u.deg_C, timezone=timezone('UTC'), description="MeerKAT")
coordinates = SkyCoord("08h35m20.61149s", "-45d10m34.8751s", frame="icrs")
vela = FixedTarget(name="PSR J0835-4510", coord=coordinates)
observe_time = Time(['2015-03-15 15:30:00'])
sun_coord = astropy.coordinates.get_sun(observe_time)
'''
#=====================================================


observe_time = Time('2014-07-14 05:31:54') #UTC time
observe_loc = coord.EarthLocation(lon=572355.5268524 * u.deg, lat=115551.2005399 * u.deg, height=41.3579993117601) #Geodetic height, m

sun_time = Time(observe_time, format='iso', scale='utc')

source_loc = FixedTarget(name="PSR J0815+4611", coord=coordinates)



altaz = AltAz(obstime=sun_time, location=observe_loc)

zen_ang = get_sun(sun_time).transform_to(altaz).zen

print(zen_ang)

