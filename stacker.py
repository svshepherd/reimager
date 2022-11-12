import numpy as np
import os
from PIL import Image
import cv2
import colorcet as cc

def pic_stack(TARGET_FOLDER, COLORSHIFT=0, PALETTE='colorwheel'):
    '''
    COLORSHIFT = 0 for none, 1 for v1 or 2 for v2
    PALETTE = 'colorwheel' #'colorwheel'|'isolum'|'rainbow' 
    '''

    TARGET_FOLDER = os.path.abspath(TARGET_FOLDER)
    flist = [f for f in os.listdir(TARGET_FOLDER)]
    n_im = len(flist)

    im = 0*cv2.imread(os.path.join(TARGET_FOLDER,flist[0]),cv2.IMREAD_COLOR)
    if COLORSHIFT==1:
        hsv_part = 255*np.ones(im.shape).astype('uint8')
    im = im.astype('float64')

    for n,f in enumerate(flist):
        if not COLORSHIFT:
            img = cv2.imread(os.path.join(TARGET_FOLDER,f),cv2.IMREAD_COLOR).astype('float64')/255/n_im
            im += img
        else:
            img = cv2.imread(os.path.join(TARGET_FOLDER,f),cv2.IMREAD_GRAYSCALE).astype('float64')/255/n_im
            if COLORSHIFT==1:
                img = np.stack([img,img,img],axis=-1)
                hsv_part[:,:,0] = (255*n/n_im) # still uint8
                im += img*cv2.cvtColor(hsv_part.astype('uint8'), cv2.COLOR_HSV2BGR).astype('float64')/255
            elif COLORSHIFT==2:
                rgba_cmap = cc.cm[PALETTE](int(255*n/len(flist)))
                cmap = (rgba_cmap[2], rgba_cmap[1], rgba_cmap[0])
                im += np.stack([img*cmap[0],img*cmap[1],img*cmap[2]],axis=-1)
            else:
                raise
    if COLORSHIFT:
        lab = cv2.cvtColor((255*im).astype('uint8'), cv2.COLOR_BGR2LAB)
        lab[:,:,0] -= lab[:,:,0].min()
        lab[:,:,0] = ( lab[:,:,0].astype(float) * 255 / lab[:,:,0].max() ).round().astype(int)
        for layer in 1,2:
            lab_layer = lab[:,:,layer].astype('float')
            lab_layer -= lab_layer.mean()
            # for whatever reason this performed poorly:
            #lab_layer -= (lab_layer*lab[:,:,0]).sum()/lab[:,:,0].sum() 
            lab_layer = 127.5*lab_layer/abs(lab_layer).max()+127.5
            lab_layer = lab_layer.round().astype('uint8')
            lab[:,:,layer] = lab_layer
        img = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
        cv2.imwrite(f'mergedim.png',img)
    else:
        cv2.imwrite(f'mergedim.png',(255*im).astype('uint8'))