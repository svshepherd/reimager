"""gui for resizing a group of image files to the size of their largest member."""

import os
import sys
import shutil
from PyQt5.QtWidgets import QApplication, QFileDialog, QLabel, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt, QUrl
from PIL import Image

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

        print(f'processing these images: {image_files}')

        # Initialize the maximum resolution
        max_res = (0, 0)

        # Find the maximum resolution
        for image_file in image_files:
            with Image.open(image_file) as img:
                width, height = img.size
                max_res = (max(max_res[0], width), max(max_res[1], height))
        print(f'upscale to max resolution: {max_res}')

        # Rescale each image to the maximum resolution
        for image_file in image_files:
            # # Backup the original file
            # backup_file = image_file + '.bak'
            # if os.path.exists(backup_file):
            #     i = 1
            #     while os.path.exists(backup_file + str(i)):
            #         i += 1
            #     backup_file += str(i)
            # shutil.copy(image_file, backup_file)

            print(f'...{image_file}...')
            with Image.open(image_file) as img:
                resized_img = img.resize(max_res, Image.LANCZOS)
                ## I'd like to add a _ before the filename in the image_file name which includes the path.
                #new_name = image_file.split(os.sep)
                new_name = image_file.split('/')
                new_name[-1] = '_'+new_name[-1]
                #new_name = os.sep.join(new_name)
                new_name = '/'.join(new_name)
                ##
                resized_img.save(new_name)

def main():
    app = QApplication(sys.argv)
    widget = DropWidget()
    widget.show()
    app.exec_()

if __name__ == '__main__':
    main()