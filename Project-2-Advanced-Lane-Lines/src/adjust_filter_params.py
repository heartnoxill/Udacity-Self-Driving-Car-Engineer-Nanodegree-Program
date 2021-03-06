#Adjust filter params
import glob
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import numpy as np
import cv2

from cameraCalibration import get_undistorted_image
from combiningThresholds import alpha_beta_auto_correction

image = np.array([])
filter_window_name = "Filtering"
ksize = 5

h_ch = np.array( [  3,  31] )
l_ch = np.array( [  0, 255] )
s_ch = np.array( [110, 255] )

# sobel_mag = np.array([54, 255])
# sobel_ang = np.array([-1.4486232791552935, 1.3089969389957472])
sobel_mag = np.array([20, 255])
sobel_ang = np.array([-1.18682389, 0.15707963])

def abs_sobel_thresh(img, orient='x', sobel_kernel=3, thresh=(0, 255)):
    # Calculate directional gradient
    # Apply threshold
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)

    if orient == 'x':
        sobel = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=sobel_kernel)
    elif orient == 'y':
        sobel = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=sobel_kernel)

    abs_sobel = np.absolute(sobel)
    scaled_sobel = np.uint8(abs_sobel * 255 / np.max(abs_sobel))

    grad_binary = np.zeros_like(img)
    grad_binary[(thresh[0] <= scaled_sobel) & (scaled_sobel <= thresh[1])] = 255
    return grad_binary

def mag_thresh(image, sobel_kernel=3, mag_thresh=(0, 255)):
    # Calculate gradient magnitude
    # Apply threshold
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize = sobel_kernel)
    sobely = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize = sobel_kernel)

    abs_sobelxy = np.sqrt( np.square(sobelx) + np.square(sobely) )
    sobelxyScaled = np.uint8( 255 * abs_sobelxy / np.max(abs_sobelxy) )

    mag_binary = np.zeros_like(sobelxyScaled)
    mag_binary[(mag_thresh[0] < sobelxyScaled) & (sobelxyScaled < mag_thresh[1])] = 255
    return mag_binary

def dir_threshold(image, sobel_kernel=3, thresh=(0, np.pi/2)):
    # Calculate gradient direction
    # Apply threshold
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize = sobel_kernel)
    sobely = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize = sobel_kernel)
    
    abs_sobelxy = np.sqrt(np.square(sobelx) + np.square(sobely))
    graddir = np.arctan2(np.absolute(sobely), np.absolute(sobelx))
    
    dir_binary = np.zeros_like(abs_sobelxy)
    dir_binary[ (thresh[0] < graddir) & ( graddir < thresh[1] ) ] = 1
    return dir_binary

def sobel_mag_dir_treshold(image, sobel_kernel=3, mag_thresh=(0, 255), dir_thresh=(0, np.pi/2)):
    # gray = image
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    gray = alpha_beta_auto_correction(gray)
    # grat = cv2.equalizeHist(gray)
    sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize = sobel_kernel)
    sobely = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize = sobel_kernel)
    
    abs_sobelxy = np.sqrt( np.square(sobelx) + np.square(sobely) )
    sobelxyScaled = np.uint8( 255 * abs_sobelxy / np.max(abs_sobelxy) )

    abs_sobelxy = np.sqrt( np.square(sobelx) + np.square(sobely) )
    graddir = np.arctan2(np.absolute(sobely), np.absolute(sobelx))
    
    res_binary = np.zeros_like(sobelxyScaled)
    res_binary[ ((mag_thresh[0] < sobelxyScaled) & (sobelxyScaled < mag_thresh[1]) & (dir_thresh[0] < graddir) & ( graddir < dir_thresh[1] )) ] = 255
    return res_binary

def hls_convert_and_filter(rgb_image, h, l, s):
    local_image = cv2.cvtColor(rgb_image, cv2.COLOR_RGB2HLS)
    low_th = np.array([h[0], l[0], s[0]])
    high_th = np.array([h[1], l[1], s[1]])
    res = cv2.inRange(local_image, low_th, high_th)
    return res

def filter_and_show(image, h, l, s, sobel_mag, sobel_angle, openingKernel=3):
    low_th = np.array([h[0], l[0], s[0]])
    high_th = np.array([h[1], l[1], s[1]])
    hlsRes   = hls_convert_and_filter(image, h_ch, l_ch, s_ch)
    sobel_res = sobel_mag_dir_treshold(image, sobel_kernel=ksize, 
                                        mag_thresh=sobel_mag, dir_thresh=sobel_angle)
    opening_ker = np.ones((6, 6), np.uint8)
    closing_ker = np.ones((10, 10), np.uint8)
    sobel_res = cv2.morphologyEx(sobel_res, cv2.MORPH_OPEN, opening_ker)
    sobel_res = cv2.morphologyEx(sobel_res, cv2.MORPH_CLOSE, closing_ker)

    combined_picture = np.zeros_like(image)
    combined_picture[:, :, 0] = hlsRes
    combined_picture[:, :, 1] = sobel_res
    combined_picture[:, :, 2] = 0
    
    print(sobel_mag, " | ", sobel_angle)

    cv2.imshow(filter_window_name, combined_picture)
    # cv2.waitKey(0)

def hls_h_min_ch_trackbar(val):
    global h_ch
    h_ch[0] = val
    filter_and_show(image, h_ch, l_ch, s_ch, sobel_mag, sobel_ang)

def hls_h_max_ch_trackbar(val):
    global h_ch
    h_ch[1] = val
    filter_and_show(image, h_ch, l_ch, s_ch, sobel_mag, sobel_ang)

def hls_l_min_ch_trackbar(val):
    global l_ch
    l_ch[0] = val
    filter_and_show(image, h_ch, l_ch, s_ch, sobel_mag, sobel_ang)

def hls_l_max_ch_trackbar(val):
    global l_ch
    l_ch[1] = val
    filter_and_show(image, h_ch, l_ch, s_ch, sobel_mag, sobel_ang)

def hls_s_min_ch_trackbar(val):
    global s_ch
    s_ch[0] = val
    filter_and_show(image, h_ch, l_ch, s_ch, sobel_mag, sobel_ang)

def hls_s_max_ch_trackbar(val):
    global s_ch
    s_ch[1] = val
    filter_and_show(image, h_ch, l_ch, s_ch, sobel_mag, sobel_ang)

def on_sobel_mag_min_trackbar(val):
    global sobel_mag
    sobel_mag[0] = val
    filter_and_show(image, h_ch, l_ch, s_ch, sobel_mag, sobel_ang)

def on_sobel_mag_max_trackbar(val):
    global sobel_mag
    sobel_mag[1] = val
    filter_and_show(image, h_ch, l_ch, s_ch, sobel_mag, sobel_ang)

def on_sobel_ang_min_trackbar(val):
    global sobel_ang
    sobel_ang[0] = np.radians(val - 90)
    filter_and_show(image, h_ch, l_ch, s_ch, sobel_mag, sobel_ang)

def on_sobel_ang_max_trackbar(val):
    global sobel_ang
    sobel_ang[1] = np.radians(val - 90)
    filter_and_show(image, h_ch, l_ch, s_ch, sobel_mag, sobel_ang)

def opening_kernel_trackbar(val):
    global oks
    #  = val
    oks = np.ones((val, val), np.uint8)
    filter_and_show(image, h_ch, l_ch, s_ch, sobel_mag, sobel_ang, oks)

def adjuct_filter_parameters(input_image):
    global image
    image = np.copy(input_image)
    image = cv2.blur(image, (5,5))

    filter_window_name = "Filtering"
    cv2.namedWindow(filter_window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(filter_window_name, 700, 500)
    trackbarHMinName = "H min"
    trackbarHMaxName = "H max"
    trackbarLMinName = "L min"
    trackbarLMaxName = "L max"
    trackbarsMinName = "S min"
    trackbarsMaxName = "S max"

    trackbarMagMinName = "Min mag"
    trackbarMagMaxName = "Max mag"
    trackbarAngMinName = "Min angle"
    trackbarAngMaxName = "Max angle"

    trackbarOpenKernelName = "Open/Close Kernel"

    cv2.createTrackbar(trackbarHMinName, filter_window_name, 0, 180, hls_h_min_ch_trackbar)
    cv2.createTrackbar(trackbarHMaxName, filter_window_name, 0, 180, hls_h_max_ch_trackbar)
    cv2.createTrackbar(trackbarLMinName, filter_window_name, 0, 255, hls_l_min_ch_trackbar)
    cv2.createTrackbar(trackbarLMaxName, filter_window_name, 0, 255, hls_l_max_ch_trackbar)
    cv2.createTrackbar(trackbarsMinName, filter_window_name, 0, 255, hls_s_min_ch_trackbar)
    cv2.createTrackbar(trackbarsMaxName, filter_window_name, 0, 255, hls_s_max_ch_trackbar)
    cv2.setTrackbarPos(trackbarHMinName, filter_window_name, h_ch[0])
    cv2.setTrackbarPos(trackbarHMaxName, filter_window_name, h_ch[1])
    cv2.setTrackbarPos(trackbarLMinName, filter_window_name, l_ch[0])
    cv2.setTrackbarPos(trackbarLMaxName, filter_window_name, l_ch[1])
    cv2.setTrackbarPos(trackbarsMinName, filter_window_name, s_ch[0])
    cv2.setTrackbarPos(trackbarsMaxName, filter_window_name, s_ch[1])

    cv2.createTrackbar(trackbarMagMinName, filter_window_name, 0, 255, on_sobel_mag_min_trackbar)
    cv2.createTrackbar(trackbarMagMaxName, filter_window_name, 0, 255, on_sobel_mag_max_trackbar)
    cv2.createTrackbar(trackbarAngMinName, filter_window_name, 0, 180, on_sobel_ang_min_trackbar)
    cv2.createTrackbar(trackbarAngMaxName, filter_window_name, 0, 180, on_sobel_ang_max_trackbar)
    cv2.setTrackbarPos(trackbarMagMinName, filter_window_name, sobel_mag[0])
    cv2.setTrackbarPos(trackbarMagMaxName, filter_window_name, sobel_mag[1])
    cv2.setTrackbarPos(trackbarAngMinName, filter_window_name, int(sobel_ang[0] * 180 / np.pi + 90))
    cv2.setTrackbarPos(trackbarAngMaxName, filter_window_name, int(sobel_ang[1] * 180 / np.pi + 90))
    
    cv2.createTrackbar(trackbarOpenKernelName, filter_window_name, 0, 35, opening_kernel_trackbar)
    cv2.setTrackbarPos(trackbarOpenKernelName, filter_window_name, 3)

    cv2.waitKey(0)