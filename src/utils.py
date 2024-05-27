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


def accRead(br: bytearray) -> list:
    """Convierte un bytearray en una lista de aceleraciones en g (float)"""

    mr = bytearray2int16list(br)
    m_ret = [accint162float32(element) for element in mr]
    return m_ret


def accint162float32(value) -> float:
    """Convierte un entero de 16 bits en un float de 32 bits"""

    return float(value) * 4.0 / 32768.0      # Rango de medición de ±4g. Además, 32768 = 1024 * 32


def gyrRead(br: bytearray) -> list:
    """Convierte un bytearray en una lista de velocidades angulares en grados por segundo (float)"""

    mr = bytearray2int16list(br)
    m_ret = [gyrint162float32(element) for element in mr]
    return m_ret


def gyrint162float32(value) -> float:
    """Convierte un entero de 16 bits en un float de 32 bits"""

    return float(value) * 2000.0 / 32768.0      # Rango de medición de ±2000 grados por segundo. Además, 32768 = 1024 * 32


def batRead(br: bytearray) -> list:
    """Convierte un bytearray en una lista de niveles de batería en porcentaje (float)"""

    mr = list()
    br2 = len(br)
    for j in range(0, br2 >> 1):
        aux = br[2 * j:2 * j + 2]
        mf = int.from_bytes(aux, byteorder='little', signed=False)
        ax = float(mf) * 3.3 / 1023.0           # Lectura de un convertidor analógico-digital de 10 bits con referencia a 3.3V
        ax = 5 * ax / 3                         # 0V = 0%, 3V = 100%
        mr.append(ax)
    return mr


def stRead(br: bytearray) -> list:
    """Convierte un bytearray en una lista de temperaturas de la piel en grados Celsius (float)"""

    mr = list()
    br2 = len(br)
    for j in range(0, br2 >> 1):
        aux = br[2 * j:2 * j + 2]
        mf = int.from_bytes(aux, byteorder='little', signed=False)
        mr.append(mf)
    # TODO: conversión de uint16 a ºC
    m_ret = [float(element) for element in mr]  # * 100.0 / 1024.0 for element in mr]
    return m_ret


def taRead(br: bytearray) -> list:
    """Convierte un bytearray en una lista de temperaturas ambientales en grados Celsius (float)"""
    
    mr = bytearray2uint16list(br)
    m_ret = [float(element) / 16.0 + 25 for element in mr]      # Escala de 16 bits, 0 = 25ºC, 16 = 26ºC...
    return m_ret

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

    def __str__(self):
        return (f"blemanager(id={self.id}, address={self.address}" 
        f", eda_config={self.eda_config}, lsl_acc={self.lsl_acc}, lsl_hr={self.lsl_hr}, lsl_bat={self.lsl_bat}"
        f", lsl_br={self.lsl_br}, lsl_ecg={self.lsl_ecg}, lsl_eda={self.lsl_eda}, lsl_gyr={self.lsl_gyr}, lsl_st={self.lsl_st}" 
        f", lsl_ta={self.lsl_ta}, lsl_eda_config={self.lsl_eda_config})")
    
    def setData(self, data):
        self.data = data

    def setHandle(self, handle):
        self.handle = handle
    
