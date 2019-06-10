"""Read data from a file."""
import networkx as nx
import matplotlib.pyplot as plt
import math
import random
from Plot import *
from Procedimientos import *


def get_words(line):
    """Return a list of the tokens in line."""
    line = line.replace("\t", " ")
    line = line.replace("\v", " ")
    line = line.replace("\r", " ")
    line = line.replace("\n", " ")
    while line.count("  "):
        line = line.replace("  ", " ")
    line = line.strip()
    return [word + " " for word in line.split(" ")]


def read_dat_file(filename):
    f = open(filename)
    ret = []
    continuation = False
    first_line=f.readline()
    # print first_line
    aux,n,aux2,cap,aux3=[eval(x) for x in get_words(first_line)]
    # print n, cap
    for line in f:
        node=[]
        for word in get_words(line):
            if continuation:
                entity = "".join([entity, word])
            else:
                entity = word
            try:
                node.append(eval(entity))
                continuation = False
            except SyntaxError:
                continuation = True
        ret.append(node)
    return n,cap,ret

def generate(file1,file2,path,ropke,costo_r=100):
    print 'Please include the DEPOT.instance file with out any modifier'
    extension='.instance'
    n,cap,ret       =   read_dat_file(path+file1+extension)    #archivo de instancia   
    n2, cap2, ret2  =   read_dat_file(path+file2+extension)    #archivo de depots
    
    

    n_clientes=n
    n_depots=n2 
    
    M=n_clientes*2 +n_depots
    # print M
    # print ret
    G=nx.DiGraph(nx.complete_graph(M))
    pos=zip(zip(*ret)[1:3][0],zip(*ret)[1:3][1])

##se cargan los depots
    
    for i in range(n_depots):
        id,xi,yi,service,demandi,li,ui=ret2[i]
        G.add_node(i,x=xi,y=yi,tipo='terminal',l=li,u=ui)
        
##se carga el grafo de Ropke

    for i in range(n_depots,M):
        id,xi,yi,service,demandi,li,ui=ret[i-n_depots+1]
        G.add_node(i,x=xi,y=yi,l=li,u=ui,demand=demandi)

            
            
    for i in G:
        for j in G[i]:
            xi=G.node[i]['x']
            yi=G.node[i]['y']
            xj=G.node[j]['x']
            yj=G.node[j]['y']
            dij=math.hypot(xi-xj,yi-yj)
            tij=dij
            G.add_edge(i,j,d=dij,t=tij)
            
    for i in range(n_depots):
        for j in G[i]:
            G.add_edge(i,j,d=G[i][j]['d'])

    #labels +i, -i
    for i in range(n_depots,n_depots+n_clientes):
        G.add_node(i,tipo=i-(n_depots-1))
        
    for i in range(n_depots+n_clientes,M):
        G.add_node(i,tipo=-(i-(n_depots+n_clientes-1)))      
    
    s=path+file1
    
    for i in range(n_depots):
        Subgrafo_depot2(G,i,s,ropke,costo_r)
         
    
    nx.write_gpickle(G,s+'.gpickle')
    Plot_grafo(G,False,s)
        
    return G

def Subgrafo_depot(G,D,s,ropke):
    nodos=[D]
    
    for n in G:
        if G.node[n]['tipo']!='terminal':
           nodos.append(n)
           
    H=G.subgraph(nodos)
    
    H=nx.convert_node_labels_to_integers(H)
    N=H.order()
    H.add_node(N,H.node[0].copy())

# the two-liner version 
    for u,v,d in H.edges(0,data=True): 
        H.add_edge(v,N,d) # makes a copy of the data 


    if ropke:
        for j in H[0]:
            H.add_edge(0,j,d=100+H[0][j]['d'])
        
    nx.write_gpickle(H,s+'_Depot%d.gpickle'%D)        
    return H

def Subgrafo_depot2(G,D,s,ropke, costo_r=100):
    """ incluye la posibilidad de definir un costo de ruta r
    """
    nodos=[D]
    
    for n in G:
        if G.node[n]['tipo']!='terminal':
           nodos.append(n)
           
    H=G.subgraph(nodos)
    
    H=nx.convert_node_labels_to_integers(H)
    N=H.order()
    H.add_node(N,H.node[0].copy())

# the two-liner version 
    for u,v,d in H.edges(0,data=True): 
        H.add_edge(v,N,d) # makes a copy of the data 


    if ropke:
        for j in H[0]:
            H.add_edge(0,j,d=costo_r+H[0][j]['d'])
        
    nx.write_gpickle(H,s+'_Depot%d.gpickle'%D)        
    return H
