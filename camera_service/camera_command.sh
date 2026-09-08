#!/bin/sh

DATE_PATH=`date "+%Y/%m/%d/%H"`
FILENAME=`date "+%Y%m%d_%H%M%S"`

CUR_MINUTE=`date "+%M" | bc`
CUR_SECOND=`date "+%S" | bc`

SUN_THRESHOLD=`echo '95.0' | bc`        #constant

echo "$CUR_MINUTE"
echo "$CUR_SECOND"

SUN_THETA=`python /home/allsky/camera_service/sun_position_calc.py | awk '{print $1}' | bc`

if echo "$SUN_THETA < $SUN_THRESHOLD" | bc -l | grep -q 1; then
 echo "Daytime detected, Image acquired"
 mkdir -p /home/allsky/data/$DATE_PATH/
 libcamera-still -n -r -o /home/allsky/camera_service/raw_frame.dng --denoise off --ev -1 --immediate --awbgains 1,1
 python /home/allsky/camera_service/crop_and_conv2png.py /home/allsky/camera_service/raw_frame.dng /home/allsky/data/$DATE_PATH/$FILENAME.png
else
 echo "Nighttime detected, No image acquired"
 if [ $CUR_MINUTE -eq 30 ];then
  if [ $CUR_SECOND -lt 25 ]; then
   mkdir -p /home/allsky/data/$DATE_PATH/
   libcamera-still -n -r -o /home/allsky/camera_service/raw_frame.dng --denoise off --ev -1 --immediate --awbgains 1,1
   python /home/allsky/camera_service/crop_and_conv2png.py /home/allsky/camera_service/raw_frame.dng /home/allsky/data/$DATE_PATH/$FILENAME.png
  fi
 fi
fi
