import networkx as nx
# from padnums import *
import sys

def A(List,a,b):#o que esta entre a y b en la lista
    i=List.index(a)
    j=List.index(b)
    if i > j:
        print 'cuidado que '+str(b)+' aparece antes que '+str(a)
    return List[i+1:j]

def branch_rule(visitados, D): #funcion que a partir de una ruta entrega las reglas de branch Dumas 1991
    dicc=[]
    visitados=[x for x in visitados if x not in D]
    a=visitados[:]
    b=visitados[:]
    a.pop()
    b.pop(0)
    tuplas=zip(a,b)
    print tuplas
    aux={}
    iterable=range(len(tuplas)+1)
    iterable.reverse()
    for k in iterable:
        print k
        aux={}
        l=0
        una_false=True
        for oij in tuplas:
            if l<k:
                aux[oij]=True
            else:
                if una_false:
                    aux[oij]=False
                    una_false=False
            l=l+1
        
        dicc.append(aux)
        
    return dicc
def clean_up(H,cap,*num_clientes): #preproceso total del grafo auxiliar H, capacidad de los vehiculos

    Aux=H.copy()
    

    
    if len(num_clientes)==0:
        N=H.order()
    else:
        N=2*num_clientes[0]+2
    
    P=range(1,N/2)
    D=range(N/2,N-1)
    n=len(P)
##TW###############
    bdepot=H.node[N-1]['u']
    b0=H.node[0]['u']
    a0=H.node[0]['l']
    
    for i in P:
        b_n_mas_i=H.node[n+i]['u']
        b_n_mas_i=min(b_n_mas_i,bdepot-H[i][N-1]['t'])

        H.add_node(n+i,u=b_n_mas_i)
        
        b_i=H.node[i]['u']
        b_i=min(b_i,b_n_mas_i-H[i][n+i]['t'])
        H.add_node(i,u=b_i)
        
        a_i=H.node[i]['l']
        a_i=max(a_i,a0+H[0][i]['t'])
        H.add_node(i,l=a_i)
        
        a_n_mas_i=H.node[n+i]['l']
        a_n_mas_i=max(a_n_mas_i,a_i+H[i][n+i]['t'])
        H.add_node(n+i,l=a_n_mas_i)
        
    for k in P+D:
        a_k=H.node[k]['l']
        b_k=H.node[k]['u']
        a_k=max(a_k,min(b_k,min([H.node[j]['l']-H[k][j]['t'] for j in H.successors(k)])))
        H.add_node(k,l=a_k)
        
        b_k=min(b_k,max(a_k,max([H.node[i]['u']+H[i][k]['t'] for i in H.predecessors(k)])))
        H.add_node(k,u=b_k)
    
    for k in P+D:
        a_k=H.node[k]['l']
        b_k=H.node[k]['u']
        a_k=max(a_k,min(b_k,min([H.node[j]['l']-H[k][j]['t'] for j in H.successors(k)])))
        H.add_node(k,l=a_k)
        
        b_k=min(b_k,max(a_k,max([H.node[i]['u']+H[i][k]['t'] for i in H.predecessors(k)])))
        H.add_node(k,u=b_k)    
        
        
##PRIORIDAD########   
    #Sacamos los arcos que van del depot a deliverys
    contador_prioridad=0
    for j in D:
        if (0,j) in H.edges():
            #print 'Saco el arco: (%d,%d)'%(0,j)
            contador_prioridad=contador_prioridad+1
            H.remove_edge(0,j)
    
    #Sacamos los arcos desde pickups de vuelta al depot
    for i in P:
        if (i,N-1) in H.edges():
            #print 'Saco el arco: (%d,%d)'%(i,N)
            contador_prioridad=contador_prioridad+1
            H.remove_edge(i,N-1)
        if (i,0) in H.edges():
            #print 'Saco el arco: (%d,%d)'%(i,N)
            contador_prioridad=contador_prioridad+1
            H.remove_edge(i,0)
    
    #Sacamos los arcos entre deliverys-->Pickups
    
    for j in D:
        if (j,j-len(P)) in H.edges():
            #print 'Saco el arco: (%d,%d)'%(j,j-len(P))
            contador_prioridad=contador_prioridad+1
            H.remove_edge(j,j-len(P))
    
    
##Capacidad
    contador_capacidad=0
    for i in P:
        for j in P:
            if i!=j:
                if H.node[i]['demand']+H.node[j]['demand']>cap:
                    if (i,j) in H.edges():
                        contador_capacidad=contador_capacidad+1
                        H.remove_edge(i,j)
                    if (j,i) in H.edges():
                        contador_capacidad=contador_capacidad+1
                        H.remove_edge(j,i)
                    if (i,n+j) in H.edges():
                        contador_capacidad=contador_capacidad+1
                        H.remove_edge(i,n+j)
                    if (j,n+i) in H.edges():
                        contador_capacidad=contador_capacidad+1
                        H.remove_edge(j,n+i)
                    if (n+j,n+i) in H.edges():
                        contador_capacidad=contador_capacidad+1
                        H.remove_edge(n+j,n+i)
                    if (n+i,n+j) in H.edges():
                        contador_capacidad=contador_capacidad+1
                        H.remove_edge(n+i,n+j)
                        
                        
 ##TW#####
    contador_tw=0
    for i in P+D:
        for j in P+D:
            if i!=j:
                if (i,j) in H.edges():
                    if H.node[i]['l']+H[i][j]['t']>H.node[j]['u']:
                        H.remove_edge(i,j)
                        contador_tw=contador_tw+1
                    
                    
                    
##TW+prec####
    contador_tw_pre=0
    for i in P:
        for j in P:
            if i!=j:
                if not factible(H,[j,i,n+j,n+i]):
                    if (i,n+j) in H.edges():
                        contador_tw_pre=contador_tw_pre+1
                        H.remove_edge(i,n+j)
                if not factible(H,[i,n+i,j,n+j]):
                    if (n+i,j) in H.edges():
                        contador_tw_pre=contador_tw_pre+1
                        H.remove_edge(n+i,j)
                if not factible(H,[i,j,n+i,n+j]):
                    if (i,j) in H.edges():
                        contador_tw_pre=contador_tw_pre+1
                        H.remove_edge(i,j)
                    if not factible(H,[j,i,n+i,n+j]):
                        if (n+i,n+j) in H.edges():
                            contador_tw_pre=contador_tw_pre+1
                            H.remove_edge(n+i,n+j)
    

    cambio_a=sum([abs(Aux.node[i]['l']-H.node[i]['l']) for i in Aux])/float(Aux.order())
    cambio_b=sum([abs(Aux.node[i]['u']-H.node[i]['u']) for i in Aux])/float(Aux.order())       
    cantidad_a=sum([1 for i in Aux if abs(Aux.node[i]['l']-H.node[i]['l'])>0])
    cantidad_b=sum([1 for i in Aux if abs(Aux.node[i]['u']-H.node[i]['u'])>0])

    table=[['TW',''],
            ['Nodos_modificados_en_lower_bound',cantidad_a],
            ['Nodos_modificados_en_upper_bound',cantidad_b],
            ['Modificacion_promedio_lower_bound',cambio_a],
            ['Modificacion_promedio_upper_bound',cambio_b],
            ['',''],
            ['BORRADO_DE_ARCOS',''],
            ['Arcos_totales:',len(Aux.edges())],
            ['Eliminados_por_Prioridad',contador_prioridad],
            ['Eliminados_por_Capacidad',contador_capacidad],
            ['Eliminados_por_TW',contador_tw],
            ['Eliminados_por_TW_precedencia',contador_tw_pre],
            ['Porcentaje_de_arcos_eliminados',((100.0*(contador_prioridad+contador_capacidad+contador_tw+contador_tw_pre))/len(Aux.edges()))]]
    #out = sys.stdout
    #pprint_table(out, table)
    return(table)
    
def factible(G,V):
    i=V.pop(0)
    t=G.node[i]['l']
    while V:
        j=V.pop(0)
        if (i,j) in G.edges():
            if t+G[i][j]['t']<=G.node[j]['u']:
                t=max(G.node[j]['l'],t+G[i][j]['t'])
                
            else:
                # print 'salto por tiempo en (i,j):'+str(i)+','+str(j)
                return False
        else:
            # print 'salto por que el arco:'+str(i)+','+str(j)+' no esta'
            return False
        i=j
    return True
        
    
#mod marzo2016
def actualizar(H,G,mu,pi,depot,alpha,beta,gamma1,gamma2):
    #num_clientes=len(pi)
    #num_depots=len(mu[0])
    PI=[0]+[e for e in pi]+[0 for e in pi]+[0] #cargamos el paseo al PU
    MU=[0]+[e[depot] for e in mu]+[0 for e in mu]+[0]
    arcos=[e for e in H.edges_iter(data=True)]
    for i,j,edge_data in arcos:
        if i==0:
            H.add_edge(i,j,d=G[i][j]['d']-PI[j]+MU[j]-alpha[depot]-beta[depot]-gamma1-gamma2)
            #H.add_edge(i,j,d=G[i][j]['d']-PI[j]+MU[j])
        else:    
            H.add_edge(i,j,d=G[i][j]['d']-PI[j]+MU[j])

def costo_ruta(H,ruta):
    edges=[]
    ruta=ruta.visitados()
    anterior=ruta[0]
    costo=0
    for n in ruta[1:]:
        costo=H[anterior][n]['d']+costo
        anterior=n  
    return costo

def H1(G,l):
    N=G.order()
    P=range(1,N/2)
    D=range(N/2,N-1)
    H=nx.DiGraph(G)

    for i in G:
        #pu=list(set(P).intersection(set(G[i].keys())))
        #pu.sort(key=lambda x: G[i][x]['d'])
        #pu=pu[0:l]
        #de=list(set(D).intersection(set(G[i].keys())))
        #de.sort(key=lambda x: G[i][x]['d'])
        #de=de[0:l]
        #remove=set(G[i].keys()).difference(set(de))
        #remove=remove.difference(set(pu))
        #remove=list(remove)
        L=list(G[i].keys())
        L.sort(key=lambda x: G[i][x]['d'])
        L=L[0:int(l*len(G[i].keys()))]
        remove=list(set(G[i].keys()).difference(set(L)))
        for j in remove:
            H.remove_edge(i,j)
            
    for j in P: #agrego los nodos a los PU
        if (0,j) in G.edges():
            H.add_edge(0,j,G[0][j])
        if (j,j+(N-1)/2) in G.edges():
            H.add_edge(j,j+(N-1)/2,G[j][j+(N-1)/2])
    for i in D: #agrego los nodos a los PU
        if (i,N-1) in G.edges():
            H.add_edge(i,N-1,G[i][N-1])
        
    return(H)
        
        
        
        
