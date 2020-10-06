from scipy import misc
# import Tkinter as tk
import glob
import numpy as np
import time
import sys
import tensorflow as tf
import cv2
import csv
from array import array
import shutil
import os
import socket as sct
from tensorflow.python.framework import graph_util
from PyQt5 import QtTest
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import threading
from multiprocessing import Value
import subprocess


import datetime

MODE = 1
DROP_RATE = 0.15
UNITS = 4096
POO = 0
INIT_FILTERS = 32
BATCH_SIZE = 16


class MyMainWindow(QMainWindow):
    def __init__(self, *argv, **keywords ):
        super(MyMainWindow,self).__init__(*argv,**keywords)
        self.initUI()

    def initUI(self):
        self.setGeometry(300, 150, 200, 0)
        self.setWindowTitle('SituationScore')
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.show()

        timer = QTimer(self)
        timer.timeout.connect(self.showSituationScore)
        timer.start(100) #msec

        soundtimer = QTimer(self)
        soundtimer.timeout.connect(self.playAudienceSound)
        soundtimer.start(5000) #msec

    def showSituationScore(self):
        palette = QPalette()
        if float(sscore.value) > 0:
            palette.setColor(QPalette.Background,QColor(255,255,255 - float(sscore.value)*2.55))
        elif float(sscore.value) <= 0:
            palette.setColor(QPalette.Background,QColor(255,255-float(sscore.value)*-2.55,255-float(sscore.value)*-2.5))
        else:
            palette.setColor(QPalette.Background,QColor(0, 0, 0))

        self.setPalette(palette)
        label = QLabel('<p><font size="128"><center>'+str(sscore.value)+'</center></font></p>')
        self.setCentralWidget(label)

    def playAudienceSound(self):
        # default spectator's voice
        subprocess.call("aplay -q " + sound_dir + "default.wav &", shell=True)



def calcSituationScore(sscore, model_dir, sound_dir):

    # 1 - We restore the model and the graph
    graph = tf.Graph()
    with graph.as_default():

        with open(model_dir + 'model.pb', 'rb') as f:
            graph_def = tf.GraphDef()
            graph_def.ParseFromString(f.read())
            tf.import_graph_def(graph_def, name='')


        # Lea Eisti 2018

        # 2 - We start the server

        """We create the socket :
        socket = socket.socket(family, type);
        socket : socket descriptor, an integer
        family : integer, communication domain (AF_INET : IPv4 addresses)
        type : communication type (SOCK_STREAM : connection-based service, TCP socket)
        return -1 if fail. """
        socket = sct.socket(sct.AF_INET, sct.SOCK_STREAM)
        socket.bind(('', 15555))


        # We load the values of variables from the graph
        with tf.Session() as sess:
            while True:
                # socket.listen(queueLimit);
                # Enable a server to accept connection.
                #   queuelen : integer, number of active participants that can wait for a connection
                #   return 0 if listeningm -1 if error
                socket.listen(5)

                # client, addr = socket.accept()
                #   Accept a connection. Return a tuple.
                #   client : the new socket used for data-transfer
                #   addr : address bound to the socket on the other end of the connection
                client, address = socket.accept()

                # print " {} connected".format( address )

                # client.recv(bufsize)
                #   Receive data from the socket. The maximum amount of data to be received at once is bufsize
                #   Return the data receive.
                dirname = client.recv(4096)

                # We create a directory to move the image already evaluated
                if not os.path.exists(dirname + "-Done"):
                    os.mkdir(dirname + "-Done")

                #Image directory
                validation_images = []
                for image_name in glob.glob(dirname + "/*"):
                    validation_images.append(image_name)

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
                    batch_logits = sess.run('logits/BiasAdd:0', feed_dict={'Placeholder:0': batch, 'Placeholder_3:0':False})

                    if batch_logits < 100:
                        total_logits[i] = int(round(batch_logits)) - 100
                        if total_logits[i] < -100:
                            total_logits[i] = -100
                    else:
                        total_logits[i] = int(round(batch_logits)) - 99
                        if total_logits[i] > 100:
                            total_logits[i] = 100

                    dest = dirname + "-Done"

                    # We move the image already evaluated
                    try:
                        shutil.move(im,dest)
                        #print ("Move")
                    except:
                        print ("Move error")


                    #print ("sscore : ",total_logits[i])

                    # visualize in this phase
                    sscore.value = int(total_logits[i])
                    if int(total_logits[i]) >= 90 or int(total_logits[i]) <= -90:
                        subprocess.call("aplay " + sound_dir + "goal.wav &", shell=True)
                    elif int(total_logits[i]) >= 70:
                        subprocess.call("aplay " + sound_dir + "left.wav &", shell=True)
                    elif int(total_logits[i]) <= -70:
                        subprocess.call("aplay " + sound_dir + "right.wav &", shell=True)

            # We close the client and socket
            client.close()
            stock.close()


def showWindow(sscore, sound_dir):
    app = QApplication(sys.argv)
    w = MyMainWindow()
    sys.exit(app.exec_())


if __name__ == '__main__':
    model_dir = "./spectator/src/model/"
    sound_dir = "./spectator/src/sound-effect/"

    sscore = Value('i', 0)
    thread_1 = threading.Thread(target=showWindow, args=[sscore, sound_dir])
    thread_2 = threading.Thread(target=calcSituationScore, args=[sscore, model_dir, sound_dir])
    thread_1.start()
    thread_2.start()
