import sun_position_calc as sun
import cv2
import numpy as np
import datetime as dt
import pandas as pd

from numpy.lib.stride_tricks import sliding_window_view

def prepare_mask(mask_path):

    # read obstacle mask from predefined path
    obstacle_mask = cv2.imread(mask_path, -1)
    obstacle_mask = cv2.resize(obstacle_mask, (1520, 1520))

    return obstacle_mask

def prepare_duplicates(duplicate_list_path):

    #read list of duplicates from path, for exclusion from cloud retrieval
    duplicate_list = pd.read_csv(duplicate_list_path)["Duplicate"].to_list()
    return duplicate_list


def calc_mappings(theta_max_fish_deg, theta_max_rect_deg, image_width, mapping_function):

    #
    # generates mapping to convert fisheye images to rectilinear/plane image projection
    # available mapping_functions: "rectilinear", "stereographic", "equidistant", "equisolid", "orthographic"
    #

    img_radius = image_width/2

    rect_foclen = img_radius / np.tan(np.deg2rad(theta_max_rect_deg))            # max theta in rectilinear/plane projection: usually 80°

    
    temp_raw = np.mgrid[0:image_width,0:image_width] - img_radius
    
    xrel = temp_raw[0,:,:]
    yrel = temp_raw[1,:,:]

    # retrieve phi
    phi = np.atan2(-yrel, xrel) - np.pi/2
    phi = np.where((yrel>0) | ((yrel<=0) & (xrel>=0)), phi + 2*np.pi, phi)

    # retrieve radius and convert to new radius in projection via theta
    rect_r = np.sqrt(xrel**2+yrel**2)
    theta = np.atan(rect_r/rect_foclen)

    # get fisheye focal length and calculate radii from theta
    match mapping_function:
        case "rectilinear":
            fish_foclen = img_radius / (np.tan(np.deg2rad(theta_max_fish_deg)))
            fish_r = fish_foclen * np.tan(theta)
        case "stereographic":
            fish_foclen = img_radius / (2*np.tan(np.deg2rad(theta_max_fish_deg)/2))
            fish_r = 2*fish_foclen*np.tan(theta/2)
        case "equidistant":
            fish_foclen = img_radius / np.deg2rad(theta_max_fish_deg)
            fish_r = fish_foclen * theta
        case "equisolid":
            fish_foclen = img_radius / (2*np.sin(np.deg2rad(theta_max_fish_deg)/2))
            fish_r = 2*fish_foclen * np.sin(theta/2)
        case "orthographic":
            fish_foclen = img_radius / (np.sin(np.deg2rad(theta_max_fish_deg)))
            fish_r = fish_foclen * np.sin(theta)
        case _:
            raise ValueError("Mapping Function: \"{0}\" not found".format(mapping_function))
            return

    # create output arrays
    map_x = (-fish_r*np.sin(phi) + img_radius).astype("float32")
    map_y = (-fish_r*np.cos(phi) + img_radius).astype("float32")

    # filter values out of bounds
    map_x = np.where(rect_r>img_radius, -1, map_x)
    map_y = np.where(rect_r>img_radius, -1, map_y)

    return map_x, map_y





def repair_cloud_layer(layer_in):

    #
    # currently not used -> replaced by repair_cloud_layer_erosion
    #

    #get windows (surrounding 8 pixels for each original image pixel)
    window_views = sliding_window_view(layer_in,window_shape=(3,3))
    shifts = np.array([(0,0), (0,1), (0,2), (1,0), (1,2), (2,0), (2,1), (2,2)])

    # output layers
    neighbors_above = np.zeros_like(layer_in)
    neighbors_below = np.zeros_like(layer_in)

    # set output layers -> set to 1 if pixels have to be corrected (above->set to cloudy, below->set to clear)
    neighbors_above[1:-1,1:-1] = (np.sum(window_views[:, :, shifts[:,0], shifts[:,1]], axis=2) > 5) & (layer_in[1:-1,1:-1]==0)
    neighbors_below[1:-1,1:-1] = (np.sum(window_views[:, :, shifts[:,0], shifts[:,1]], axis=2) < 3) & (layer_in[1:-1,1:-1]==1)

    # apply corrections to cloud layer
    layer_fixed = layer_in + neighbors_above - neighbors_below

    return layer_fixed


def repair_cloud_layer_erosion(layer_in):

    kernel = np.ones((3,3), np.uint8)

    # erode and dilate afterwards
    eroded = cv2.erode(layer_in, kernel, iterations=1)
    dilated = cv2.dilate(eroded, kernel)
    
    return dilated


def convert_frac_to_octa(percent_in):

    octa_out = np.full(percent_in.shape, np.nan)
    
    octa_out = np.where(percent_in < 2.0, 0, octa_out)
    octa_out = np.where((percent_in>=2.0) & (percent_in<18.75), 1, octa_out)
    octa_out = np.where((percent_in>=18.25) & (percent_in<31.25), 2, octa_out)
    octa_out = np.where((percent_in>=31.25) & (percent_in<43.75), 3, octa_out)
    octa_out = np.where((percent_in>=43.75) & (percent_in<56.25), 4, octa_out)
    octa_out = np.where((percent_in>=56.25) & (percent_in<68.75), 5, octa_out)
    octa_out = np.where((percent_in>=68.75) & (percent_in<81.25), 6, octa_out)
    octa_out = np.where((percent_in>=81.25) & (percent_in<98.00), 7, octa_out)
    octa_out = np.where(percent_in>=98.00, 8, octa_out)
    
    return octa_out
    

def calc_fractions(sel_path, mask, mappings, duplicates, debug=False):


    # validate image
    cur_timestamp = dt.datetime.strptime(sel_path[-19:-4], "%Y%m%d_%H%M%S")
    sun_theta, sun_phi = sun.calc_sun_pos(51.333276, 12.388643, cur_timestamp)
    
    if sun_theta > 90:
        return -1, -1, cur_timestamp, -1  # skip if sun below horizon

    if sel_path in duplicates:
        return -1, -1, cur_timestamp, -1 # skip if image is duplicate
    
    # read image / preprocessing
    img_raw = cv2.imread(sel_path, -1)
    img_rgb = cv2.demosaicing(img_raw, cv2.COLOR_BAYER_BGGR2RGB)
    img_rgb = cv2.resize(img_rgb, (1520, 1520), interpolation=cv2.INTER_AREA)
    img_rgb = cv2.GaussianBlur(img_rgb, (5,5), 1)
    
    # white balance
    img_cor=np.empty_like(img_rgb)
    img_cor[:,:,0] = img_rgb[:,:,0] * 1.2148342954312141
    img_cor[:,:,1] = img_rgb[:,:,1] * 0.8269889348282208
    img_cor[:,:,2] = img_rgb[:,:,2] * 1.0334459844167483
    
    # apply mask
    img_crp = cv2.bitwise_and(img_cor, mask)
    img_crp = np.where(img_crp==0, np.nan, img_crp)
    
    # filter bright spots
    lumi = 0.2126 * img_crp[:,:,0] + 0.7152 * img_crp[:,:,1] + 0.0722 * img_crp[:,:,2]
    img_crp[:,:,0] = np.where(lumi>3500, np.nan, img_crp[:,:,0])
    img_crp[:,:,1] = np.where(lumi>3500, np.nan, img_crp[:,:,1])
    img_crp[:,:,2] = np.where(lumi>3500, np.nan, img_crp[:,:,2])
    
    # project to plane (equisolid -> rectilinear)
    img_crp = cv2.remap(img_crp, mappings[1], mappings[0], interpolation=cv2.INTER_LINEAR)
    
    # detection ratios
    rb_layer = img_crp[:,:,0] / img_crp[:,:,2]
    brbg_layer = img_crp[:,:,2] / img_crp[:,:,0] + img_crp[:,:,2] / img_crp[:,:,1]
    
    # thresholds (constant)
    rb_threshold = 0.88
    brbg_threshold = 2.2
    
    # cloud detection
    cld_rb_layer = np.where(np.isnan(rb_layer), np.nan, np.where(rb_layer > rb_threshold, 1, 0))
    cld_brbg_layer = np.where(np.isnan(brbg_layer), np.nan, np.where(brbg_layer < brbg_threshold, 1, 0))
    
    # repair layers
    cld_rb_layer = repair_cloud_layer_erosion(cld_rb_layer)
    cld_brbg_layer = repair_cloud_layer_erosion(cld_brbg_layer)
    
    # cloud fraction 
    rb_tot_px = np.nansum(np.isfinite(cld_rb_layer))
    brbg_tot_px = np.nansum(np.isfinite(brbg_layer))
    
    rb_cld_px = np.nansum(cld_rb_layer==1)
    brbg_cld_px = np.nansum(cld_brbg_layer==1)
    
    rb_fraction = np.round(rb_cld_px / rb_tot_px  *  100, 3)
    brbg_fraction = np.round(brbg_cld_px / brbg_tot_px  *  100, 3)

    # return, get more info returned, if debug flag set
    if debug==True:

        rb_hist = np.histogram(rb_layer, bins=500, range=[0.5, 1.3])
        brbg_hist = np.histogram(brbg_layer, bins=500, range=[1.5, 3])
        
        return lumi, img_crp, rb_hist, brbg_hist, rb_layer, brbg_layer, cld_rb_layer, cld_brbg_layer, rb_fraction, brbg_fraction
        
    else:
        
        return rb_fraction, brbg_fraction, cur_timestamp, np.nansum(lumi), cld_brbg_layer