from Procedimientos import *
from padnums import *
import networkx as nx
import sys


path='GEO_2/W_30_Q_15r=100/'

instances=['AA30_1']
num_depots=7
Q=15

for instance in instances:
   D={}
   tabla=[]
   
   for i in range(num_depots):
       D[i]=nx.read_gpickle(path+instance+'_Depot%d.gpickle'%i)
       table=clean_up(D[i],Q)
       tabla.append([table[x][1] for x in range(len(table))])
   t=[[table[x][0] for x in range(len(table))]]+tabla
   
   out = sys.stdout
   pprint_table(out, [['','Depot0','Depot1','Depot2','Depot3','Depot4','Depot5','Depot6']]+zip(*t))
   
   f = open(path+instance+'_preproceso.dat', 'w')
   pprint_table(f, [['','Depot0','Depot1','Depot2','Depot3','Depot4','Depot5','Depot6']]+zip(*t))
   f.close()

