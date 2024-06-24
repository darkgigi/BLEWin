import numpy as np


def bytearray2uint16(br: bytearray) -> int:
    """Convierte un bytearray en un entero sin signo de 16 bits"""

    return int.from_bytes(br, byteorder='little', signed=False)


def bytearray2uint16list(br: bytearray) -> list:
    """Convierte un bytearray en una lista de enteros sin signo de 16 bits"""

    mr = list()
    br2 = len(br)
    for j in range(0, br2 >> 1):
        aux = br[2 * j:2 * j + 2]
        mf = bytearray2uint16(aux)
        mr.append(mf)

    return mr


def bytearray2int16(br: bytearray) -> int:
    """Convierte un bytearray en un entero de 16 bits"""

    return int.from_bytes(br, byteorder='little', signed=True)


def bytearray2int16list(br: bytearray) -> list:
    """Convierte un bytearray en una lista de enteros de 16 bits"""

    mr = list()
    br2 = len(br)
    for j in range(0, br2 >> 1):
        aux = br[2 * j:2 * j + 2]
        mf = bytearray2int16(aux)
        mr.append(mf)

    return mr


def acc_read(br: bytearray) -> list:
    """Convierte un bytearray en una lista de aceleraciones en g (float)"""

    mr = bytearray2int16list(br)
    m_ret = [accint162float32(element) for element in mr]
    return m_ret


def accint162float32(value) -> float:
    """Convierte un entero de 16 bits en un float de 32 bits"""

    return float(value) * 4.0 / 32768.0      # Rango de medición de ±4g. Además, 32768 = 1024 * 32


def gyr_read(br: bytearray) -> list:
    """Convierte un bytearray en una lista de velocidades angulares en grados por segundo (float)"""

    mr = bytearray2int16list(br)
    m_ret = [gyrint162float32(element) for element in mr]
    return m_ret


def gyrint162float32(value) -> float:
    """Convierte un entero de 16 bits en un float de 32 bits"""

    return float(value) * 2000.0 / 32768.0      # Rango de medición de ±2000 grados por segundo. Además, 32768 = 1024 * 32


def bat_read(br: bytearray) -> list:
    """Convierte un bytearray en una lista de niveles de batería en porcentaje (float)"""

    mr = list()
    br2 = len(br)
    for j in range(0, br2 >> 1):
        aux = br[2 * j:2 * j + 2]
        mf = int.from_bytes(aux, byteorder='little', signed=False)
        ax = float(mf) * 3.3 / 1023.0           # Lectura de un convertidor analógico-digital de 10 bits con referencia a 3.3V
        ax = 5 * ax / 3                         
        mr.append(ax)
    return mr


def st_read(br: bytearray) -> list:
    """Convierte un bytearray en una lista de temperaturas de la piel en grados Celsius (float)"""

    mr = list()
    br2 = len(br)
    for j in range(0, br2 >> 1):
        aux = br[2 * j:2 * j + 2]
        mf = int.from_bytes(aux, byteorder='little', signed=False)
        mr.append(mf)
    m_ret = [vto_celsius(float(element)) for element in mr]  # * 100.0 / 1024.0 for element in mr]
    return m_ret


def ta_read(br: bytearray) -> list:
    """Convierte un bytearray en una lista de temperaturas ambientales en grados Celsius (float)"""
    
    mr = bytearray2uint16list(br)
    m_ret = [float(element) / 16.0 + 25 for element in mr]      # Escala de 16 bits, 0 = 25ºC, 16 = 26ºC...
    return m_ret

def get_eda_siemens(eda, eda_config):
    r1 = 0
    if eda_config == 15:
        r1 = 30300
    elif eda_config == 1:
        r1 = 50000
    elif eda_config == 14:
        r1 = 77000
    elif eda_config == 2:
        r1 = 100000
    elif eda_config == 12:
        r1 = 333333
    elif eda_config == 4:
        r1 = 500000
    elif eda_config == 8:
        r1 = 1000000

    aux = float('nan')
    if eda_config != 8 or eda != 1023:
        aux = eda * eda_v.vcc / eda_v.max
        aux = ((eda_v.r2 * aux) / eda_v.r23) + eda_v.v2
        aux = r1 * aux / eda_v.vr
        aux = aux - r1
        aux = 1000000 / aux
    return aux

class eda_val():
    def __init__(self):
        self.vcc = 3.3
        self.max = 1023
        self.r2 = 470000
        self.r3 = 200000
        self.r23 = self.r2+self.r3
        self.vr = self.vcc/11
        self.v2 = self.vcc*330000/(800000+330000)
        self.rq = [1/51000, 1/100000, 1/500000, 1/1000000]

global eda_v

eda_v = eda_val()

def vto_celsius(adc: float) -> float:
    """Convierte la temperatura en grados Celsius"""

    v = 3.3 * adc / 1023
    try:
        rntc = ((237.60/(v+11.97)) -10)*1000
    except:
        print('Error en rntc')
    if rntc < 0:
        print(rntc)
        return 0
    try:
        invt=(np.log(rntc/10000)/3694) + (1/298)
    except:
        print('Error en invt')
        print(rntc)
    try:
        x = (1/invt) -273
    except:
        print('Error en x')
    return x

class blemanager():
    def __init__(self):
        self.id = None
        self.address = None
        self.name = None
        self.lsl_acc = None             #Accelerometer
        self.lsl_hr = None              #Heart rate
        self.lsl_bat = None             #Battery level
        self.lsl_br = None              #Breathing rate
        self.lsl_ecg = None             #Electrocardiogram
        self.lsl_eda = None             #Electrodermal activity
        self.lsl_gyr = None             #Gyroscope
        self.lsl_st = None              #Skin temperature
        self.lsl_ta = None              #Ambient temperature
        self.lsl_eda_config = None      #Electrodermal activity configuration
        self.lsl_tonic = None           #Electrodermal activity tonic component

    def __str__(self):
        return (f"blemanager(id={self.id}, address={self.address}" 
        f", lsl_acc={self.lsl_acc}, lsl_hr={self.lsl_hr}, lsl_bat={self.lsl_bat}"
        f", lsl_br={self.lsl_br}, lsl_ecg={self.lsl_ecg}, lsl_eda={self.lsl_eda}, lsl_gyr={self.lsl_gyr}, lsl_st={self.lsl_st}" 
        f", lsl_ta={self.lsl_ta}, lsl_eda_config={self.lsl_eda_config}, lsl_tonic={self.lsl_tonic})")
    
    def set_data(self, data):
        self.data = data

    def set_handle(self, handle):
        self.handle = handle
    
