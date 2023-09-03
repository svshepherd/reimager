## gist is I'd like to look at exif 
## and prepend YYYYmmdd to the filename
## overwriting nothing

## should be safe

from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import requests
import os
import datetime

## now I'd like to learn when the photos were taken and prefix that date (if necessary) 
## in my standard format
def extract_date_taken(file):
    """this looks like it's doing a better job than my original method 
    for extracting date_taken, independent of subsequent edits."""
    image = Image.open(file)

    # Extract EXIF data
    exif_data = image._getexif()
    if exif_data is not None:
        for tag, value in exif_data.items():
            tag_name = TAGS.get(tag, tag)
            if tag_name == "DateTimeOriginal":
                # Convert the date format from string to datetime
                date_time_obj = datetime.datetime.strptime(value, '%Y:%m:%d %H:%M:%S')
                return date_time_obj
    return None

if __name__ == '__main__':

    ## I'd like to assume this is the same directory from which the shortcut is clicked
    PATHNAME = r'F:\extended_desktop\viz'

    ## I'd like to display the files that will be affected, just to be careful
    files = [f for f in os.listdir(PATHNAME) if os.path.isfile(os.path.join(PATHNAME, f))] 
    files

    ## Now I'd like to execute (and report) file name changes:
    for file in files:
        try:
            day = extract_date_taken(os.path.join(PATHNAME, file))
            day_prefix = f"{day:%Y%m%d}"
            if file.endswith('.ARW'):
                continue
            elif file.startswith(day_prefix):
                print(file, "===== ALREADY GOOD!!")
                continue
            else:
                newname = day_prefix+" "+file
                os.rename(os.path.join(PATHNAME, file), os.path.join(PATHNAME, newname))
                print(file, "---->", newname, "SUCCESSFUL")
        except Exception as e:
            print(file, "----X", e)   
        # if file[4]+file[7]=='--':
        #     newname = file[:4]+file[5:7]+file[8:]
        #     os.rename(os.path.join(PATHNAME, file), os.path.join(PATHNAME, newname))
        #     print(file, "---->", newname, "SUCCESSFUL")
        # elif file.startswith('PXL_'):
        #     newname = file[4:]
        #     os.rename(os.path.join(PATHNAME, file), os.path.join(PATHNAME, newname))
        #     print(file, "---->", newname, "SUCCESSFUL")
        # elif file.startswith('D')|file.startswith('P')|file.startswith('W'):
        #     try: 
        #         img = Image.open(os.path.join(PATHNAME, file))
        #         img_exif = img.getexif()
        #         ## [(k,v) for k,v in ExifTags.TAGS.items() if 'date' in v.lower()] ### 36867, 36868, 306
        #         ### evidently I also need to think about OffsetTime from GMT
        #         if 36867 in img_exif.keys():
        #             imname_pref = ''.join(img_exif[36867][:10].split(':'))+' '
        #         elif 36868 in img_exif.keys():
        #             imname_pref = ''.join(img_exif[36868][:10].split(':'))+' '
        #         else:
        #             imname_pref = ''.join(img_exif[306][:10].split(':'))+' '
        #         img.close()
        #         if imname_pref == file[:9]:
        #             print(file, "----=", file)
        #             try:
        #                 fileraw = file[9:].replace('.JPG','.ARW')
        #                 os.rename(os.path.join(PATHNAME, fileraw), os.path.join(PATHNAME, imname_pref + fileraw))
        #                 print(fileraw, "---->", imname_pref + fileraw, "SUCCESSFUL")
        #             except Exception as e:
        #                 print(e)
        #         else:
        #             print(file, "---->", imname_pref + file)
        #             os.rename(os.path.join(PATHNAME, file), os.path.join(PATHNAME, imname_pref + file))
        #             print(file, "---->", imname_pref + file, "SUCCESSFUL")
        #             try:
        #                 fileraw = file.replace('.JPG','.ARW')
        #                 os.rename(os.path.join(PATHNAME, fileraw), os.path.join(PATHNAME, imname_pref + fileraw))
        #                 print(fileraw, "---->", imname_pref + fileraw, "SUCCESSFUL")
        #             except Exception as e:
        #                 print(e + '.')
        #     except Exception as e:
        #         print(file, "----X", e)
        # else: 
        #     print('  already processed or unanticipated name format: ', file)