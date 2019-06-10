import sys
from LRP import LRP
import numpy as np

'''
Para usar este script debes poner en el path, los archivos:
prefix+num_clientes+version.instance (ej: AA40_1.instance)
Depots_1.instance

Una vez ejecutado
'''

if __name__=='__main__':

####EJEMPLO:
    '''Esto va a correr la instancia AA5_1.instance,
    localizada en el path = GEO_0/W_30_Q_15/
    Va a generar todos los archivos necesarios (grafos
        intermediarios, auxiliares, graficos, etc..)
    con la condicion de no incluir el costo de 100 a
    cada vehiculo (ropke = False)
    Si no estas seguro de lo que hace, borra todos los archivos
    en el path, salvo los terminados en .instance
    '''


    # plr = LRP(  path = 'GEO_0/W_30_Q_15/', #path a los archivos AA5_1.instance y DEPOTS_1.instance
    #             prefix= 'AA',
    #             num_clientes = 5, #cantidad de clientes
    #             num_depots = 7, #cantidad de depots
    #             Q = 15, #Capacidad vehiculo
    #             version = '1', #version de la isntancia, ej: AA40_1
    #             costo_depot = 2, #el costo de apertura de cada depot
    #             ropke = False)  #si se agrega un costo fijo de 100 a cada vehiculo

    # plr.branch_and_price()


###FIN EJEMPLO
    vv = int(sys.argv[1])

    for rr in [1,10,50,100,200]:
    #for rr in [1]:
         #for v in [30,35,40,45,50,55,60,65,70,75]: #20,21
         for v in [vv]:
             #for c in [5]:
             for c in [0.1, 1, 10, 50, 100, 200]:
                 print "------>Corriendo Instancias con c = %s"%c
                 #plr = LRP(  path = 'RC-AA-1D2', #path a los archivos AA5_1.instance y DEPOTS_1.instance
                 plr = LRP(  path = 'corridas5/W_30_Q_15r'+str(rr), #path a los archivos AA5_1.instance y DEPOTS_1.instance
                     prefix= 'AA',
                     num_clientes = 40, #cantidad de clientes
                     num_depots = 7, #cantidad de depots
                     Q = 15, #Capacidad vehiculo
                     W = 45, #Ancho de la ventana de tiempo
                     version = str(v), #version de la isntancia, ej: AA40_1
                     costo_depot = c, #el costo de apertura de cada depot
                     ropke = True, #si se agrega un costo fijo a cada vehiculo
                     costo_r = rr)  #valor del costo fijo por cada vehiculo
                 print("\n------ Iniciando instancia -------------")
                 print("r = " + str(rr) + "  mapa = " + str(v) + "  c = " + str(c) + "\n\n")

                 plr.branch_and_price(nodos_parada = 20000, gap = 0.005)


