import glob
import sys
import time

import tensorflow as tf
import cv2
import shutil
import os
import socket as sct
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import subprocess
import platform

if platform.system() == "Darwin":
    os.environ['KMP_DUPLICATE_LIB_OK'] = 'True'

MODE = 1
DROP_RATE = 0.15
UNITS = 4096
POO = 0
INIT_FILTERS = 32
BATCH_SIZE = 16


class MyMainWindow(QMainWindow):
    def __init__(self, *argv, **keywords):
        super(MyMainWindow, self).__init__()
        self.sscore = 0
        self.cmd = "afplay" if platform.system() == "Darwin" else "aplay"
        self.initUI(argv[0], argv[1])

    def initUI(self, model_dir, sound_dir):
        self.setGeometry(300, 150, 200, 0)
        self.setWindowTitle('SituationScore')
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.show()

        self.process = CalcSituationScore(model_dir, sound_dir)
        self.process.printThread.connect(self.setSituationScore)
        if not self.process.isRunning():
            self.process.start()

        timer = QTimer(self)
        timer.timeout.connect(self.showSituationScore)
        timer.start(100)  # msec

        soundtimer = QTimer(self)
        soundtimer.timeout.connect(self.playAudienceSound)
        soundtimer.start(5000)  # msec

        soundtimer2 = QTimer(self)
        soundtimer2.timeout.connect(self.playExcitementSound)
        soundtimer2.start(500)  # msec

    def setSituationScore(self, sscore):
        self.sscore = float(sscore)

    def showSituationScore(self):
        palette = QPalette()
        if float(self.sscore) > 0:
            palette.setColor(QPalette.Background, QColor(255, 255, 255 - float(self.sscore) * 2.55))
        elif float(self.sscore) <= 0:
            palette.setColor(QPalette.Background,
                             QColor(255, 255 - float(self.sscore) * -2.55, 255 - float(self.sscore) * -2.5))
        else:
            palette.setColor(QPalette.Background, QColor(0, 0, 0))

        self.setPalette(palette)
        displayed_sscore = str(int(self.sscore))

        if "-" in str(displayed_sscore):
            displayed_sscore = displayed_sscore.replace("-", "&lt;&lt; ")
        elif displayed_sscore == "0":
            pass
        else:
            displayed_sscore += " &gt;&gt;"
        label = QLabel('<p><font size="128"><center>' + displayed_sscore + '</center></font></p>')
        self.setCentralWidget(label)

    def playAudienceSound(self):
        # default spectator's voice
        subprocess.call(self.cmd + " " + sound_dir + "default.wav &", shell=True)

    def playExcitementSound(self):
        # excitement sound
        if int(self.sscore) >= 90 or int(self.sscore) <= -90:
            subprocess.call(self.cmd + " " + sound_dir + "goal.wav &", shell=True)
        elif int(self.sscore) >= 70:
            subprocess.call(self.cmd + " " + sound_dir + "left.wav &", shell=True)
        elif int(self.sscore) <= -70:
            subprocess.call(self.cmd + " " + sound_dir + "right.wav &", shell=True)


class CalcSituationScore(QThread):
    printThread = pyqtSignal(str)

    def __init__(self, model_dir, sound_dir, parent=None):
        QThread.__init__(self, parent)

        self.model_dir = model_dir
        self.sound_dir = sound_dir

    def run(self):
        # Lea Eisti 2018

        # 1 - We restore the model and the graph
        graph = tf.Graph()
        with graph.as_default():
            with open(model_dir + 'model.pb', 'rb') as f:
                graph_def = tf.GraphDef()
                graph_def.ParseFromString(f.read())
                tf.import_graph_def(graph_def, name='')

                # 2 - We start the server
                """We create the socket :
                socket = socket.socket(family, type);
                socket : socket descriptor, an integer
                family : integer, communication domain (AF_INET : IPv4 addresses)
                type : communication type (SOCK_STREAM : connection-based service, TCP socket)
                return -1 if fail. """
                socket = sct.socket(sct.AF_INET, sct.SOCK_STREAM)
                # 2020-10-30: fukushima ""->"127.0.0.1"
                socket.bind(('127.0.0.1', 15555))

                # We load the values of variables from the graph
                with tf.Session() as sess:
                    while True:
                        # socket.listen(queueLimit);
                        # Enable a server to accept connection.
                        #   queuelen : integer, number of active participants that can wait for a connection
                        #   return 0 if listeningm -1 if error
                        # 2020-10-30: fukushima 5->1
                        socket.listen(1)

                        # client, addr = socket.accept()
                        #   Accept a connection. Return a tuple.
                        #   client : the new socket used for data-transfer
                        #   addr : address bound to the socket on the other end of the connection
                        client, address = socket.accept()

                        # print " {} connected".format( address )

                        # client.recv(bufsize)
                        #   Receive data from the socket. The maximum amount of data to be received at once is bufsize
                        #   Return the data receive.
                        dirname = client.recv(4096).decode("utf-8")

                        # We create a directory to move the image already evaluated
                        dest = dirname + "-Done"
                        if not os.path.exists(dest):
                            os.mkdir(dest)

                        # Image directory
                        validation_images = []

                        # for image_name in sorted(glob.glob(dirname + "/*")):
                        #   validation_images.append(image_name)
                        # 2020-10-30:fukushima modified
                        image_name_list = sorted(glob.glob(dirname + "/*"))
                        if len(image_name_list) == 0:
                            continue
                        validation_images.append(image_name_list[-1])
                        ###
                        L = len(validation_images)

                        total_logits = [0.0 for i in range(L)]

                        # L : images number in the directory
                        # In this case, if the program is running normaly, we only have one image in the directory.
                        # But if we have delay, we can evaluate the previous images too.
                        for i in range(L):
                            batch = []
                            # im is the image number one
                            im = validation_images[i]
                            # we add the reading of the image to batch
                            # cv2.imread : read an image
                            batch.append(cv2.imread(im))

                            # logits/BiasAdd:0 : output
                            # sess.run return the first parameter, here logits
                            # 'Placeholder:0': batch = data
                            # 'Placeholder_3:0':False = not training
                            try:
                                batch_logits = sess.run('logits/BiasAdd:0', feed_dict={'Placeholder:0': batch,
                                                                                       'Placeholder_3:0': False})
                            except ValueError:
                                print("image:{} something wrong. skip...".format(im))
                                # We move this image
                                try:
                                    shutil.move(im, dest)
                                    # print ("Move")
                                except:
                                    print("Move error")
                                continue

                            if batch_logits[0][i] < 100:
                                total_logits[i] = int(batch_logits[0][i]) - 100
                                if total_logits[i] < -100:
                                    total_logits[i] = -100
                            else:
                                total_logits[i] = int(batch_logits[0][i]) - 99
                                if total_logits[i] > 100:
                                    total_logits[i] = 100

                            # We move the image already evaluated
                            try:
                                shutil.move(im, dest)
                                # print ("Move")
                            except Exception:
                                print("Move error")

                            # print ("sscore : ",total_logits[i])

                            # visualize in this phase
                            self.printThread.emit(str(total_logits[i]))

                    # We close the client and socket
                    client.close()
                    socket.close()


def showWindow(model_dir, sound_dir):
    app = QApplication(sys.argv)
    w = MyMainWindow(model_dir, sound_dir)
    sys.exit(app.exec_())


if __name__ == '__main__':
    model_dir = "./spectator/src/model/"
    sound_dir = "./spectator/src/sound-effect/"
    # model_dir = "./model/"
    # sound_dir = "./sound-effect/"
    showWindow(model_dir, sound_dir)
