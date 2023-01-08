import numpy as np
import cv2 as cv

# cap = cv.VideoCapture(0)

# while(cap.isOpened()):
#     ret, frame = cap.read()
#     if ret == True:
#         cv.imshow('frame',frame)
#     if cv.waitKey(1) & 0xFF == ord('q'):
#         break

# cap.release()
# cv.destoryAllwindows()

cap=cv.VideoCapture(0) #cv2.VideoCapture(0)代表调取摄像头资源，其中0代表电脑摄像头，1代表外接摄像头(usb摄像头)
cap.set(3,640)#宽
cap.set(4,480)#高
cap.set(10,100)#亮度
while True:
    success,img=cap.read()
    cv.imshow("Video",img)
    if cv.waitKey(1)&0xFF==ord('q'):
        break