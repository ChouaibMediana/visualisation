import numpy as np
import skimage
from skimage.io import imread, imshow
from skimage.transform import resize
import os 
import tensorflow as tf
import keras
from tensorflow.keras.models import Sequential
from sklearn.model_selection import train_test_split

def imageResize(img):
    img_res = resize(img,(64,64),anti_aliasing=True)
    img_flat = img_res.flatten() /255.0 
    return img_flat



def create_model():
    output_neurons = 1
    neurons_hidden_layer_1 = 1024
    neurons_hidden_layer_2 = 512
    model = Sequential()
    model.add(keras.layers.Input(shape=(4096,)))
    model.add(keras.layers.Dense(neurons_hidden_layer_1,activation='relu'))
    model.add(keras.layers.Dense(neurons_hidden_layer_2,activation='relu'))
    model.add(keras.layers.Dense(output_neurons,activation="sigmoid"))
    model.compile(loss='binary_crossentropy',optimizer='adam',metrics=['accuracy'])
    return model

def getData(target_folder):
    X=[]
    y=[]
    for foldername in os.listdir(target_folder):
        if(foldername =="Normal"):
            label = 0
        else:
            label = 1
        for iname in  os.listdir(target_folder+'/'+foldername):
            img= imread(target_folder+"/"+foldername+"/"+iname,as_gray=True)#as_gray=True
            img_flat = imageResize(img)
            X.append(img_flat)
            y.append(label)
    return np.array(X),np.array(y)

if __name__ == "__main__":
    train_dir = os.path.join(os.path.dirname(__file__), "Dataset/chest_xray/train")
    base_dir = os.path.dirname(__file__)
    X_train,y_train = getData(train_dir)
    X_train = X_train/X_train.max()
    X_train ,X_val ,y_train,y_val = train_test_split(X_train,y_train , test_size = 0.2, stratify = y_train, random_state = 42)
    model = create_model()
    history = model.fit(X_train,y_train,validation_data=(X_val,y_val),epochs=50,batch_size=128)
    model.save(base_dir+"/imageclassifier.keras")