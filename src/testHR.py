from pylsl import StreamInlet, resolve_stream
import pylsl as lsl
from pylsl import StreamInfo, StreamOutlet, local_clock
from rtqrs import RTQRS
from rtqrs import RTQRS
import numpy as np
import time
import matplotlib.pyplot as plt
from utils import *

def main():
    ecg_data_path = 'src/csv/ecg_data_1.csv'
    ecg_data_raw = np.loadtxt(ecg_data_path, skiprows = 1, delimiter = ',')
    datos_ecg = ecg_data_raw[:, 1]
    print(ecg_data_raw.shape)
    manuDetector = RTQRS(sizeBuffer=250, overlap=50)
    lastRR = 0
    rr_aux = 0
    list_RR = [0, 0, 0, 0, 0, 0, 0]
    paso = 200
    datos = []
    lsl_hr = StreamOutlet(
        StreamInfo('T3_HR', 'biosignal:HR', 1, lsl.IRREGULAR_RATE, 'float32', 'OWN'))
    lsl_ecg = StreamOutlet(
        StreamInfo('T3_ECG', 'biosignal:ECG', 1, lsl.IRREGULAR_RATE, 'float32', 'OWN'))
    c = 0
    c_hr = 0
    inicio = time.time()
    for e in datos_ecg:
        c += 1
        datos.append(e)
        lsl_ecg.push_sample([e])

        print(len(datos))
        if len(datos) >= 250:
            res = manuDetector.realTimeQRSDetection(np.array(datos))

            if len(res) > 0:
                for element in res:
                    rr_aux = list_RR.pop(0)
                    rr_aux = 12480 / (element - lastRR)
                    list_RR.append(rr_aux)
                    lsl_hr.push_sample([np.median(list_RR)])
                    if lastRR>50:
                        rango = range(lastRR-50, element + 51)
                        datos_ecg_grafica = datos_ecg[lastRR-50:element + 51]
                    elif lastRR<0:
                        rango = range(0, element + 51)
                        datos_ecg_grafica = datos_ecg[0:element + 51]
                    else:
                        rango = range(lastRR, element + 51)
                        datos_ecg_grafica = datos_ecg[lastRR:element + 51]
                    plt.figure()
                    plt.plot(rango, datos_ecg_grafica)
                    plt.plot([lastRR, element], [datos_ecg[lastRR], datos_ecg[element]], 'x') if lastRR > 0 else plt.plot([0, element], [datos_ecg[0], datos_ecg[element]], 'x')
                    plt.show()
                    lastRR = element
                    c_hr += 1
            if lastRR > 210:
                datos = []
                lastRR -= 250
            else:
                datos = datos[200:250]
                lastRR -= 200
        print("Tiempo:" , time.time() - inicio)
        print(c_hr)


if __name__ == '__main__':
    main()
