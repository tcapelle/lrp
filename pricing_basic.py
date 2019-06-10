import networkx as nx
import time

def pd(G):
    '''G es un Grafo dirigido del tipo de nuestro pricing
    El label esta simplificado con:
    E.g. Para un grafo con 20 clientes (22 nodos),
    L = [0,2,7,12,17,21, 212, 725,3]
        [0,2,7,12,17,21] corresponde a la label
        212 al costo
        725 al tiempo 
        3 carga del vehiculo
    '''    
    
    source = 0
    weight = 'd'
    target = G.order()-1
    N = G.order()
    P = range(1,N/2)
    D = range(N/2,N-1)

    caminos = []

    S0 = [0 ,0, 0, 0] #[primeros l-2 elementos es la label, costo, tiempo]
    h = [S0] #lista de labels
    estados = 0
    t = 0
    l = 1
    while h:

        label= h.pop()
        v = label[-4]  #nodo terminal de la label actual
        vecinos = G[v].keys()
        edges = possible_edges(vecinos, label[0:-3], P, D, label[-1])

        for w in edges:
            c_vw = G[v][w][weight]
            t_vw = G[v][w]['t']
            cost = label[-2] + c_vw
            t = label[-1] + t_vw
            if (t <= G.node[w]['u']):
                if (t <= G.node[w]['l']):    # lo puedo agregar!
                    t = G.node[w]['l']
                labelN = label[0:-3]
                labelN.append(w)
                labelN.append(cost)
                labelN.append(t)
                if w in P:
                    labelN.append(label[-1]+1)
                if w in D:
                    labelN.append(label[-1]-1)
                if w == target:
                    labelN.append(0)
                    caminos.append(labelN)
                else:
                    h.append(labelN)
            estados += 1

    return caminos, estados


def possible_edges(V, R, P, D, q):
    '''entrega los posibles vecinos con respecto a la ruta actual
    V: es el conjutno de vecinos G[v].keys()
    R: es la ruta actual
    P: son los pickups 
    D: los deliverys
        Para resumir, la funcion devuelve los pickups que no estan
        acualmente en el vehiculo, los deliverys que el correspondiente
        pickup esta en al vehiculo, intersectado con los nodos vecinos
        del nodo terminal de la ruta.
    q: la carga del vehiculo
    '''
    terminal = len(P)*2+1      

    pickup_posibles = []
    for x in P:
        if x not in R:
            pickup_posibles.append(x)

    delivery_posibles = []
    for x in D:
        if x not in R and x-len(P) in R:
            delivery_posibles.append(x)
    if q == 0:
        delivery_posibles.append(terminal)

    aux = pickup_posibles + delivery_posibles

    return [x for x in aux if x in V]

def possible_edges_bis(V, R, P, D, q):
    '''entrega los posibles vecinos con respecto a la ruta actual
    V: es el conjutno de vecinos G[v].keys()
    R: es la ruta actual
    P: son los pickups 
    D: los deliverys
        Para resumir, la funcion devuelve los pickups que no estan
        acualmente en el vehiculo, los deliverys que el correspondiente
        pickup esta en al vehiculo, intersectado con los nodos vecinos
        del nodo terminal de la ruta.
    q: la carga del vehiculo
    '''
    terminal = len(P)*2+1      

    pickup_posibles = [x for x in P if x not in R]

    delivery_posibles = [x for x in D if x not in R and x-len(P) in R]

    if q == 0: #auto vacio, pa la casa
        delivery_posibles.append(terminal)

    aux = pickup_posibles + delivery_posibles

    return [x for x in aux if x in V]

if __name__=='__main__':
    G = nx.read_gpickle("test_graph_small")
    pd(G)

