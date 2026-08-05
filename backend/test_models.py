import cv2
from tensorflow.keras.models import load_model
from pathlib import Path

print('cv2 version:', cv2.__version__)
# face detector
fp = Path('models/deploy.prototxt')
fm = Path('models/res10_300x300_ssd_iter_140000.caffemodel')
print('face proto exists:', fp.exists(), 'face model exists:', fm.exists())
try:
    net = cv2.dnn.readNet(str(fp), str(fm))
    print('face net loaded OK')
except Exception as e:
    print('face net load error:', e)

# age
ap = Path('models/age_deploy.prototxt')
am = Path('models/age_net.caffemodel')
print('age proto exists:', ap.exists(), 'age model exists:', am.exists())
try:
    age_net = cv2.dnn.readNet(str(ap), str(am))
    print('age net loaded OK')
except Exception as e:
    print('age net load error:', e)

# mask
mp = Path('models/mask_detector.model')
print('mask model exists:', mp.exists())
try:
    m = load_model(str(mp))
    print('mask model loaded OK')
except Exception as e:
    print('mask model load error:', e)
