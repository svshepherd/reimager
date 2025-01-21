"""the purpose of this program is to fix the damned stupid fact that my camera images, 
saved via Seek rather than the camera roll, keep geotagging but mysteriously lose 
timestamps! note that *if* this works, it only works for very basic Exif data"""

import piexif

import os
from shutil import move
#from pprint import pprint

if __name__ == '__main__':

    os.chdir(r'C:\Users\svs\Desktop\ims\fix_ts')

    for i in [i for i in os.listdir() if i[-4:]=='.jpg'] :
        if (i[4],i[7]) != ('-','-') :
            pprint('no')
            continue
        #pprint( 'move( ' + i + ', (' + i[0:4] + i[5:7] + i[8:] + ') )' )
        filename = i
        exif_dict = piexif.load(filename)
        exif_dict["Exif"][36867] = \
            filename[:-4].replace("-",":").replace(".",":")
            # NOTE: "The character string length is 20 bytes including NULL 
            # for termination." - https://www.awaresystems.be/imaging/tiff/tifftags/privateifd/exif/datetimeoriginal.html
            # ...BUT seems to be okay
        exif_bytes = piexif.dump(exif_dict)
        piexif.insert(exif_bytes, filename)
        move( i, (i[0:4]+i[5:7]+i[8:]) )