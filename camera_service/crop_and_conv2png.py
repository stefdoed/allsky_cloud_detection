import tifffile
import cv2
import sys
import numpy as np

file_path_in=sys.argv[1]
file_path_out=sys.argv[2]

im_raw=tifffile.TiffFile(file_path_in)
im_sel=im_raw.series[1].asarray()
im_cropped=im_sel[:,508:3548]

mask=np.zeros_like(im_cropped)
mask=cv2.circle(mask,(1520,1520), 1520, (4095,4095,4095), -1)

im_cropped=cv2.bitwise_and(im_cropped, mask)

cv2.imwrite(file_path_out,im_cropped)
