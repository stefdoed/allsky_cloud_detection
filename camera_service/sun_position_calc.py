# script for calcalution of sun position for camera control

import numpy as np
import datetime as dt

geo_lat_deg = 51.333276
geo_lon_deg = 12.388643
current_time = dt.datetime.now()        # assume UTC on allsky camera
    
geo_lat_rad=np.deg2rad(geo_lat_deg)
#longitude conversion omitted, because not needed

doy = current_time.timetuple().tm_yday
gamma = (2*np.pi*(doy-1)) / 366


declination = 0.006918 - 0.39912*np.cos(gamma) + 0.070257*np.sin(gamma) - 0.006758*np.cos(2*gamma) + 0.000907*np.sin(2*gamma)

g = 24/(2*np.pi) * (0.000075+0.001868*np.cos(gamma)-0.032077*np.sin(gamma)-0.014615*np.cos(2*gamma)-0.040849*np.sin(2*gamma))

t_utc = current_time
t_utc_hours = t_utc.hour + t_utc.minute/60 + t_utc.second/3600

t_loc_hours = t_utc_hours + 24/360 * (geo_lon_deg) + g

kappa = ((12-t_loc_hours) / 24 * 360)  *  np.pi/180



theta_0 = np.arccos(np.sin(geo_lat_rad)*np.sin(declination) + np.cos(geo_lat_rad)*np.cos(declination)*np.cos(kappa))
phi_0 = np.arccos( (np.cos(theta_0)*np.sin(geo_lat_rad)-np.sin(declination)) / (np.sin(theta_0)*np.cos(geo_lat_rad)) )

if kappa > 0:
    phi_0 *= -1

phi_0 += np.pi

print(np.rad2deg(theta_0), np.rad2deg(phi_0))