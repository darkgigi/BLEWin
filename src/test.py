import ClisData
from matplotlib import pyplot as plt
import numpy as np

sufix = 'A'
name_type_3 = 'data_Simulation' + sufix
clis = ClisData.ClisData()

def test_bat_num_data(baterias, tiempos):

    dim_b = baterias.shape
    dim_t = tiempos.shape
    dimensiones_correctas = dim_b[0] == dim_t[0]
    print(f"La cantidad de marcas de tiempo y de datos de giroscopio es la misma: {dimensiones_correctas}")
    if not dimensiones_correctas:
        return
    
    first_time_data = list()
    for i in range( 0, dim_t[0]-1, 13):
        t = tiempos[i]
        t = t[~np.isnan(t)]
        first_time_data.append(t[0])
        
    num_incorrectos = []
    for time, next_time in zip(first_time_data, first_time_data[1:]):
        datos = []
        for i in range(0, dim_t[0]-1):
            if tiempos[i][0] >= time and tiempos[i][0]< next_time:
                datos.append(tiempos[i][0])
            if tiempos[i][0] == next_time:
                break
        if len(datos) != 13:
            num_incorrectos.append(f'Error, no hay 13 muestras en este intervalo de tiempo {time} - {next_time}')
    if len(num_incorrectos) == 0:
        print('Todos los intervalos de tiempo tienen 13 muestras de batería')
    else:
        for error in num_incorrectos:
            print(error)

def test_gyr_num_data(giroscopios, tiempos):

    dim_g = giroscopios.shape
    dim_t = tiempos.shape
    dimensiones_correctas = dim_g[0] == dim_t[0]
    print(f"La cantidad de marcas de tiempo y de datos de giroscopio es la misma: {dimensiones_correctas}")
    if not dimensiones_correctas:
        return
    
    first_time_data = list()
    for i in range( 0, dim_t[0]-1, 24):
        t = tiempos[i]
        t = t[~np.isnan(t)]
        first_time_data.append(t[0])
        
    num_incorrectos = []
    for time, next_time in zip(first_time_data, first_time_data[1:]):
        datos = []
        for i in range(0, dim_t[0]-1):
            if tiempos[i][0] >= time and tiempos[i][0]< next_time:
                datos.append(tiempos[i][0])
            if tiempos[i][0] == next_time:
                break
        if len(datos) != 24:
            num_incorrectos.append(f'Error, no hay 24 muestras en este intervalo de tiempo {time} - {next_time}')
    if len(num_incorrectos) == 0:
        print('Todos los intervalos de tiempo tienen 24 muestras del giroscopio')
    else:
        for error in num_incorrectos:
            print(error)

if __name__ == '__main__':
    name_type_1 = 'p2_Nano33IoT_Leg_BAT'
    name_type_2 = 'p2_Nano33IoT_Chest_BAT'
    name_type_3 = 'p2_Nano33IoT_Chest_BAT'

    f = 'src/records/' + name_type_1 + '.clis'
    f2 = 'src/records/' + name_type_2 + '.clis'
    f3 = 'src/records/' + name_type_3 + '.clis'
    
    d = clis.importData(f)
    d2 = clis.importData(f2)
    d3 = clis.importData(f3)

    print(f'Analizando {name_type_1}')
    baterias = d[name_type_1.replace('p2', 'data')]
    tiempos= d[name_type_1.replace('p2', 'time')]
    test_bat_num_data(baterias, tiempos)

    print()
    print(f'Analizando {name_type_2}')
    baterias = d2[name_type_2.replace('p2', 'data')]
    tiempos= d2[name_type_2.replace('p2', 'time')]
    test_bat_num_data(baterias, tiempos)

    print()
    print(f'Analizando {name_type_3}')
    baterias = d3[name_type_3.replace('p2', 'data')]
    tiempos= d3[name_type_3.replace('p2', 'time')]
    test_bat_num_data(baterias, tiempos)

    name_type_1 = 'p2_Nano33IoT_Leg_GYR'
    name_type_2 = 'p2_Nano33IoT_Wrist_GYR'
    name_type_3 = 'p2_Nano33IoT_Chest_GYR'

    f = 'src/records/' + name_type_1 + '.clis'
    f2 = 'src/records/' + name_type_2 + '.clis'
    f3 = 'src/records/' + name_type_3 + '.clis'

    d = clis.importData( f )
    d2 = clis.importData( f2 )
    d3 = clis.importData( f3 )

    print()
    print(f'Analizando {name_type_1}')
    giroscopios = d[name_type_1.replace('p2', 'data')]
    tiempos= d[name_type_1.replace('p2', 'time')]
    test_gyr_num_data(giroscopios, tiempos)

    print()
    print(f'Analizando {name_type_2}')
    giroscopios = d2[name_type_2.replace('p2', 'data')]
    tiempos= d2[name_type_2.replace('p2', 'time')]
    test_gyr_num_data(giroscopios, tiempos)

    print()
    print(f'Analizando {name_type_3}')
    giroscopios = d3[name_type_3.replace('p2', 'data')]
    tiempos= d3[name_type_3.replace('p2', 'time')]
    test_gyr_num_data(giroscopios, tiempos)

    
