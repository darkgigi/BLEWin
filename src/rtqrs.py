import numpy as np
from collections import deque
from time import gmtime, strftime

import scipy.interpolate
from scipy import signal
# from sklearn.cluster import KMeans
import math


class RTQRS(object):
    """
        Authors:    Manuel Merino-Monge (manmermon@dte.us.es);
                    Isabel M. Gómez-González (igomez@us.es);
                    Alberto J. Molina-Cantero (almolina@us.es)
                    Juan A. Castro-García (jacastro@us.es)

        Based on:  Merino, M., Gómez, I. M., & Molina, A. J. (2015).
                    Envelopment filter and K-means for the detection of QRS waveforms in electrocardiogram.
                    Medical Engineering and Physics. https://doi.org/10.1016/j.medengphy.2015.03.019

        ----------------------------------------------------------------------------
        "THE BEER-WARE LICENSE" (Revision 42):
        Merino-Monge wrote this file.  As long as you retain this notice you
        can do whatever you want with this stuff. If we meet some day, and you think
        this stuff is worth it, you can buy me a beer in return.
        ----------------------------------------------------------------------------
    """

    def __init__(self, sizeBuffer: int = 64, overlap: int = 32, fs: float = 208, meanfilterorder: int = 3,
                 envelopmentfilterorder: int = 2):
        """
        RTQRS class initialisation method.
        :param int sizeBuffer: Buffer's length (in samples)
        :param int overlap: Overlap's length (in samples)
        :param float fs: sampling frequency (Hz)
        :param in filterOrder: order of the filter
        """
        self.sizeBuffer = sizeBuffer
        self.overlap = overlap
        self.fs = fs
        self.meanfilterorder = meanfilterorder
        self.envelopmentfilterorder = envelopmentfilterorder

        self.myBuffer = [0.0] * self.sizeBuffer
        # self.centroids = [0.0, 0.0] ## comentado por MMM
        # self.countPlot = 0
        # self.initCentroids = False ## comentado por MMM
        self.countSamples = 0
        # self.qrsValues=0
        # self.nQRSValues = 0
        # self.kmean = KMeans(n_clusters=2)
        # self.kmean.fit([[0, 1],[0, 10]])

        # self.centroids = [0, 100] ## comentado por MMM
        self.centroids = []  ## Puesto por MMM
        self.prevQRSInOverlapArea = False  ## Puesto por MMM

        self.a = 0
        self.b = 0
        self.bandpass_filter_creator(lowcut=1, highcut=30, signal_freq=self.fs, filter_order=3)

    def realTimeQRSDetection(self, buffer):
        laux = len(buffer)
        bfil = buffer  # self.bandpass_filter_app(buffer)
        base = 10
        # self.centroids = [0, 100] ## comentado por MMM
        if laux > self.sizeBuffer:
            return np.array([])
        else:
            if laux == self.sizeBuffer:
                self.myBuffer = bfil
            else:
                self.myBuffer[0:self.sizeBuffer - laux] = self.myBuffer[laux:self.sizeBuffer]
                self.myBuffer[self.sizeBuffer - laux:self.sizeBuffer] = bfil

        self.countSamples = self.countSamples + laux

        self.myBuffer = self.bandpass_filter_app(self.myBuffer)
        bfil = self.myBuffer

        # Processing
        f = self.mean_filter(self.myBuffer)
        filteredECG = self.envelopment_filter(f)
        qrs1 = self.myBuffer - filteredECG
        qrs2 = self.mean_filter(qrs1)
        qrs = qrs2 - self.envelopment_filter(qrs2)
        ### comentarios MMM
        # locs = signal.find_peaks_cwt(qrs,np.arange(1,self.overlap)) # Por que con wavelet?
        locs = signal.find_peaks(qrs)[0]  # este es el que yo uso en matlab
        pks = qrs[locs]
        self.myBuffer = bfil
        labels = self.myKMeans(pks)
        if len(labels) > 0:
            aux = np.zeros((1, len(locs)))
            # pos = locs[(labels == 1)[0]] # label == 1 -> QRS candidate
            pos = np.argwhere((labels == 1)[0])  # label == 1 -> QRS candidate
            idx = 1

            while idx < len(pos):
                # df = np.diff(qrs[ pos[idx-1]:pos[idx]]) ## comentada por MMM
                df = np.diff(qrs[(locs[pos[idx - 1]][0]): (locs[pos[idx]][0])])  ## añadida por MMM
                sdf = df[0:len(df) - 1] * df[1:len(df)]
                sdf = np.concatenate((sdf, [0]))

                if sum(df[sdf < 0] < 0) == 1:
                    # aux[0,idx] = -1 ## comentada por MMM
                    aux[0, pos[idx][0]] = -1  ## añadida por MMM
                    idx = idx + 1

                idx = idx + 1

            if len(pos) > 0:  # and pos[0] < 18: # 18 por que???? ### comentarios MMM
                aux[0, 0] = -1
            labels[aux == -1] = 0
            qrs_pos = locs[(labels == 1)[0]]

            ## -> Añadido por MMM
            if self.prevQRSInOverlapArea:
                qrs_pos = qrs_pos[qrs_pos >= self.overlap]  # Eliminamos los QRS en la zona de solapamiento

            # comprobamos y registramos si hay algun QRS en la zona de solapamiento de la siguiente ventana
            self.prevQRSInOverlapArea = any(qrs_pos >= (self.sizeBuffer - self.overlap))
            ## <-

            return qrs_pos

    def bandpass_filter_creator(self, lowcut, highcut, signal_freq, filter_order):
        """
        Method responsible for creating and applying Butterworth filter.
        :param float lowcut: filter lowcut frequency value
        :param float highcut: filter highcut frequency value
        :param int signal_freq: signal frequency in samples per second (Hz)
        :param int filter_order: filter order
        :return b and a arrays
        JACG
        """
        nyquist_freq = 0.5 * signal_freq
        low = lowcut / nyquist_freq  # <- No se usa (MMM)
        high = highcut / nyquist_freq
        b, a = signal.butter(filter_order, [high], btype="low")
        self.b = b
        self.a = a

    def bandpass_filter_app(self, data):
        y = signal.lfilter(self.b, self.a, data)
        return y

    def mean_filter(self, buffer):
        y = [0] * len(buffer)
        lbuffer = len(buffer)
        size = self.meanfilterorder
        msize = size - math.floor(size / 2)
        idx = 0
        for element in range(msize, size + 1):
            # y[idx] = sum(buffer[0:idx+1])/element ## comentada por MMM
            y[idx] = sum(buffer[0: element]) / element
            idx = idx + 1
        for element in range(size, lbuffer):
            # y[idx] = sum( buffer[ element-size : element ] ) / size ### comentada por MMM
            y[idx] = ((y[idx - 1] * size) - buffer[element - size] + buffer[element]) / size
            idx = idx + 1
        """
        # comentado por MMM
        #
        idx = len(y)
        for element in range(1,size-msize+1):
            y[idx-element] = sum(buffer[lbuffer-size+element:lbuffer])/(size-element)
            idx = idx + 1
        #print(y)
        """
        idx = lbuffer - msize + 1
        for element in range(1, msize):
            y[idx] = sum(buffer[(lbuffer - size + element): lbuffer]) / (size - element);
            idx = idx + 1
        return y

    def envelopment_filter(self, buffer):
        if len(buffer) < 2:
            return buffer
        y = [0] * len(buffer)
        data = buffer.copy()
        for element in range(0, self.envelopmentfilterorder):
            e1 = self.envelopment(data)
            e2 = self.envelopment(e1)
            y = y + ((e1 + e2) / 2)
            data = data - y

        return y

    def envelopment(self, buffer):
        df = np.diff(buffer)
        buf = np.array(buffer)
        extrema = np.where((df[1:len(df)] * df[0:len(df) - 1]) <= 0)[0]
        # up = np.concatenate((np.concatenate(([0],(extrema[df[extrema]>=0])+1)),[len(buffer)-1]))
        bottom = np.concatenate((np.concatenate(([0], (extrema[df[extrema] < 0]) + 1)), [len(buffer) - 1]))
        # i_up = scipy.interpolate.pchip_interpolate(up,buffer[up],list(range(0,len(buffer))))
        i_bottom = scipy.interpolate.pchip_interpolate(bottom, buf[bottom], list(range(0, len(buffer))))
        return i_bottom
        # return i_up, i_bottom

    def cond_min_eq(self, x):
        return x <= 0

    def cond_min(self, x):
        return x < 0

    def cond_may_eq(self, x):
        return x >= 0

    def myKMeans(self, data):
        if len(data) > 0:
            dt = np.array(data)
            data_len = len(data)
            labels = np.ones((1, data_len))
            distances = np.zeros((2, data_len))  # distance[fil,centroid]
            # ->añadido MMM
            if len(self.centroids) < 2:
                self.centroids = np.quantile(data, [0.25, 0.75])
            # <-
            check = True
            while check:
                t_labels = labels.copy()
                for idx in range(0, data_len):
                    distances[0, idx] = abs(dt[idx] - self.centroids[0])
                    distances[1, idx] = abs(dt[idx] - self.centroids[1])
                    t_labels[0, idx] = np.argmin(distances[:, idx])

                check = np.sum((labels - t_labels) ** 2) != 0
                if check is not False:
                    labels = t_labels
                    """
                    ## comentado por MMM
                    ax = dt[(labels == 0)[0]]
                    if len(ax) > 0:
                        self.centroids[0]= (np.mean(ax)+self.centroids[0])/2
                    ax = dt[(labels == 1)[0]]
                    if len(ax) > 0:
                        self.centroids[1] = (np.mean(ax) + self.centroids[1]) / 2
                    """
                    ## Añadido por MMM
                    ax = dt[(labels == 0)[0]]
                    if len(ax) > 0:
                        self.centroids[0] = np.median(ax)
                    ax = dt[(labels == 1)[0]]
                    if len(ax) > 0:
                        self.centroids[1] = np.median(ax)

            if self.centroids[0] > self.centroids[1]:
                t_labels = labels.copy()
                labels[t_labels == 0] = 1
                labels[t_labels == 1] = 0
                x = self.centroids[0]
                self.centroids[0] = self.centroids[1]
                self.centroids[1] = x
            return labels
        else:
            return []




















