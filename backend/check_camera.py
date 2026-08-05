import cv2
cap = cv2.VideoCapture(0)
print('cap.isOpened():', cap.isOpened())
ret, frame = cap.read()
print('read ret:', ret)
if ret:
    print('frame shape:', getattr(frame, 'shape', None))
cap.release()
