"""gui for prefixing filenames with the 8-digit date taken."""

import os
import sys
#import shutil
#import requests
import datetime
from PyQt5.QtWidgets import QApplication, QFileDialog, QLabel, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt, QUrl
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS


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


class DropWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setAcceptDrops(True)
        self.label = QLabel('Drag and Drop Files Here', self)
        self.label.setAlignment(Qt.AlignCenter)
        layout = QVBoxLayout()
        layout.addWidget(self.label)
        self.setLayout(layout)
        self.resize(256, 256)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        image_files = [str(QUrl.toLocalFile(url)) for url in event.mimeData().urls()]

        ## Now I'd like to execute (and report) file name changes:
        for file in image_files:
            # split_name = file.split(os.sep) ### curious this doesn't work!
            split_name = file.split('/')
            path_name = os.sep.join(split_name[:-1])
            file_name = split_name[-1]
            try:
                day = extract_date_taken(file)
                day_prefix = f"{day:%Y%m%d}"
                if file_name.endswith('.ARW'):
                    continue
                elif file_name.startswith(day_prefix):
                    print(file_name, "===== ALREADY GOOD!!")
                    continue
                else:
                    new_name = day_prefix+" "+file_name
                    os.rename(os.path.join(path_name, file_name), os.path.join(path_name, new_name))
                    print(file_name, "---->", new_name, "SUCCESSFUL")
            except Exception as e:
                print(file, "----X", e)   


def main():
    app = QApplication(sys.argv)
    widget = DropWidget()
    widget.show()
    app.exec_()

if __name__ == '__main__':
    main()
    