import clis_data
from matplotlib import pyplot as plt
import numpy as np

clis = clis_data.ClisData()
colors = ['blue', 'green', 'red']
def gen_graph(file):

    data = clis.importData('src/records/' + file + '.clis')
    print(data)
    values = data[file.replace('data_lab', 'data')]

    dim = values.shape

    for i in range( 0, dim[ -1 ]-1 ):
        c = values[ :, i ]
        c = c[ ~np.isnan( c ) ]

        plt.plot(c, colors[i])
        plt.title(['data Simulation ' + file ])
    plt.show()

gen_graph('data_lab_T3_ECG')
