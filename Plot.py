import networkx as nx
import matplotlib.pyplot as plt

def Plot_grafo(G,arcos,s): #grafo, si dibuja los arcos
    M=G.order()
    pos={}
    plt.figure(figsize=(10,10))
    t=0

    for n in G:
        pos[n]=(G.node[n]['x'],G.node[n]['y'])
        if G.node[n]['tipo']=='terminal':
            nx.draw_networkx_nodes(G,pos,nodelist=[n],
                                    node_size=500,
                                    node_color='r',
                                    alpha=0.7,
                                    cmap=plt.cm.Reds_r)
            nx.draw_networkx_labels(G,pos,{n:t},font_size=10)
            t=t+1;
        else:
            nx.draw_networkx_nodes(G,pos,nodelist=[n],
                                    node_size=300,
                                    node_color='w',
                                    cmap=plt.cm.Reds_r)
            nx.draw_networkx_labels(G,pos,{n:G.node[n]['tipo']},font_size=10)
            
        #nx.draw_networkx_labels(G,pos,{n:n})   #etiquetas reales
    
    if arcos:
        nx.draw_networkx_edges(G,pos, edge_color='gray', alpha=0.16)
    
        

    plt.xlim(-1,51)
    plt.ylim(-1,51)
    plt.axis('on')
    plt.savefig(s+'.png')
    #plt.show()
    
def Plot_ruta(G,R,t,s='AA'): #grafo G, ruta R, terminal t
    M=G.order()
    s=s+str((M-2)/2)
    pos={}
    plt.figure(figsize=(10,10))
    for n in G:
        pos[n]=(G.node[n]['x'],G.node[n]['y'])
        if G.node[n]['tipo']=='terminal':
            nx.draw_networkx_nodes(G,pos,nodelist=[n],
                                    node_size=500,
                                    node_color='r',
                                    alpha=0.7,
                                    cmap=plt.cm.Reds_r)
            nx.draw_networkx_labels(G,pos,{n:t},font_size=10)
        else:
            nx.draw_networkx_nodes(G,pos,nodelist=[n],
                                    node_size=300,
                                    node_color='w',
                                    cmap=plt.cm.Reds_r)
            nx.draw_networkx_labels(G,pos,{n:G.node[n]['tipo']},font_size=10)
            
        #nx.draw_networkx_labels(G,pos,{n:n})   #etiquetas reales
    #print R
    edges=[]
    anterior=R[0]
    Raux=R[1:len(R)]
    for n in Raux:
        edges.append((anterior,n))
        anterior=n   
    #print edges
    nx.draw_networkx_edges(G,pos, edgelist=edges,edge_color='black',alpha=0.7)
    
    #plt.xlim(-0.05,1.05)
    #plt.ylim(-0.05,1.05)
    plt.axis('off')
    plt.savefig(s+'.png')
    plt.show()

# def Plot_rutas(G,Rs,t,s='AA'): #grafo G, ruta R, terminal t
#     M=G.order()
#     s=s+str((M-2)/2)
#     pos={}
#     plt.figure(figsize=(10,10))
#     for n in G:
#         pos[n]=(G.node[n]['x'],G.node[n]['y'])
#         if G.node[n]['tipo']=='terminal':
#             nx.draw_networkx_nodes(G,pos,nodelist=[n],
#                                     node_size=500,
#                                     node_color='r',
#                                     alpha=0.7,
#                                     cmap=plt.cm.Reds_r)
#             nx.draw_networkx_labels(G,pos,{n:t},font_size=10)
#         else:
#             nx.draw_networkx_nodes(G,pos,nodelist=[n],
#                                     node_size=300,
#                                     node_color='w',
#                                     cmap=plt.cm.Reds_r)
#             nx.draw_networkx_labels(G,pos,{n:G.node[n]['tipo']},font_size=10)
            
#         #nx.draw_networkx_labels(G,pos,{n:n})   #etiquetas reales
#     #print R
#     edges=[]
#     anterior=R[0]
#     Raux=R[1:len(R)]
#     for n in Raux:
#         edges.append((anterior,n))
#         anterior=n   
#     #print edges
#     nx.draw_networkx_edges(G,pos, edgelist=edges,edge_color='black',alpha=0.7)
    
#     #plt.xlim(-0.05,1.05)
#     #plt.ylim(-0.05,1.05)
#     plt.axis('off')
#     plt.savefig(s+'.png')
#     plt.show()
    