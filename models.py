# -*- coding: utf-8 -*-
"""Copy of models.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1pihJj4lx__XUOdoD09j05cvmv6K9TyVd
"""

from google.colab import drive
import os
def mountDir(dir, subdir = '', path = 'drive/My Drive/'):
  
    drive.mount('/content/drive')
    print(os.getcwd())
    if subdir == '':
        os.chdir(path + dir)
    else:        
        os.chdir(path + dir + '/' + subdir)
    print(os.getcwd())
    # !ls -la

def storeData(data, filename, ext = '.pkl'):

    pickle.dump(data, open(filename + ext, 'wb') )  
    print(filename + ext + ' saved!')

def loadData(filename, ext = '.pkl'):     

    filename += ext
    data = pickle.load(open(filename, 'rb'))  
    print(filename, ' loaded!')
    
    return data
mountDir('IRProject')

import numpy as np
import pandas as pd
import pickle
from tqdm import tqdm
import cv2
from google.colab.patches import cv2_imshow # because cv2.imshow does'nt work in colab
from matplotlib import pyplot as plt

paths = loadData('path_holiday.list', '')
# paths = loadData('path_shoe.list', '')

"""Get Features from new image"""

def histogram(image, bins = 10):
    # convert the image to HSV color-space
    image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    # compute the color histogram
    hist  = cv2.calcHist([image], [0, 1, 2], None, [bins, bins, bins], [0, 256, 0, 256, 0, 256])
    # normalize the histogram
    cv2.normalize(hist, hist)
    # return the histogram
    return hist.flatten()

def hu_moments(image):
    # image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    feature = cv2.HuMoments(cv2.moments(image)).flatten()
    return feature

!pip install mahotas
import mahotas
# feature-descriptor-2: Haralick Texture
def haralick(image):
    # convert the image to grayscale
    # gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # compute the haralick texture feature vector
    haralick = mahotas.features.haralick(image).mean(axis=0)
    # return the result
    return haralick

from skimage.feature import hog

def hog_f(image):
    fd, hog_image = hog(image, orientations=9, pixels_per_cell=(8, 8),cells_per_block=(2, 2), visualize=True, multichannel=True)
    return fd

def preprocess_image(img):
    # img = cv2.imread(path)                 #original image
    img2 = np.invert(img)                  #invert image
    gray = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
    img2 = cv2.Canny(gray, threshold1=30, threshold2=100)    #edge detection
    img2 = cv2.GaussianBlur(img2,(5,5),cv2.BORDER_DEFAULT) #gaussian blur 
    ret, img2 = cv2.threshold(img2, 1, 255, cv2.THRESH_BINARY)     #thresholding 
    img2 = cv2.adaptiveThreshold(img2 ,255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 255, 1)
    img2 = np.invert(img2)
    temp = tuple(img2 for i in range(3))
    temp = np.dstack(temp)
    image = cv2.subtract(img, temp)
    return image

def Histogram(image, mask):
    hist = cv2.calcHist([image], [0, 1, 2], mask, (8, 12, 3), [0, 180, 0, 256, 0, 256])
    hist = cv2.normalize(hist, hist).flatten()
    return hist

def get_feature(image):

    # image = cv2.imread(path)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    feature = []
    (h, w) = image.shape[:2]
    (cX, cY) = (int(w * 0.5), int(h * 0.5))
    segments = [(0, cX, 0, cY), (cX, w, 0, cY), (cX, w, cY, h),(0, cX, cY, h)]
    (axesX, axesY) = (int(w * 0.75) // 2, int(h * 0.75) // 2)
        
    ellipMask = np.zeros(image.shape[:2], dtype = "uint8")
    cornerMask = np.zeros(image.shape[:2], dtype = "uint8")
    cv2.ellipse(ellipMask, (cX, cY), (axesX, axesY), 0, 0, 360, 255, -1)
        
    for (startX, endX, startY, endY) in segments:
        cv2.rectangle(cornerMask, (startX, startY), (endX, endY), 255, -1)
        cornerMask = cv2.subtract(cornerMask, ellipMask)
        hist = Histogram(image, cornerMask)
        feature.extend(hist)
    hist = Histogram(image, ellipMask)
    return hist

# typ = 'shoe'
typ = 'holi'
# path = 'shoe1.jpg'
path = 'holi1.jpg'
img = cv2.imread(paths[0])
h0, b0, c = img.shape

feat = dict()

img = cv2.imread(path)
# cv2_imshow(img)
h, b = img.shape[:2]
if h > b:
    r = h0/h
else:
    r = b0/b
img = cv2.resize(img, (0,0), fx=r, fy=r)
x = int((img.shape[0] - h0)/2)
y = int((img.shape[1] - b0)/2)
img = img[x:x+h0,y:y+b0]
filename = path.split('.')[0] + '1.jpg'
cv2.imwrite(filename, img)
feat['color'] = img
grey = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
feat['hu'] = hu_moments(grey).tolist()
feat['haral'] = haralick(grey).tolist()
img = preprocess_image(img)
feat['hist'] = histogram(img).tolist()
feat['hog'] = hog_f(img).tolist()
feat['seghist'] = get_feature(img).tolist()

    # print(img.shape, cv2.imread(paths[0]).shape)

import numpy as np
from numpy import linalg as LA
from keras.applications.vgg16 import VGG16
from keras.preprocessing import image
from keras.applications.vgg16 import preprocess_input

class VGGNet:
    def __init__(self):
        # weights: 'imagenet'
        # pooling: 'max' or 'avg'
        # input_shape: (width, height, 3), width and height should >= 48
        self.input_shape = (240, 240, 3)
        self.weight = 'imagenet'
        self.pooling = 'max'
        self.model = VGG16(weights = self.weight, input_shape = (self.input_shape[0], self.input_shape[1], self.input_shape[2]), pooling = self.pooling, include_top = False)
        self.model.predict(np.zeros((1, 240, 240 , 3))) #change image size

    def extract_features(self, img_path):
        img = image.load_img(img_path, target_size=(self.input_shape[0], self.input_shape[1]))
        img = image.img_to_array(img)
        img = np.expand_dims(img, axis=0)
        img = preprocess_input(img)
        feat = self.model.predict(img)
        norm_feat = feat[0]/LA.norm(feat[0])
        return norm_feat

model=VGGNet()

features=model.extract_features('shoe1.jpg')

feat['vggfeat'] = features.tolist()
# features.tolist()

"""Load Features"""

# f = loadData('s_haral','.list')
# f = [f[i].tolist() for i in range(len(f))]
# storeData(f, 's_haral', '.list2')
# f = loadData('s_hist','.list')
# f = [f[i].tolist() for i in range(len(f))]
# storeData(f, 's_hist', '.list2')
# f = loadData('s_hog','.list')
# f = [f[i].tolist() for i in range(len(f))]
# storeData(f, 's_hog', '.list2')
# f = loadData('s_hu','.list')
# f = [f[i].tolist() for i in range(len(f))]
# storeData(f, 's_hu', '.list2')
# # f[0]

# f = loadData('h_seghist','.list')
# # f = [f[i].tolist() for i in range(len(f))]
# storeData(f, 'h_seghist', '.list2')
# f = loadData('s_seghist','.list')
# # f = [f[i].tolist() for i in range(len(f))]
# storeData(f, 's_seghist', '.list2')
# f = loadData('vgg_features','.sav')
# # f = [f[i].tolist() for i in range(len(f))]
# storeData(f, 's_vggfeat', '.list2')
# f = loadData('vgg_features_holiday','.sav')
# # f = [f[i].tolist() for i in range(len(f))]
# storeData(f, 'h_vggfeat', '.list2')

"""Stack Features"""

!ls *.list2

def stack_features(feature_set):
    fdic = dict()
    for feature in feature_set:
        fdic[feature] = loadData(feature, '.list2')
    return np.hstack(fdic.values())

def stack_testf(feature_set):
    fdic  =dict()
    for feature in feature_set:
        fdic[feature] = feat[feature.split('_')[-1]]
    return np.hstack(fdic.values())

tfe = stack_testf(['s_vggfeat', 's_hist' ])
tfe.shape

features = stack_features(['h_vggfeat', 'h_hist' ])
features.shape

"""Knn"""

from sklearn.neighbors import NearestNeighbors
# neigh = NearestNeighbors(n_neighbors=10)
# neigh.fit(features.s_f_prephist.values.tolist())
neigh = NearestNeighbors(n_neighbors=10, p= 2)
neigh.fit(features)

x = 5
n = 100
neighbours = neigh.kneighbors(features[x:x+1], n, return_distance=False)
# for i in neighbours.tolist()[0]:
#     cv2_imshow(cv2.imread(paths[i]))

bhak = {'knn' : neighbours.tolist()[0]}

"""Cosine"""

from sklearn.metrics.pairwise import cosine_similarity

n = 100
res = cosine_similarity(features, [features[78]], dense_output=True)
res = res.flatten()
res= pd.Series(res)

bhak['cos'] = res.nlargest(n).index.to_list()

# for i in res.nlargest(n).index.to_list():
#     cv2_imshow(cv2.imread(paths[i]))
# res

res.nlargest(n).index.to_list()

"""Voting"""

!ls *.list2

"""fset: list of feature sets for multiple knn models

pset: p value for metric evaluation of models

weights: importance of each knn (experimental)

x: index of image to search

n: #neighbours
"""

fset = [['h_vggfeat'], ['h_seghist','h_haral', 'h_hog'], ['h_hist','h_haral', 'h_hog']]
pset = [1,2, 3]
# weights = [1, 0.9, 0.8]
x = 78
n = 100

ndic = list()
for i in tqdm(range(len(fset))):
    features = features = stack_features(fset[i])
    neigh = NearestNeighbors(n_neighbors=10, p=pset[i])
    neigh.fit(features)
    neighbours = neigh.kneighbors(features[x:x+1], n, return_distance=False)
    ndic.append(neighbours.tolist()[0])
# pd.DataFrame(ndic)

flist = dict()
for j, ns in enumerate(ndic):
    for i in range(len(ns)):
        if ns[i] not in flist.keys():
            flist[ns[i]] = i
        else:
            flist[ns[i]] += i
res = [k[0] for k in sorted(flist.items(), key=lambda x: x[1])][:n]

# flist, ndic, res
bhak['vot'] = res

storeData(bhak, 'hoist')

for i in res:
    cv2_imshow(cv2.imread(paths[i]))
# res

