import cv2

face_proto = "models/deploy.prototxt"
face_model = "models/res10_300x300_ssd_iter_140000.caffemodel"

print("Loading model...")
net = cv2.dnn.readNet(face_proto, face_model)
print("Model loaded successfully!")
