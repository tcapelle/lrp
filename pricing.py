import sys
(0, '/usr/local/lib')


import cplex
from cplex.exceptions import CplexError
from cplex.exceptions import CplexSolverError
from cplex import SparsePair



import networkx as nx
import time
from Clases import *
from multiprocessing import Pool
import random


Q=15

GRAN_CONTADOR = 180000

def intersect(a, b):
     return list(set(a).intersection(set(b)))
def dif(U,a):
    return list(set(U).difference(set(a)))

def pd3(obj): #version Diciembre
    G=obj[0]
    calidad=obj[1]  
    weight='d'
    target=G.order()-1
    tiem=time.time()
    tr=time.clock()
    M=G.order()
    N=M-2
    P=range(1,N/2+1)
    #print P
    D=range(N/2+1,N+1)
    #print D
    Caminos=[]
    n=0
    t=0
    l=0
    c=0
    V=[]
    O=[]
    S0=Label(n,t,l,c,V,O,'source')
    h=[S0]
    negatives=[]
    contador=0
    
    if calidad==-1:
        return [],-1
    while h:
        #h=h[0:500]    
        L=h.pop(0)
        if L!=0:

            
            i=L.node()
            
            if len(negatives)>400 or contador>150000:
                break
            if i==target:
                #print 'voy en el label ' +str(L)
                #print L.ruta()

                negatives.append(L)

            else:
                #print P
                #print list(set(P).intersection(set(G[i].keys())-set(L.V)))
                #print [x+N/2 for x in L.O]
                edges=G[i].keys()#list(set(list(set(P).intersection(set(G[i].keys())-set(L.V)))+[x+N/2 for x in L.O]).intersection(set(G[i].keys())))
                #print edges
                #if len(L.O)==0 and len(L.V)>0:
                #    edges.append(target)
    
                h=h+map(extend2,[L]*len(edges),edges)
                #for j in edges:
                    #print 'extendiendo '+str(L)+' a %d'%j
                #    h.append(extend(L,j))
        contador=contador+1
    neg_rut=[x.ruta() for x in negatives]
    
    print 'Total de Rutas finales: %d' %len(neg_rut)
    print 'Tiempo total empleado (Real, CPU): (%d,%d)' %(-tiem+time.time(),-tr+time.clock())
    print '---------------------------SOLUCION'
    print 'Contador: %d'%contador

    return neg_rut,calidad



def pd2(obj):# G es un Grafo, source es el nodo origen, target el nodo destino, time es True si se usa el TW, weight es un string con el nombre del costo    
    
    G=obj[0]
    lar=obj[1]
    source=0
    weight='d'
    usa_tw=True
    target=G.order()-1
    
    tiem=time.time()
    tr=time.clock()
    Tmin=nx.all_pairs_dijkstra_path_length(G,'t')
    M=G.order()
    N=M-2
    P=range(1,N/2+1)
    #print P
    #print P
    D=range(N/2+1,N+1)
    #print D
    #print D
    Caminos=[]

     #arreglo vacio =)
    S0=Ruta(source,[source],0,0,2)
    h=[[S0]]
    estados=0
    g={}
    t=0
    l=1
#    for k in range(1,M+1): #k es el largo de la ruta
    for k in range(1,lar): #k es el largo de la ruta        
        # print 'Rutas de largo %d'%k
        for f in h:
            while f:
                ruta=f.pop(0)
                #print ruta
                v=ruta.terminal()   
                vecinos=G[v].keys()
                edges=precedencia(N,G[v],ruta.visitados(),v)
                #print ruta
                for w in edges:
                    #print v,w
                    c_vw=G[v][w][weight]
                    t_vw=G[v][w]['t']
                    cost = ruta.costo() +c_vw
                    t=ruta.tiempo()+t_vw
                    #print w
                    if usa_tw:  #Uso el TW
                        if (t<=G.node[w]['u']):
                            if (t<=G.node[w]['l']):    # lo puedo agregar!
                                t=G.node[w]['l']
                            if w in P:  
                                # print w  
                                if ((t+Tmin[w][w+N/2]<=G.node[w+N/2]['u']) and (t+Tmin[w][w+N/2]+Tmin[w+N/2][N+1]<=G.node[N+1]['u'])): #Puedo alcanzar el delivery en el tiempo
                                    estados=estados+1
                                    rutaN=Ruta(w,ruta.visitados()+[w],t,cost,ruta.iden()+2*(10**w)-1*(10**ruta.terminal()))
                                    #print rutaN
                                    if rutaN.iden() in g:
                                       g[rutaN.iden()].append(rutaN)
                                    else:
                                       g[rutaN.iden()]=[rutaN]
                            else:
                                estados=estados+1
                                rutaN=Ruta(w,ruta.visitados()+[w],t,cost,ruta.iden()+2*(10**w)-1*(10**ruta.terminal()))
                                #print rutaN
                                if rutaN.iden() in g:
                                    g[rutaN.iden()].append(rutaN)
                                else:
                                    g[rutaN.iden()]=[rutaN]    
                                if rutaN.terminal()==target:
                                    Caminos.append(rutaN)

        #pool = Pool(4)
        #g2 = pool.map(comparar, g.values())      #Multithread
        g2 = map(comparar2, g.values())
        h = g2
        g={}

            
    # print 'Total de Rutas subrutas: %d' %estados
    # print 'Total de Rutas finales: %d' %len(Caminos)
    # print 'Tiempo total empleado (Real, CPU): (%s,%s)' %(-tiem+time.time(),-tr+time.clock())
    # print '---------------------------SOLUCION'
    #Caminos.sort(key=lambda s: s.R,reverse=True)
    #for r in Caminos:
    #    print r
    #sol=Caminos.pop()
    #print sol
    #return (Caminos)
    return Caminos,-1



def heur1(obj):
    global G
    global N
    G=obj[0]
    calidad=obj[1]  
    weight='d'
    target=G.order()-1
    tiem=time.time()
    tr=time.clock()
    M=G.order()
    N=M-2
    P=range(1,N/2+1)
    #print P
    D=range(N/2+1,N+1)
    #print D
    Caminos=[]
    n=0
    t=0
    l=0
    c=0
    V=[]
    O=[]
    S0=Label(n,t,l,c,V,O,'source')
    h=[S0]
    negatives=[]
    contador=0
    h_max=20000
    if calidad==0:
        return [],0
    for len_h in [500]:
        S0=Label(n,t,l,c,V,O,'source')
        h=[S0]
        if len(negatives)>0:
            break
        
        #if h_max<len_h:
        #    print 'salimos por break'
        #    break
        # print 'Estamos en h_max=%d'%len_h
        h_max=0
        contador=0
        while h:
            h_max=max(h_max,len(h))
            
            h=h[0:len_h]    
    
            #L=h.pop(random.randint(0,len(h)-1))
            L=h.pop(0)
    
            if L!=0:    
                #print 'voy en el label ' +str(L)
                i=L.node()

                if contador>20000:
                    if len(negatives)>50 or contador> 2*GRAN_CONTADOR or -tiem+time.time()>20:
                        
                        print 'Hago Break con: Contador= %d, |Rutas|= %d , len(h)%d'%(contador,len(negatives),len(h))
                        break
        
        
                if i==target:
                    if L.c<-0.01:
                    #print L
                        negatives.append(L)
                        #print 'Econtre 1, '
                        calidad=-1   
                else:
                    #print P
                    #print list(set(P).intersection(set(G[i].keys())-set(L.V)))
                    #print [x+N/2 for x in L.O]
                    edges=list(set(list(set(P).intersection(set(G[i].keys())-set(L.V)))+[x+N/2 for x in L.O]).intersection(set(G[i].keys())))
                    #print edges
                    
                    
                    if len(L.O)==0 and len(L.V)>0:
                        edges.append(target)
                    edges.sort(key=lambda x: G[i][x]['d'])#ordeno por costo!
                    
                    h=h+map(extend,[G]*len(edges),[L]*len(edges),edges)
                    #for j in edges:
                        #print 'extendiendo '+str(L)+' a %d'%j
                    #    h.append(extend(L,j))
            #print h
            h=[x for x in h if x!=0]
            h.sort(key=lambda Label: Label.c)#ordeno por costo!
            contador=contador+1
    neg_rut=[x.ruta() for x in negatives]
    #if len(neg_rut)>0:
    #    neg_rut=[neg_rut.pop()]
    # print 'Total de Rutas finales: %d' %len(neg_rut)
    # print 'Tiempo total empleado (Real, CPU): (%d,%d)' %(-tiem+time.time(),-tr+time.clock())
    # print 'Contador: %d'%contador
    #print '---------------------------SOLUCION'
    if len(neg_rut)==0:
        calidad=0
    return neg_rut,calidad




def heur_dominancia(obj):
    global G
    global N
    G=obj[0]
    calidad=obj[1]  
    weight='d'
    target=G.order()-1
    tiem=time.time()
    tr=time.clock()
    M=G.order()
    N=M-2
    P=range(1,N/2+1)
    #print P
    D=range(N/2+1,N+1)
    #print D
    Caminos=[]
    n=0
    t=0
    l=0
    c=0
    V=[]
    O=[]
    
    S0=Label(n,t,l,c,V,O,'source')
    h={(0,0):[S0]} #nodo,carga
    negatives=[]
    contador=0
    contador_dominadas=0
    if calidad==0:
        return [],0
        
    while h.keys():
        if -tiem+time.time()>240:
            print 'salgo por tiempo'
            break
        tipo=h.keys().pop(0) #tipo es una tupla (n,l)
        LISTA=h.pop(tipo) #lista con todos los nodos del tipo (n,l)
        while LISTA:
            #print LISTA
            L=LISTA.pop(0)    
            i=L.node()

    
            if i==target:
                if L.c<-0.01:
                #print L
                    negatives.append(L)
                    #print 'Econtre 1, '
                    calidad=-1   
            else:
                aux=[Lx for Lx in LISTA if (L.V==Lx.V and L.O==Lx.O and L.c>Lx.c and L.t>Lx.t )]
                #print aux
                if len(aux)>0:
                    contador_dominadas=contador_dominadas+1
                    #print aux
                    #print 'sale dominada'
                else:
                    edges=list(set(list(set(P).intersection(set(G[i].keys())-set(L.V)))+[x+N/2 for x in L.O]).intersection(set(G[i].keys())))
                    
                    if len(L.O)==0 and len(L.V)>0:
                        edges.append(target)
                    #edges.sort(key=lambda x: G[i][x]['d'])#ordeno por costo!
        
                    g=map(extend,[G]*len(edges),[L]*len(edges),edges)
                    g=[x for x in g if x!=0]
                    for Lx in g:
                        if (Lx.n,Lx.l) in h:
                            h[(Lx.n,Lx.l)].append(Lx)
                        else:
                            h[(Lx.n,Lx.l)]=[Lx]
            contador=contador+1
    neg_rut=[x.ruta() for x in negatives]
    #if len(neg_rut)>0:
    #    neg_rut=[neg_rut.pop()]
    # print 'Total de Rutas finales: %d' %len(neg_rut)
    # print 'Tiempo total empleado (Real, CPU): (%d,%d)' %(-tiem+time.time(),-tr+time.clock())
    # print 'Contador: %d'%contador
    # print 'Contador Dominadas: %d'%contador_dominadas
    #print '---------------------------SOLUCION'
    if len(neg_rut)==0:
        calidad=0
    return neg_rut,calidad

def heur_branch1(obj):
    global G
    global N
    G=obj[0]
    calidad=obj[1]
    rules=obj[2]
    weight='d'
    target=G.order()-1
    tiem=time.time()
    tr=time.clock()

    M=G.order()
    N=M-2
    P=range(1,N/2+1)
    #print P        
    D=range(N/2+1,N+1)
    #print D
    Caminos=[]
    n=0
    t=0
    l=0
    c=0
    V=[]
    O=[]
    S0=Label(n,t,l,c,V,O,'source',0)
    h=[S0]
    negatives=[]
    contador=0
    rest=[]
    if calidad==0:
        return [],0
    while h:
        #print h
        
        h=h[0:500]
        
        if -tiem+time.time()>50:
            print contador,len(h)
            break
        L=h.pop()
        if L!=0:    
            #print 'voy en el label ' +str(L)
            i=L.node()
            if contador>20000:
                if len(negatives)>5 or contador>GRAN_CONTADOR:
                    print 'Hago Break con: Contador= %d, |Rutas|= %d , len(h)%d'%(contador,len(negatives),len(h))
                    break
            
            
            if i==target:
                if L.c<-0.01:
                #print L
                    negatives.append(L)
                    #print 'Econtre 1, '
                    calidad=0
                L.ruta()

                
            else:
                rest=[] #conjunto de arcos prohibidos
                pick=L.pickup #ultimo pickup hecho por la ruta
                for j in P+[target]:
                    if (pick, j) in rules:
                        if rules[(pick,j)]==False: #hay una regla con False
                            rest.append(j) #rest contiene todos los arcos a borrar, prohibo el arco j
                aux=L.V[:]

                if pick!=0:
                    aux.remove(pick)
                for (x,y) in [(l,m) for (l,m) in rules if l in aux]: #reviso reglas True viejas
                    if rules[(x,y)]==True:
                        if m not in L.V:
                            rest.append(m)
                edges=list(set(P)-set(L.V))+[x+N/2 for x in L.O]
                if len(L.O)==0 and len(L.V)>0: #LA RUTA PERMITE IR AL DEPOT , no hay open requests
                    edges.append(target)
                edges=[x for x in edges if x not in rest]
                  
                #print edges
                edges=list(set(edges).intersection(set(G[i].keys())))
                edges.sort(key=lambda x: G[i][x]['d'])#ordeno por costo!
                h=h+map(extend,[G]*len(edges),[L]*len(edges),edges)
                h=[x for x in h if x!=0]
        #print contador 
        contador=contador+1
    neg_rut=[x.ruta() for x in negatives]
    #print 'el contador del pricing vale: '+str(contador)
    #print 'Total de Rutas finales: %d' %len(neg_rut)
    #print 'Tiempo total empleado (Real, CPU): (%d,%d)' %(-tiem+time.time(),-tr+time.clock())
    #print '---------------------------SOLUCION'
    


    return neg_rut,calidad

def heur_branch2(obj):
    global G
    global N
    G=obj[0]
    calidad=obj[1]
    rules=obj[2]
    weight='d'
    target=G.order()-1
    tiem=time.time()
    tr=time.clock()

    M=G.order()
    N=M-2
    P=range(1,N/2+1)
    #print P        
    D=range(N/2+1,N+1)
    #print D
    Caminos=[]
    n=0
    t=0
    l=0
    c=0
    V=[]
    O=[]
    S0=Label(n,t,l,c,V,O,'source',0)
    h=[S0]
    negatives=[]
    contador=0
    rest=[]
    if calidad==0:
        return [],0
    while h:
        #print h
        
        #h=h[0:500]
        
        if -tiem+time.time()>50:
            print contador,len(h)
            break
        L=h.pop()
        if L!=0:    
            #print 'voy en el label ' +str(L)
            i=L.node()
            if contador>20000:
                if len(negatives)>5 or contador>GRAN_CONTADOR:
                    print 'Hago Break con: Contador= %d, |Rutas|= %d , len(h)%d'%(contador,len(negatives),len(h))
                    break
            
            
            if i==target:
                if L.c<-0.01:
                #print L
                    negatives.append(L)
                    #print 'Econtre 1, '
                    calidad=0
                L.ruta()

                
            else:
                rest=[] #conjunto de arcos prohibidos
                pick=L.pickup #ultimo pickup hecho por la ruta
                for j in P+[target]:
                    if (pick, j) in rules:
                        if rules[(pick,j)]==False: #hay una regla con False
                            rest.append(j) #rest contiene todos los arcos a borrar, prohibo el arco j
                aux=L.V[:]

                if pick!=0:
                    aux.remove(pick)
                for (x,y) in [(l,m) for (l,m) in rules if l in aux]: #reviso reglas True viejas
                    if rules[(x,y)]==True:
                        if m not in L.V:
                            rest.append(m)
                edges=list(set(P)-set(L.V))+[x+N/2 for x in L.O]
                if len(L.O)==0 and len(L.V)>0: #LA RUTA PERMITE IR AL DEPOT , no hay open requests
                    edges.append(target)
                edges=[x for x in edges if x not in rest]
                  
                #print edges
                edges=list(set(edges).intersection(set(G[i].keys())))
                edges.sort(key=lambda x: G[i][x]['d'])#ordeno por costo!
                h=h+map(extend,[G]*len(edges),[L]*len(edges),edges)
                h=[x for x in h if x!=0]
        #print contador 
        contador=contador+1
    neg_rut=[x.ruta() for x in negatives]
    #print 'el contador del pricing vale: '+str(contador)
    #print 'Total de Rutas finales: %d' %len(neg_rut)
    #print 'Tiempo total empleado (Real, CPU): (%d,%d)' %(-tiem+time.time(),-tr+time.clock())
    #print '---------------------------SOLUCION'
    


    return neg_rut,calidad


"""
Idea de modelo para pricing de P&D 

modelo por arcos, MTZ

x_ij = 1 si voy del nodo i al j 
w_i = instante de visita nodo i   (<= Tfinal)
q_i = carga al salir de nodo i   (<= capacidad de vehiculo)


1. Salgo y vuelvo a la bodega 

sum_j x_0j = 1
sum_j x_j,2N+1 = 1

2. Conservacion de flujo en nodos: para todo i != 0,2N+1

sum_j x_ij = sum_j x_ji  

3. Visito pickup node si y solo si visito delivery node: para todo i,  1 <= i <= N

sum_j x_ij = sum_j x_i+N,j

4. MTZ: para todo i,j

w_j >= w_i + T_ij + M(1-x_ij)    (T_ij: travel time)

5. w_i = 0 si no visito i: para todo i

w_i <= Tgrande sum_j x_ij

6. Visito delivery node despues de pickup node: para todo i,  1 <= i <= N

w_i + T_i,i+N (1-sum_j x_ij) <= w_i+N

7. Salgo  y vuelvo vacio a la bodega

q_0 = 0 
q_2N+1 = 0 

8. Continuidad de carga: para todo i,j

q_j >= q_i + L_i + M(1-x_ij)     (L_i: load cargada en i, <0 si es delivery)

9. Ventanas de tiempo: para todo i 

a_i  sum_j x_ij <= w_i <= b_i  sum_j x_ij

F.O. 

min sum_i,j c_ij x_ij


NUEVO MODELO AGREGA

y_i = 1 si visita nodo i 
z_i = variables "orden" como MTZ TSP

10. definicion de variable de visita 

y_0 = 1
y_i = sum_j x_ji para i != 0 

11. MTZ para orden: para todo i,j

z_j >= z_i + 1 + M(1-x_ij)  


"""


def pricing_exacto_MIP(obj):
    global G
    global N
    G=obj[0]
    calidad=obj[1]  
    weight='d'
    target=G.order()-1
    tiem=time.time()
    tr=time.clock()
    M=G.order()
    N=M-2
    P=range(1,N/2+1)
    #print P
    D=range(N/2+1,N+1)
    #print D

    neg_rut = []
    calidad = 0


    sub = cplex.Cplex()
    sub.objective.set_sense(sub.objective.sense.minimize)
    sub.set_problem_type(sub.problem_type.MILP)

    print("Pase 1")

    TMax = 1000 # OJO
    QVeh = 15 #OJO

    ##Variables
    """
    x_ij = 1 si voy del nodo i al j 
    w_i = instante de visita nodo i   (<= Tfinal)
    q_i = carga al salir de nodo i   (<= capacidad de vehiculo)
    """

    #Arcos


    sub.variables.add(names = ["x_"+str(i)+"_"+str(j) for i,j in G.edges()], types = [sub.variables.type.binary] * len(G.edges()),
                      obj = [G[i][j]['d'] for i,j in G.edges()])

    print("Pase 2")


    #Tiempos

    sub.variables.add(names = ["w_"+str(i) for i in G.nodes()], types = [sub.variables.type.continuous] * len(G.nodes()), 
                      lb = [0] * len(G.nodes()), ub = [TMax] * len(G.nodes()))


    print("Pase 3")

    #Cargas

    sub.variables.add(names = ["q_"+str(i) for i in G.nodes()], types = [sub.variables.type.continuous] * len(G.nodes()), 
                      lb = [0] * len(G.nodes()), ub = [QVeh] * len(G.nodes()))

    print("Pase 4")

    #Visita: y_i = 1 si visita nodo i 

    sub.variables.add(names = ["y_"+str(i) for i in G.nodes()], types = [sub.variables.type.binary] * len(G.nodes()))

    #Orden: z_i = variables "orden" como MTZ TSP

    sub.variables.add(names = ["z_"+str(i) for i in G.nodes()], types = [sub.variables.type.integer] * len(G.nodes()), 
                      lb = [0] * len(G.nodes()), ub = [G.order()] * len(G.nodes()))

    ### Restricciones 

    """
    1. Salgo y vuelvo a la bodega 

    sum_j x_0j = 1
    sum_j x_j,2N+1 = 1
    """

    var0 = ["x_"+str(i)+"_"+str(j) for i,j in G.edges() if i == 0]
    var2N1 = ["x_"+str(i)+"_"+str(j) for i,j in G.edges() if j == (G.order()-1)]
    coeff = [1]*len(var0)    

    """
    print("var0 = " + str(var0))
    print("var2N1 = " + str(var2N1))
    print("coeff = " + str(coeff))
    """

    print(str(len(var0)) +" " + str(len(var2N1)) +" " + str(len(coeff))) 

    print("Pase 5")


    sub.linear_constraints.add(lin_expr=[cplex.SparsePair(ind=var0,val=coeff)],
                               senses=['E'], rhs=[1], names=['salgo'])

    sub.linear_constraints.add(lin_expr=[cplex.SparsePair(ind=var2N1,val=coeff)],
                               senses=['E'], rhs=[1], names=['vuelvo'])
    print("Pase 6")


    """
    2. Conservacion de flujo en nodos: para todo i != 0,2N+1

    sum_j x_ij = sum_j x_ji  
    """

    for i in range(1,N+1):
        #print("antes i = " + str(i))
        var0 = ["x_"+str(k)+"_"+str(j) for k,j in G.edges() if k==i]
        var1 = ["x_"+str(j)+"_"+str(k) for j,k in G.edges() if k==i]
        coeff0 = [1]*len(var0)    
        coeff1 = [-1]*len(var1)    

        """
        print("var0 = " + str(var0))
        print("var1 = " + str(var1))
        print("coeff0 = " + str(coeff0))
        print("coeff1 = " + str(coeff1))



        print("despues i = " + str(i))


        print("Pase 7 con i = " + str(i))
        """

        sub.linear_constraints.add(lin_expr=[cplex.SparsePair(ind=var0+var1,val=coeff0+coeff1)],
                                   senses='E', rhs=[0], names=['conservacion_'+str(i)])

        #print("Pase 8 con i = " + str(i))


    """
    3. Visito pickup node si y solo si visito delivery node: para todo i,  1 <= i <= N

    sum_j x_ij = sum_j x_i+N,j
    """
    
    for i in P:
        var0 = ["x_"+str(k)+"_"+str(j) for k,j in G.edges() if k==i ]
        var1 = ["x_"+str(k)+"_"+str(j) for k,j in G.edges() if k==i+N/2]
        coeff0 = [1]*len(var0)    
        coeff1 = [-1]*len(var1)    

        sub.linear_constraints.add(lin_expr=[cplex.SparsePair(ind=var0+var1,val=coeff0+coeff1)],
                                   senses='E', rhs=[0], names=['PD_'+str(i)])

    
    """
    4. MTZ: para todo i,j

    w_j >= w_i + T_ij - M(1-x_ij)    (T_ij: travel time)

    supongo desigualdad triangular , lo hago solo sobre los arcos, los que no estan fueron eliminados en preproceso
    """
    
    MMM = TMax

    for i,j in G.edges():
        var = ["w_"+str(j), "w_"+str(i), "x_"+str(i)+"_"+str(j) ]
        coeff = [1,-1,-MMM]    

        sub.linear_constraints.add(lin_expr=[cplex.SparsePair(ind=var,val=coeff)],
                                   senses='G', rhs=[G[i][j]['t'] - MMM], names=['MTZ_'+str(i)+'_'+str(j)])

    
    """
    5. w_i = 0 si no visito i: para todo i

    w_i <= Tgrande sum_j x_ij
    """
    """
    for i in G.nodes():
        if (i > 0 and i < G.order()-1):
            var0 = ["x_"+str(k)+"_"+str(j) for k,j in G.edges() if k==i]
            coeff0 = [-TMax]*len(var0)    

            var = ["x_"+str(k)+"_"+str(j) for k,j in G.edges() if k==i]

            sub.linear_constraints.add(lin_expr=[cplex.SparsePair(ind=["w_"+str(i)]+var0,val=[1]+coeff0)],
                                       senses='L', rhs=[0], names=['w0novisito_'+str(i)])



    """

    """
    6. Visito delivery node despues de pickup node: para todo i,  1 <= i <= N

    w_i + T_i,i+N (1-sum_j x_ij) <= w_i+N


    puedo asumir que siempre existe el arco (i,i+N/2)

    """
    
    for i in P:
        varw = ["w_"+str(i), "w_"+str(i+N/2)]
        varx = ["x_"+str(k)+"_"+str(j) for k,j in G.edges() if k==i]
        coeffw = [1,-1]    
        coeffx = [-G[i][i+N/2]['t']] * len(varx)   

        sub.linear_constraints.add(lin_expr=[cplex.SparsePair(ind=varw+varx,val=coeffw+coeffx)],
                                   senses='L', rhs=[-G[i][i+N/2]['t']], names=['tiempoPD_'+str(i)])

    
    """
    7. Salgo  y vuelvo vacio a la bodega

    q_0 = 0 
    q_2N+1 = 0 
    """
    
    sub.linear_constraints.add(lin_expr=[cplex.SparsePair(ind=['q_0'],val=[1])],
                               senses='E', rhs=[0], names=['sale_vacio'])

    sub.linear_constraints.add(lin_expr=[cplex.SparsePair(ind=['q_'+str(N+1)],val=[1])],
                               senses='E', rhs=[0], names=['vuelve_vacio'])

    """
    8. Continuidad de carga: para todo i,j

    q_j >= q_i + L_i - M(1-x_ij)     (L_i: load cargada en i, <0 si es delivery)

    M aca puede ser la cap del camion
    """


    """
    for i,d in G.nodes_iter(data=True):
        #if i > 0 and i < G.order()-1: 
        print("i = " + str(i) + "  d = " + str(d))
    """
    
    data_nodos = G.nodes(data=True)

    dict_nodos = dict()
    for i,d in data_nodos:
        dict_nodos[i] = d

    #print(dict_nodos)

    """

    for i,j in G.edges():
        if i > 0 and i < G.order()-1: 
            var = ["q_"+str(j), "q_"+str(i), "x_"+str(i)+"_"+str(j) ]
            coeff = [1,-1,-QVeh]    

            sub.linear_constraints.add(lin_expr=[cplex.SparsePair(ind=var,val=coeff)],
                                       senses='G', rhs=[dict_nodos[i]['demand'] - QVeh], names=['MTZ_carga_'+str(i)+'_'+str(j)])
    
    for j in P:
        var = ["q_"+str(j), "q_"+str(0), "x_"+str(0)+"_"+str(j) ]
        coeff = [1,-1,QVeh]    

        sub.linear_constraints.add(lin_expr=[cplex.SparsePair(ind=var,val=coeff)],
                                   senses='G', rhs=[QVeh], names=['MTZ_carga_'+str(0)+'_'+str(j)])
            
    """           
    """
    9. Ventanas de tiempo: para todo i 

    a_i  sum_j x_ij <= w_i <= b_i  sum_j x_ij
    NO MEJOR

    a_i <= w_i + M (1-sum_j x_ij)
    w_i <= b_i + M (1-sum_j x_ij)


    """
    
    for i in range(1,max(D)+1):
        var = ["x_"+str(k)+"_"+str(j) for k,j in G.edges() if k==i]
        #cota inferior ventana
        """
        coeffa = [dict_nodos[i]['l']] * len(var)    
        coeffb = [-dict_nodos[i]['u']] * len(var)    
        """
        coeff = [TMax] * len(var)    


        """
        sub.linear_constraints.add(lin_expr=[cplex.SparsePair(ind=var+['w_'+str(i)],val=coeffa+[-1])],
                                   senses='L', rhs=[0], names=['lowTW_'+str(i)])     
        sub.linear_constraints.add(lin_expr=[cplex.SparsePair(ind=['w_'+str(i)]+var,val=[1]+coeffb)],
                                   senses='L', rhs=[0], names=['upTW_'+str(i)])     
        """

        sub.linear_constraints.add(lin_expr=[cplex.SparsePair(ind=var+['w_'+str(i)],val=coeff+[-1])],
                                   senses='L', rhs=[TMax-dict_nodos[i]['l']], names=['lowTW_'+str(i)])     
        sub.linear_constraints.add(lin_expr=[cplex.SparsePair(ind=['w_'+str(i)]+var,val=[1]+coeff)],
                                   senses='L', rhs=[TMax+dict_nodos[i]['u']], names=['upTW_'+str(i)])     




    """
    10. definicion de variable de visita 

    y_0 = 1
    y_i = sum_j x_ji para i != 0 
    """

    sub.linear_constraints.add(lin_expr=[cplex.SparsePair(ind=["y_"+str(0)],val=[1])],
                               senses='E', rhs=[1], names=['visita_'+str(0)])

    for i in range(1,G.order()):
        #print("antes i = " + str(i))
        var = ["x_"+str(j)+"_"+str(k) for j,k in G.edges() if k==i]
        coeff = [-1]*len(var)    

        sub.linear_constraints.add(lin_expr=[cplex.SparsePair(ind=var+["y_"+str(i)],val=coeff+[1])],
                                   senses='E', rhs=[0], names=['visita_'+str(i)])
  
    """
    11. MTZ para orden: para todo i,j

    z_j >= z_i + 1 - M(1-x_ij)  
    """
    MMM = G.order()

    for i,j in G.edges():
        var = ["z_"+str(j), "z_"+str(i), "x_"+str(i)+"_"+str(j) ]
        coeff = [1,-1,-MMM]    

        sub.linear_constraints.add(lin_expr=[cplex.SparsePair(ind=var,val=coeff)],
                                   senses='G', rhs= [1 - MMM], names=['MTZ_orden_'+str(i)+'_'+str(j)])



    """
    12. z_target = largo de la ruta

    z_2N+1 = sum_i,j x_ij    

    """

    var = ["x_"+str(i)+"_"+str(j) for i,j in G.edges()]
    coeff = [-1]*len(var)
    sub.linear_constraints.add(lin_expr=[cplex.SparsePair(ind=var+["z_"+str(target)],val=coeff+[1])],
                               senses='E', rhs=[0], names=['orden_target'])

    
    #sub.write("subproblema.lp")


    """

    sub.solve()

    sub_status = sub.solution.get_status()

    print("Status subp: " + str(sub_status))

    if sub_status == 101 or sub_status == 102:
        print("Objetivo subp: " + str(sub.solution.get_objective_value()))

    """



    
    sub.parameters.mip.pool.relgap.set(0.5)
    sub.parameters.mip.limits.populate.set(100)
    sub.parameters.mip.pool.replace.set(2) # para diversidad
    sub.parameters.mip.tolerances.uppercutoff.set(-0.00001)

    sub.parameters.timelimit.set(1800)


    #sub.parameters.mip.limits.capacity(1000)
    try:
        sub.populate_solution_pool()
    except CplexSolverError:
        print("Exception raised during populate")
        exit(-1)

    print()
    # solution.get_status() returns an integer code
    print("Solution status = " + str(sub.solution.get_status()))
    # the following line prints the corresponding string
    print(sub.solution.status[sub.solution.get_status()])

    numsol = sub.solution.pool.get_num()

    if numsol >= 1:    
        #generar secuencias
        for ii in range(numsol):
            print("loop vuelta ii = " + str(ii))
            objval_ii = sub.solution.pool.get_objective_value(ii)
            if objval_ii < -0.0001:
                """
                for v in range(sub.variables.get_num()):
                    if sub.variables.get_names(v).startswith("x") or sub.variables.get_names(v).startswith("y") or sub.variables.get_names(v).startswith("z"):
                        if sub.solution.pool.get_values(ii,v)>= 0.9: 
                            print(sub.variables.get_names(v) + " = " + str(sub.solution.pool.get_values(ii,v)))
                
                print('\n'.join(["y_"+str(i) + " = " + str(sub.solution.pool.get_values(ii,"y_"+str(i))) + " = " + str(int(round(sub.solution.pool.get_values(ii,"y_"+str(i))))) for i in G.nodes()]))
                """

                Nvisitados = sum([int(round(sub.solution.pool.get_values(ii,"y_"+str(i)))) for i in G.nodes()])

                #print("Nvisitados = " + str(Nvisitados))
                ruta = [0] * Nvisitados

                for i in G.nodes():
                    #print("Nodo: " + str(i))
                    #print("Visita: " + str(sub.solution.pool.get_values(ii,"y_"+str(i))))
                    #print("Orden: " + str(int(round(sub.solution.pool.get_values(ii,"z_"+str(i))))))
                    if sub.solution.pool.get_values(ii,"y_"+str(i))>= 0.9:
                        #print("len(ruta): " + str(len(ruta)))
                        #print("i: " + str(i))
                        #print("posicion: " + str(int(round(sub.solution.pool.get_values(ii,"z_"+str(i))))))
                        #print("z: " + str(sub.solution.pool.get_values(ii,"z_"+str(i))))
     
                        ruta[int(round(sub.solution.pool.get_values(ii,"z_"+str(i))))] = i
                    #print("Ruta:")
                    #print(str(ruta))

                #print("pase a1")

                t = sub.solution.pool.get_values(ii,"w_"+str(ruta[-2])) + G[ruta[-2]][target]['t']
                        
                """
                print("sali de generar ruta: ")
                print(ruta)
                print(" t = " + str(t))
                print(" objval_ii = " + str(objval_ii))
                """
                
                neg_rut.append(Ruta(ruta[-1],ruta,t,objval_ii,0))



        print('numsol = ' + str(numsol))
        #print('\n'.join(["neg_rut: "] + [str(rr) for rr in neg_rut]))

        #if len(neg_rut)>0:
        #    neg_rut=[neg_rut.pop()]
        # print 'Total de Rutas finales: %d' %len(neg_rut)
        # print 'Tiempo total empleado (Real, CPU): (%d,%d)' %(-tiem+time.time(),-tr+time.clock())
        # print 'Contador: %d'%contador
        #print '---------------------------SOLUCION'

    """
    if len(neg_rut)==0:
        calidad=0

    """
    return neg_rut,calidad

def extend(G,L,j):
    #print j
    M=G.order()
    N=M-2
    P=range(1,N/2+1)
    D=range(N/2+1,N+1)
    
    i=L.node()
    c_ij=G[i][j]['d']
    t_ij=G[i][j]['t']
    V=[]
    O=[]
    t=L.t+t_ij
    c=L.c+c_ij
    
    
    pickup=L.pickup
    if t<G.node[j]['u']:
        t=max(t,G.node[j]['l'])
        l=0

        if j in P:
            if L.l+G.node[j]['demand']<=Q:
                V=L.V+[j]
                O=L.O+[j]
                l=L.l+G.node[j]['demand'] #carga
                pickup=j
            else:
                return 0
        if j in D:
            V=L.V
            O=L.O[:]
            #print O
            #print j-N
            O.remove(j-N/2)
            
            l=L.l+G.node[j]['demand'] #carga
        if j==M-1:
            V=L.V
            O=L.O
            l=L.l
            pickup=j
            
        if len(O)==1 or len(O)==2:
            if not TSP(t,j,O):
                #print "TSP cago"
                return 0
        return Label(j,t,l,c,V,O,L,pickup)
    else:
        return 0
    

    
def extend2(L,j): #la unica diferencia con extend es que este solo acepta rutas de largo 1
    #print j
    M=G.order()
    N=M-2
    P=range(1,N/2+1)
    D=range(N/2+1,N+1)
    
    i=L.node()
    c_ij=G[i][j]['d']
    t_ij=G[i][j]['t']
    V=[]
    O=[]
    t=L.t+t_ij
    c=L.c+c_ij
    
    if j in L.V:
        return 0
    if j in D and j-N/2 not in L.O:
        return 0
    if j ==M-1 and len(L.O)!=0:
        return 0

    if len(L.V)>2:              ####<------------
        return 0
    
    if t<G.node[j]['u']:
        t=max(t,G.node[j]['l'])
        l=0

        if j in P:
            if L.l+G.node[j]['demand']<=Q:
                V=L.V[:]+[j]
                O=L.O+[j]
                l=L.l+G.node[j]['demand'] #carga
            else:
                return 0
        if j in D:
            V=L.V
            O=L.O[:]
            #print O
            #print j-N
            O.remove(j-N/2)
            
            l=L.l+G.node[j]['demand'] #carga
        if j==M-1:
            V=L.V
            O=L.O
            l=L.l
            
        if len(O)==1 or len(O)==2:
            if not TSP(t,j,O):
                #print "TSP cago"
                return 0
        return Label(j,t,l,c,V,O,L)
    else:
        return 0

def TSP(t,j,O):
    t_k=0
    D=[x+N/2 for x in O]
    if len(O)==1:
        k=D[0]
        if (j,k) not in G.edges(): #chekeo que el arco este!
            return True
        if t_k<G.node[k]['u']:
            return True
    if len(O)==2:
        k=D[0]
        l=D[1]
        if (j,k) not in G.edges() or (j,l) not in G.edges() or  (l,k) not in G.edges() or (k,l) not in G.edges(): #chekeo que los arcos esten
            return True
        for i in range(2):

            t_k=max(t+G[j][k]['t'],G.node[k]['l'])
            if t_k<G.node[k]['u']:
                t_kl=max(t_k+G[k][l]['t'],G.node[l]['l'])
                if t_kl<G.node[k]['u']:
                    return True
            l=D[0]
            k=D[1]
            
    return False
    

  



def precedencia(N,neigh,S,u):  #donde S es el conjunto visitado, vecinos es una lista de nodos vecinos, u el nodo donde estamos y N el total de nodos del grafo
    vecinos=neigh.keys()
    if u==N+1:
        return []
    P=range(1,N/2+1)
    D=range(N/2+1,N+1)
    if len(intersect(S,P))-len(intersect(S,D))>=5: #carga en el vehiculo
        Pvis=[]
    else:
        Pvis=dif(P,S)
    Defectivo=dif([x+N/2 for x in intersect(P,S) ],S)
    Pdone=intersect(P,S)
    #if len(Pdone)>11: #no mas de x clientes por ruta
    #    Pvis=[]
    
    if Defectivo==[] and len(S)>1:#chekeo poder ir al depot
        Defectivo.append(N+1)
    sol=intersect((Pvis+Defectivo),vecinos)
    sol.sort(key=lambda x: neigh[x]['d']) #los devuelvo ordenados por costo 'd'
    return(sol)


def comparar3(h):
    if len(h)==0:
        return h
    prueba=h[0]
    l=prueba.largo()
    visit=prueba.visitados()
    terminal=visit[l-1]
    h.sort(key=lambda ruta: ruta.costo())
    if terminal==nodo_terminal:
        return comparar2(h)
    return [h[0]]
    
def comparar(h): #TW
    
    if len(h)==0:
        return h
    prueba=h[0]
    total=len(h)
    l=prueba.largo()
    #print 'Vamos a comparar las rutas de largo %d, con terminal en %d que son %d'%(l,prueba.terminal(), len(h))
    j=0
    a=[]
    visit=prueba.visitados()
    terminal=visit[l-1]
    #if terminal==nodo_terminal:
    #    return comparar2(h)
    
    h.sort(key=lambda ruta: ruta.costo())    
    for r in h:
            for k in range(j+1,len(h)):
                r2=h[k]
                if r2.costo()<r.costo() and (r2.tiempo()< r.tiempo()):  
                    #print 'comparando:'
                    #print r
                    #print r2
                    #print 'La ruta con costo y tiempo (%d,%d) sale dominada por (%d,%d)'%(r.tiempo(),r.costo(),r2.tiempo(),r2.costo())
                    if j not in a:
                        a=a+[j]
                    else:
                        break   
                if r2.costo()>=r.costo() and (r2.tiempo()>= r.tiempo()):
                    if k not in a:
                        a=a+[k]
                            #print 'comparando:'
                            #print r
                            #print r2
                            #print 'La ruta con costo y tiempo (%d,%d) sale dominada por (%d,%d)'%(r2.tiempo(),r2.costo(),r.tiempo(),r.costo())
                    else:
                        break 
            j=j+1
    a.sort()
    a.reverse()
    for i in a:
        h.pop(i)
        #print r
    #print '-----TOTAL DE RUTAS ELIMINADAS %d'%len(a)
    return h        
    
def comparar2(h):
    a=min(h,key=lambda s: s.R)
    return [a] 



   
if __name__ == '__main__':
   G=nx.read_gpickle('grafo_bench.gpickle')

   pd2((G,7))



