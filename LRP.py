#import sys
#sys.path.append('/Users/thomascapelle/ILOG/CPLEX_Studio_AcademicResearch122/cplex/python/x86_darwin9_gcc4.0')

import cplex
from cplex.exceptions import CplexError
import networkx as nx
from pricing import *
from cplex.exceptions import CplexSolverError
from cplex import SparsePair
from Procedimientos import *
from Plot import *
from inputdata import generate
from padnums import pprint_table
from multiprocessing import Pool

import random
import time
import sys
import os
import math
import collections
# import logging
# from sys import stdout

# log_level = logging.DEBUG
# logging.basicConfig(format = '%(asctime)s - %(levelname)s - %(message)s',
#                     level  = log_level,
#                     stream = stdout)

pool = Pool(1)

random.seed(1) # para hacerlo reproducible


def imprimir_nodos_ruta(ff,nruta):
    ff.write("Nodos ruta: " + str(sum(nruta.values())) + "\n")
    for l in range(0,18,2): #OJO en duro
        #for l in nruta.keys():
        if l in nruta.keys():
            ff.write("Rutas de " + str(l/2)+ " pickups: " + str(nruta[l]) + " = " + str(nruta[l]/(l/2+1)) + " x " + str(l/2+1)+"\n")
        else:
            ff.write("Rutas de " + str(l/2)+ " pickups: " + str(0) + " = " + str(0) + " x " + str(l/2+1)+"\n")
    return



class Nodo_branch:
    
    #version Mar2016
    def __init__(self,nodo_padre,rules,dep,LB,UB,min_rutas,max_rutas,total_rutas):
        self.nodo_padre = nodo_padre
        self.rules      = rules
        self.LB         = LB
        self.UB         = UB
        self.rules_depots     = dep
        self.min_rutas   = min_rutas[:]
        self.max_rutas   = max_rutas[:]
        self.total_rutas = total_rutas[:]
        
    def __str__(self):
        st=str(self.rules)+str(self.rules_depots)+str(self.min_rutas)+str(self.max_rutas)+str(self.total_rutas)
        return st

class LRP:
    '''Class PLR
    This class is the bread and butter of PLRPDP. It computes
    all the variables related to the optimisation problem.
    It has many method for computing each parts:
        -Initialisation
        -Pricing
        -Branch and Bound
    '''
    def __init__(self, path = 'GEO_0/W_30_Q_15/', prefix= 'AA', num_clientes = 5, num_depots = 7, Q = 15, W = 30, version = '20', costo_depot = 0.1,  ropke = False, costo_r = 100):
        self.Q = Q
        self.W = W
        self.version = version
        if path[-1]!='/':
            self.path = path+'/'
        else:
            self.path = path
        self.prefix = prefix
        self.num_clientes = num_clientes
        self.num_depots = num_depots
        self.hora_inicio = time.time()
        #self.num_iter_pric = 7
        self.num_iter_pric = 100
        self.largo_rutas_iniciales = 6 
        self.ropke = ropke
        self.costo_depot = costo_depot
        self.pricing_has_been_runned = False

        self.P = range(1,self.num_clientes+1)
        self.D = range(self.num_clientes+1,2*self.num_clientes+1)
        self.rutas_iniciales = {}
        self.dicc_rutas = {} #diccionario que establece biyeccion entre rutas como clase y variables de cplex, por medio de sus nombres

        self.c_depot = [self.costo_depot]*self.num_depots  #costos ignorados = (multi-depot PDP)
        #c_depot=[200,300,100]
        self.costo_r = costo_r
        

        

        if not os.path.isfile(self.path+self.prefix+'%d_%s_Depot0.gpickle'%(self.num_clientes,self.version)):
            print "Generando los subgrafos por depot"
            generate(self.prefix+'%d_%s'%(self.num_clientes, self.version),'DEPOTS',self.path,self.ropke,self.costo_r)
            print 'Iniciando el Preproceso'
            Di_aux={}
            tabla=[]
            for i in range(self.num_depots):
               print "Depot i=%d"%i
               Di_aux[i]=nx.read_gpickle(self.path+self.prefix+'%d_%s_Depot%d.gpickle'%(self.num_clientes, self.version, i))
               table=clean_up(Di_aux[i],Q)
               nx.write_gpickle(Di_aux[i],self.path+self.prefix+'%d_%s_Depot%d.gpickle'%(self.num_clientes, self.version, i))
               tabla.append([table[x][1] for x in range(len(table))])
            t=[[table[x][0] for x in range(len(table))]]+tabla
       
            out = sys.stdout
            pprint_table(out, [['','Depot0','Depot1','Depot2','Depot3','Depot4','Depot5','Depot6']]+zip(*t)) # OJO N DEPOTS
            #pprint_table(out, [['','Depot0']]+zip(*t))           

            f = open(self.path+self.prefix+'%d_%s'%(self.num_clientes, self.version)+'_preproceso.dat', 'w')
            pprint_table(f, [['','Depot0','Depot1','Depot2','Depot3','Depot4','Depot5','Depot6']]+zip(*t))
            #pprint_table(f, [['','Depot0']]+zip(*t))
            f.close()
            print 'Preproceso Terminado'
        else:
            print 'Archivos ya existentes, no se hizo preproceso'

        #Grafos:
        self.G_total = nx.read_gpickle(self.path+self.prefix+'%d_%s.gpickle'%(self.num_clientes,self.version))
        self.Di={}
        self.aux={}
        self.aux5={}   #solo mejores 5 arcos
        self.aux10={} #solo mejores 10 arcos
        print 'Cargando Grafos auxiliares por depot'
        for i in range(self.num_depots):
            self.aux[i]      = nx.read_gpickle(self.path+self.prefix+'%d_%s_Depot%d.gpickle'%(self.num_clientes,self.version,i))
            self.Di[i]       = nx.read_gpickle(self.path+self.prefix+'%d_%s_Depot%d.gpickle'%(self.num_clientes,self.version,i))
            
            self.aux5[i]=H1(self.aux[i],0.3)
            self.aux10[i]=H1(self.aux[i],0.5)

        ##CPLEX SHIT!
        c = cplex.Cplex()
        c.objective.set_sense(c.objective.sense.minimize)
        c.set_problem_type(c.problem_type.LP)

        ##Restricciones Lineales###################################
        c.linear_constraints.add(names = ['cliente_%d'%(i+1) for i in range(self.num_clientes) ], #restricciones numeradas de 1 a N clientes
                                 senses = ["E"] * self.num_clientes,
                                 rhs=[1 for i in range(self.num_clientes)])# poner 1 en vez del random para no estabilizar
            
        
        for i in range(self.num_clientes):               #restricciones de i,j cliente-depot, clientes de 1 a N, depots de 0 a J-1   =)
            for j in range(self.num_depots):
                nom_res='depot%d,cliente%d'%(j,i+1)
                c.linear_constraints.add(names = [nom_res],
                                 senses = ["G"],
                                 rhs=[0])
        
        #NUEVO MAR2016  

        for j in range(self.num_depots):               #Cota inferior en el numero de rutas por depot: 0 
           nom_res='min_rutas_depot%d'%(j)
           c.linear_constraints.add(names = [nom_res],
                            senses = ["G"],
                            rhs=[0])
        
        for j in range(self.num_depots):               #Cota superior en el numero de rutas por depot: numero de clientes 
           nom_res='max_rutas_depot%d'%(j)
           c.linear_constraints.add(names = [nom_res],
                            senses = ["L"],
                            rhs=[self.num_clientes])
        #Cota inferior en el numero total de rutas: 0
        nom_res='min_total_rutas'
        c.linear_constraints.add(names = [nom_res],senses = ["G"],rhs=[0])
        #Cota superior en el numero total de rutas: numero de clientes
        nom_res='max_total_rutas'
        c.linear_constraints.add(names = [nom_res],senses = ["L"],rhs=[self.num_clientes])
        

        ##Variables#################################################
        
        #Localizacion:
        for j in range(self.num_depots):
            c.variables.add(obj = [self.c_depot[j]],
                            names = ['depot%d'%j],
                            lb = [0],
                            columns = [cplex.SparsePair(ind = ['depot%d,cliente%d'%(j,i+1) for i in range(self.num_clientes)], val=[1]*self.num_clientes)])
        
        self.c = c 
        a = pool.map(pd2, zip(self.aux.values(),[self.largo_rutas_iniciales]*self.num_depots))      #Multithread
        self.rutas_iniciales,basura = zip(*a)
        
        for d in range(self.num_depots):
            for r in self.rutas_iniciales[d]:
                self.anadir_ruta(r, d)

        print 'Total de Variables Iniciales: %d' %self.c.variables.get_num()
        print '\n####################################fin inicializacion Prob. Maestro#################################\n'
        self.c.solve()
        return

    def anadir_ruta(self, r, d):
        ID = r.visitados()
        agregue = 1
        #print ID
        if ('d%d_'%d+str(ID)) not in self.dicc_rutas: #solo creo la ruta si no esta ya en el problema maestro
            r.R = costo_ruta(self.Di[d],r)# le cambio el costo reducido al objeto ruta, por el costo real en el grafo original
            COS = r.costo()
            COL = r.col()
            
            self.dicc_rutas['d%d_'%d+str(ID)]=r

            self.c.variables.add(obj = [COS],
                                    names = ['d%d_'%d+str(ID)],
                                    lb = [0.0],
                                    #ub=[0.0],
                                    columns = [cplex.SparsePair(ind = ['cliente_%d'%(k+1) for k in range(self.num_clientes) ]+['depot%d,cliente%d'%(d,i+1) for i in range(self.num_clientes)] + ['min_rutas_depot%d'%(d), 'max_rutas_depot%d'%(d)] + ['min_total_rutas','max_total_rutas'], val = COL+[-k for k in COL]+[1,1]+[1,1])])
                                    #NUEVO MAR2016: filas que corresponden a cotas
                                    #esto lo que hace es cargar la columna a la restriccion de servicio, y carga a la restriccion de localizacion el vector -columna + un par de 1s en las filas cotas del depot d
        else:
            print '\nesta ruta ya estaba: d%d_'%d+str(ID)+'\n'
            print r
            agregue = 0 
            #print 'CPLEX costo: '+str(self.c.objective.get_linear('d%d_'%d+str(ID)))
            #print 'RED: '+str(self.c.solution.get_reduced_costs('d%d_'%d+str(ID)))
    
        return(agregue)




# def indice(A,i):
#     valor=0
#     for k in range(len(A)):
#         for l in range(len(A[k])):
#             valor=valor+1 
#             if valor==i:
                # return(A[k][l])
    def report(self, f = sys.stdout):
        c = self.c
        print >>f,'\n============> Solucion PM <====================\n'
        print >>f,"Objetivo: " + str(c.solution.get_objective_value())+'\n'

        for v in range(c.variables.get_num()):
            
            if c.solution.get_values(v)!= 0.0:
                dep=str(c.variables.get_names(v))[0:2]
                if dep=='de':
                    print>> f, "Depot" + str(v) + " = " + str(c.solution.get_values(v))+', ID: '+str(c.variables.get_names(v))+', COST:  '+str(c.objective.get_linear(c.variables.get_names(v)))
                else:
                    ruta = self.dicc_rutas[c.variables.get_names(v)]
                    print >>f, "Ruta " + str(v) + " = " + str(c.solution.get_values(v))+', [lb, ub] = ['+str(c.variables.get_lower_bounds(v))+','+str(c.variables.get_upper_bounds(v))+'], ID: '+str(c.variables.get_names(v))+', COL: '+str(ruta.col())+', COST:  '+str(c.objective.get_linear(c.variables.get_names(v)))

    #NUEVO MAR 2016
    def guarda_incumbente(self):
        print("Guardando incumbente")
        c = self.c
        reporte = ""
        reporte = reporte + '\n============> Solucion PM <====================\n'
        reporte = reporte + "Objetivo: " + str(c.solution.get_objective_value())+'\n'
        reporte = reporte + "Status: " + str(c.solution.get_status())+'\n\n'


        for v in range(c.variables.get_num()):
            
            if c.solution.get_values(v)!= 0.0:
                dep=str(c.variables.get_names(v))[0:2]
                if dep=='de':
                    reporte = reporte + "Depot" + str(v) + " = " + str(c.solution.get_values(v))
                    reporte = reporte + ', ID: '+str(c.variables.get_names(v))
                    reporte = reporte + ', COST:  '+str(c.objective.get_linear(c.variables.get_names(v)))+"\n"
                else:
                    ruta = self.dicc_rutas[c.variables.get_names(v)]
                    reporte = reporte + "Ruta " + str(v) + " = " + str(c.solution.get_values(v))+', [lb, ub] = ['+str(c.variables.get_lower_bounds(v))+','+str(c.variables.get_upper_bounds(v))+'], ID: '+str(c.variables.get_names(v))+', COL: '+str(ruta.col())+', COST:  '+str(c.objective.get_linear(c.variables.get_names(v)))+"\n"

        """

        reporte.join('\n\n============> Solucion PM Incumbente <====================\n\n')
        reporte.join("Objetivo: " + str(c.solution.get_objective_value())+'\n\n')

        print(reporte)
        for v in range(c.variables.get_num()):
            
            if c.solution.get_values(v)!= 0.0:
                dep=str(c.variables.get_names(v))[0:2]
                if dep=='de':
                    reporte.join("Depot" + str(v) + " = " + str(c.solution.get_values(v)))
                    reporte.join(', ID: '+str(c.variables.get_names(v)))
                    reporte.join(', COST:  '+str(c.objective.get_linear(c.variables.get_names(v)))+"\n")
                else:
                    ruta = self.dicc_rutas[c.variables.get_names(v)]
                    reporte.join("Ruta " + str(v) + " = " + str(c.solution.get_values(v))+', [lb, ub] = ['+str(c.variables.get_lower_bounds(v))+','+str(c.variables.get_upper_bounds(v))+'], ID: '+str(c.variables.get_names(v))+', COL: '+str(ruta.col())+', COST:  '+str(c.objective.get_linear(c.variables.get_names(v)))+"\n")
        """

        print(reporte)
        return(reporte)
    
 
    def graficar(self):
        c = self.c



        for v in range(c.variables.get_num()):
        
            if c.solution.get_values(v)!= 0.0:
                dep=str(c.variables.get_names(v))[0:2]
                if dep!='de':
                    ruta = self.dicc_rutas[c.variables.get_names(v)]
                
                    
                    if dep=='d0':
                        Plot_ruta(Di[0],ruta.visitados(),1,c.variables.get_names(v))
                    if dep=='d1':
                        Plot_ruta(Di[1],ruta.visitados(),2,c.variables.get_names(v))
                    if dep=='d2':
                       Plot_ruta(Di[2],ruta.visitados(),3,c.variables.get_names(v))
                    if dep=='d3':
                       Plot_ruta(Di[3],ruta.visitados(),4,c.variables.get_names(v))
                    if dep=='d4':
                       Plot_ruta(Di[4],ruta.visitados(),5,c.variables.get_names(v))
                    if dep=='d5':
                       Plot_ruta(Di[5],ruta.visitados(),6,c.variables.get_names(v))
                    if dep=='d6':
                       Plot_ruta(Di[6],ruta.visitados(),7,c.variables.get_names(v))
       
    def dual_values(self):
        c = self.c
        ##Calculo Variables Duales
        pi = c.solution.get_dual_values(range(self.num_clientes))
        mu = []
        #NUEVO MAR2016
        alpha = []
        beta = []
        gamma1 = 0.0
        gamma2 = 0.0

        for i in range(self.num_clientes):               #restricciones de i,j cliente-depot, clientes de 1 a N, depots de 0 a J-1   =)
            mu.append([])
            for j in range(self.num_depots):
                nom_res='depot%d,cliente%d'%(j,i+1)
                mu[i].append(c.solution.get_dual_values(nom_res))

        #print(c.linear_constraints.get_names())


        #NUEVO MAR2016
        for j in range(self.num_depots):
            nom_res='min_rutas_depot%d'%(j)
            alpha.append(c.solution.get_dual_values(nom_res))

        for j in range(self.num_depots):
            nom_res='max_rutas_depot%d'%(j)
            beta.append(c.solution.get_dual_values(nom_res))
        
        gamma1 = c.solution.get_dual_values('min_total_rutas')
        gamma2 = c.solution.get_dual_values('max_total_rutas')


        #
        #print 'Mu:'
        #print mu
        #print 'Pi:'
        #print pi
        
        print ('alpha: '+str(alpha))
        print ('beta: '+str(beta))
        print ('gamma1: '+str(gamma1))
        print ('gamma2: '+str(gamma2))
        return pi,mu,alpha,beta,gamma1,gamma2

    #talvez 
    #def BB(self, gap=0.0, tiempomax=1800):
        
    def BB(self):
        c = self.c
        print '\n============> USANDO B&B de CPLEX <============'
        c.variables.set_types(zip(range(c.variables.get_num()),['I']*c.variables.get_num()))
        c.variables.set_lower_bounds(zip(range(c.variables.get_num()),[0.0]*c.variables.get_num()))
        c.variables.set_upper_bounds(zip(range(c.variables.get_num()),[1]*c.variables.get_num()))
        c.solve()
        self.report()
        return c.solution.get_objective_value()

    def CC(self):
        c = self.c
        c.variables.set_types(zip(range(c.variables.get_num()),['C']*c.variables.get_num()))
        c.set_problem_type(c.problem_type.LP)
        c.solve()
        return c.solution.get_objective_value()

    # def indice(A,i):
    #     valor=0
    #     for k in range(len(A)):
    #         for l in range(len(A[k])):
    #             valor=valor+1 
    #             if valor==i:
    #                 return(A[k][l])




    def pricing(self, ran):
        c = self.c
        calidad = [1]*self.num_depots
        calidad5 = [1]*self.num_depots
        calidad10 = [1]*self.num_depots
        for k in range(ran):
            if c.variables.get_num()>300000:
                break
            print "\nIteracion Pricing: # %d --------------------------------------------------------------"%(k+1)
            print 'Total de variables: %d'%c.variables.get_num()

            #MODIF MAR2016
            pi,mu,alpha,beta,gamma1,gamma2 = self.dual_values()
            #print pi, mu
          
            #poner en cero duales de cotas de rutas en depots cerrados
            for i in range(self.num_depots):
                if c.variables.get_upper_bounds(i) < 0.00001 and c.variables.get_lower_bounds(i) < 0.00001: 
                    alpha[i] = 0.0
                    beta[i] = 0.0

            ##Actualizar Costos Reducidos en grafos Auxiliares.
          
            #MODIF MAR2016
            for i in range(self.num_depots):
                actualizar(self.aux[i],self.Di[i],mu,pi,i,alpha,beta,gamma1,gamma2) #actualiza el grafo auxiliar con los costos reducidos
                actualizar(self.aux5[i],self.Di[i],mu,pi,i,alpha,beta,gamma1,gamma2) #actualiza el grafo auxiliar con los costos reducidos
                actualizar(self.aux10[i],self.Di[i],mu,pi,i,alpha,beta,gamma1,gamma2)
            #print aux.values()
            #print calidad
            #print len(aux5.values())
            #print len([61]*num_depots)
        
        
            # print "\nUsando grafo 5"
            a   = pool.map(heur_dominancia, zip(self.aux5.values(),calidad5))
            
            rutas_negativas,calidad5=zip(*a)
            #print 'calidad'+str(calidad)
            #print len(rutas_negativas[0])
            
            
            if sum([len(rutas_negativas[i]) for i in range(self.num_depots)])==0:
                print "\nUsando grafo 10"
                a   = pool.map(heur1, zip(self.aux10.values(),calidad10))
                rutas_negativas,calidad10=zip(*a)
                
            
            if sum([len(rutas_negativas[i]) for i in range(self.num_depots)])==0:
                print "\nUsando grafo 10"
                a   = pool.map(heur_dominancia, zip(self.aux10.values(),calidad10))
                rutas_negativas,calidad10=zip(*a)
            
            if sum([len(rutas_negativas[i]) for i in range(self.num_depots)])==0:
                print "\nUsando grafo total"
                a   = pool.map(heur1, zip(self.aux.values(),calidad))
                rutas_negativas,calidad=zip(*a)    
            
            if sum([len(rutas_negativas[i]) for i in range(self.num_depots)])==0:
                # MODIF ABRIL 2017
                # LLAMAR A PRICING EXACTO 
                # ESTO ES PARALELO, CAMBIAR Y LLAMAR A UN SOLO PRICING QUE CORRA SECUENCIALMENTE PARA LOS DEPOTS
                print "\nUsando MIP"
                a   = pool.map(pricing_exacto_MIP, zip(self.aux.values(),calidad))
                rutas_negativas,calidad=zip(*a)    
            
            contador=0  
            for d in range(self.num_depots):
                for r in rutas_negativas[d]:
                    #print r
                    agregue = self.anadir_ruta(r, d)
                    ID=r.visitados()
                    
                    #print '\Agrego: d%d_'%d+str(ID)+'\n'
                    
                    #print 'CPLEX costo: '+str(c.objective.get_linear('d%d_'%d+str(ID)))
                    #print 'pi A = '+str(sum([x*y for (x,y) in zip(r.col(),pi)]))
                    #print 'RED: '+str(c.solution.get_reduced_costs('d%d_'%d+str(ID)))
                    #c.solve()
                    #report(c)
                    #pi,mu=dual_values(c)
                    #print 'pi A = '+str(sum([x*y for (x,y) in zip(r.col(),pi)]))
                    contador=contador+agregue

            if contador==0:
                print "No Agregamos rutas en esta iteracion, BREAK"

                break
               
            print "Agregamos %d rutas en esta iteracion"%contador
            print "Quedamos con %d"%c.variables.get_num()
            c.solve()
            self.report()
            #pi,mu=dual_values(c)
            #c.write('P'+str(k+1),'lp')
        self.pricing_has_been_runned = True
        return
        
    def pricingMOD(self, rules, rules_depots, minru, maxru,total_rutas): #rules es un diccionario de la forma {(0,1):True, (1,2):False,...} usando el branching sugerido por Dumas 1991
        c = self.c
        calidad=[1]*self.num_depots

        print '\n#######Branch en la rama: '+str(rules)+str(rules_depots)+"MinRu: " + str(minru)+"MaxRu: " + str(maxru) + " Total rutas: " + str(total_rutas)

        #MODIF MAR2016
        if rules == {} and rules_depots == [-1]*self.num_depots and minru == [0 for x in range(self.num_depots)] and maxru == [self.num_clientes for x in range(self.num_depots)] and total_rutas == [0,self.num_clientes]:
            return
        print 'Total de variables: %d'%c.variables.get_num()
        self.apagar_rutas(rules)
        print rules_depots
        self.cerrar_depots(rules_depots)
        print("MinRu: " + str(minru))
        print("MaxRu: " + str(maxru))

        self.fijar_flujos(minru,maxru)

        c.linear_constraints.set_rhs('min_total_rutas',total_rutas[0])
        c.linear_constraints.set_rhs('max_total_rutas',total_rutas[1])
        print("Con total_rutas: " + str(total_rutas) + " fijamos : ")
        print("       total rutas >= " + str(c.linear_constraints.get_rhs('min_total_rutas')))
        print("       total rutas <= " + str(c.linear_constraints.get_rhs('max_total_rutas')))

        c.solve()

        #MODIF MAR2016
        pi,mu,alpha,beta,gamma1,gamma2 = self.dual_values()

          
        #poner en cero duales de cotas de rutas en depots cerrados
        for i in range(self.num_depots):
           if c.variables.get_upper_bounds(i) < 0.00001 and c.variables.get_lower_bounds(i) < 0.00001: 
               alpha[i] = 0.0
               beta[i] = 0.0

        ##Actualizar Costos Reducidos en grafos dep
        
        #MODIF MAR2016
        for i in range(self.num_depots):
            actualizar(self.aux[i],self.Di[i],mu,pi,i,alpha,beta,gamma1,gamma2) #actualiza el grafo auxiliar con los costos reducidos
            actualizar(self.aux5[i],self.Di[i],mu,pi,i,alpha,beta,gamma1,gamma2) #actualiza el grafo auxiliar con los costos reducidos
            actualizar(self.aux10[i],self.Di[i],mu,pi,i,alpha,beta,gamma1,gamma2)
        #print aux.values()
        #print calidad
        #print len(aux5.values())
        #print len([61]*num_depots)


        print "\nUsando grafo 5"
        a   = pool.map(heur_branch2, zip(self.aux5.values(),calidad,[rules]*self.num_depots))
        
        rutas_negativas,calidad=zip(*a)

        if sum([len(rutas_negativas[i]) for i in range(self.num_depots)])==0:
            print "\nUsando grafo 10"
            a   = pool.map(heur_branch2, zip(self.aux10.values(),calidad,[rules]*self.num_depots))
            
            rutas_negativas,calidad=zip(*a)
        if sum([len(rutas_negativas[i]) for i in range(self.num_depots)])==0:
            print "\nUsando grafo total"
            a   = pool.map(heur_branch1, zip(self.aux.values(),calidad,[rules]*self.num_depots))
            rutas_negativas,calidad=zip(*a)
            
        contador=0
        
        for d in range(self.num_depots):
            for r in rutas_negativas[d]:
                #print r
                self.anadir_ruta(r, d)
                #print r
                contador=contador+1
        if contador<4:
            print "No Agregamos rutas en esta iteracion, BREAK"
            #break
                
        print "Agregamos %d rutas en esta iteracion"%contador
        c.solve()
        return
    




    def cerrar_depots(self, L):
        c = self.c
        for dep in range(len(L)):
            if L[dep]==1:
                c.variables.set_upper_bounds(dep, 1)
                c.variables.set_lower_bounds(dep, 1)
            if L[dep]==0:
                c.variables.set_upper_bounds(dep, 0)
                c.variables.set_lower_bounds(dep, 0)
                print c.variables.get_names(dep)
                print 'se puso en cero putos!'
            if L[dep]==-1:
                c.variables.set_upper_bounds(dep, 1)
                c.variables.set_lower_bounds(dep, 0)
        return

    #NUEVO MAR2016
    def fijar_flujos(self,minru,maxru):
        c = self.c
        for j in range(self.num_depots):               #fijar cotas  en el numero de rutas por depot para pricing 
           nom_res='min_rutas_depot%d'%(j)
           c.linear_constraints.set_rhs(nom_res,minru[j])
           nom_res='max_rutas_depot%d'%(j)
           c.linear_constraints.set_rhs(nom_res,maxru[j])

           """
           print("DENTRO DE FIJAR FLUJOS")
           cotas_inf = []
           cotas_sup = []

           for j in range(self.num_depots):               #leer cotas  en el numero de rutas por depot para pricing 
                nom_res='min_rutas_depot%d'%(j)
                cotas_inf.append(c.linear_constraints.get_rhs(nom_res))
                nom_res='max_rutas_depot%d'%(j)
                cotas_sup.append(c.linear_constraints.get_rhs(nom_res))
           
           print("Minru: " + str(minru)) 
           print("Cotas_inf: " + str(cotas_inf)) 
           print("Maxru: " + str(maxru)) 
           print("Cotas_sup: " + str(cotas_sup)) 
           """
        return




    def apagar_rutas(self, dicc):
        c = self.c
        for r in self.dicc_rutas: #diccionario de las soluciones actuales del problema de cplex (variables)
            visitados = self.dicc_rutas[r].visitados() #nodos que visita la ruta r
            c.variables.set_upper_bounds(r, cplex.infinity)
           # print 'revisando:'+str(visitados)
            for a,b in dicc: #dicc son las reglas de branch de Dumas 1991, de la forma {(1,3):True}
               # print 'revisando %d,%d'%(a,b)
                if a in visitados and b in visitados and visitados.index(a)<visitados.index(b): # la ruta r contiene a los pickups a < b
                    if dicc[(a,b)]:#a debe venir despues de b
                        if set(A(visitados, a,b)).intersection(set(self.P))!=set([]):#hay pickups entre a y b
                            c.variables.set_upper_bounds(r, 0.0)
                            #print 'apago la ruta: '+r
                    else:
                        if set(A(visitados, a,b)).intersection(set(self.P))==set([]):
                            c.variables.set_upper_bounds(r, 0.0)
                            #print 'apago la ruta: '+r
                #if a in visitados and b not in visitados and dicc[(a,b)]:
                 #   c.variables.set_upper_bounds(r, 0.0)
                    #print 'apago la ruta: '+r
        return





    def branch_and_price(self, nodos_parada = 150, gap = 0.005):
        '''
        Variables:
        nodos_parada = 150
        gap = 0.005
        '''
        c = self.c

        variables_iniciales = c.variables.get_num()

        if not self.pricing_has_been_runned:
            self.pricing(self.num_iter_pric)
        
        
        variables_raiz = c.variables.get_num()  
        t_raiz = time.time() - self.hora_inicio

        UB = self.BB()
        Mejor_c = self.guarda_incumbente()        
        LB = self.CC()  

        LB_root = LB

        depots_usados=[]
        c.solve()
        #version Marzo2016
        N0 = Nodo_branch({},{},[-1 for x in range(self.num_depots)],LB,UB,[0 for x in range(self.num_depots)],[self.num_clientes for x in range(self.num_depots)],[0,self.num_clientes])
        LISTA = []
        LISTA.append(N0)
        nodos_creados = 0
        nodos_depot = 0
        nodos_flujos = 0
        nodos_flujosd = 0
        nodos_ruta = collections.defaultdict(int)
        mejora_incumbente = 0 
        

        epsilon = 0.001
        variable_rutas_ya_brancheadas = []

        nodos_abiertos = set()
         
        t_branch = time.time()
        
        while LISTA and UB/LB > (1+gap) and (time.time()-t_branch<14400):
 
            self.CC()
            print 'Quedan %d nodos sin procesar'%len(LISTA)
            #print 'Rutas ya procesadas: '+str(variable_rutas_ya_brancheadas)
            if nodos_creados>nodos_parada:
                print 'Salimos por el contador'
                break
            Nodo = LISTA.pop()
            rule = Nodo.rules
            rules_depots = Nodo.rules_depots
            #mod marzo2016
            minru = Nodo.min_rutas
            maxru = Nodo.max_rutas
            total_ru = Nodo.total_rutas
            ttotal_ru = total_ru[:]
            try:
                #for d in range(num_depots):#sin MT
                #    pricingMOD(c,d,rule)
                self.pricingMOD(rule,rules_depots,minru,maxru,total_ru)

                cotas_inf = []
                cotas_sup = []

                for j in range(self.num_depots):               #leer cotas  en el numero de rutas por depot para pricing 
                     nom_res='min_rutas_depot%d'%(j)
                     cotas_inf.append(c.linear_constraints.get_rhs(nom_res))
                     nom_res='max_rutas_depot%d'%(j)
                     cotas_sup.append(c.linear_constraints.get_rhs(nom_res))
                
                print("Minru: " + str(minru)) 
                print("Cotas_inf: " + str(cotas_inf)) 
                print("Maxru: " + str(maxru)) 
                print("Cotas_sup: " + str(cotas_sup)) 

                total_r = [c.linear_constraints.get_rhs('min_total_rutas'),c.linear_constraints.get_rhs('max_total_rutas')]

                print("Total_ru: " + str(total_ru)) 
                print("Cotas: " + str(total_r)) 

                
                c.solve()
                self.report()
            
                print 'SOLUTION STATUS: '+str(c.solution.get_status())
                print 'Branch: '+str(rule)+str(rules_depots)
                print 'UB: %f'%UB
                loc_var_branch = {}
                # volvi route_var_branch a {} lo tenia como dict() 
                route_var_branch = {}
                depot_flow_branch = dict()

                depots_enteros = True
                num_rutas_entero = True
                flujos_enteros = True

                sol_entera = True

                var_rutas_depots = dict()
                for dd in range(self.num_depots):
                     var_rutas_depots[dd] = set()
                     #print("Dep: " + str(dd) + "  var_rutas_depots: " + str(type(var_rutas_depots[dd])))
                        

        ########BRANCH EN LOCATION
                for i in range(self.num_depots):
                    if abs(1-c.solution.get_values(i))>epsilon and abs(c.solution.get_values(i))>epsilon: #veo si la variable es igual a su cajon inferior  OJO variable puede ser mayor a 1
                        print("Analizando variable de depot " + str(i) + "valor = " + str(c.solution.get_values(i)))
                        loc_var_branch[c.variables.get_names(i)]= c.solution.get_values(i)# di vuelta
                        depots_enteros=False
                print '\nLas variables de localizacion (1) a branchear son: '+str(loc_var_branch)+'\n'



        ########BRANCH EN NUMERO TOTAL DE RUTAS
                
                if depots_enteros:
                   flujo_total = sum([c.solution.get_values(v) for v in range(self.num_depots,c.variables.get_num())])
                   print("Total rutas: " + str(flujo_total))
                   if (abs(flujo_total - math.floor(flujo_total)) > epsilon) and (abs(flujo_total - math.ceil(flujo_total)) > epsilon):
                         print("Hacer branching en total de rutas, flujo total: " + str(flujo_total))
                         num_rutas_entero = False

        ########BRANCH EN NUMERO DE RUTAS DEPOT
                
                if depots_enteros and num_rutas_entero:
                    for v in range(self.num_depots,c.variables.get_num()):
                        if c.solution.get_values(v)!= 0.0:
                             temp_var = c.variables.get_names(v)
                             temp_dep = int(temp_var[1])
                             (var_rutas_depots[temp_dep]).add(temp_var) 
                    for dd in range(self.num_depots):
                        flujo = sum([c.solution.get_values(i) for i in var_rutas_depots[dd]])
                        print("Flujo: " + str(flujo))
                        print("floor(Flujo): " + str(math.floor(flujo)))
                        if (abs(flujo - math.floor(flujo)) > epsilon) and (abs(flujo - math.ceil(flujo)) > epsilon):
                              print("Agregar depot!")
                              depot_flow_branch[dd] = flujo
                              flujos_enteros = False
                #OJO
                #flujos_enteros = True  

        ########BRANCH EN RUTAS (si no hubo en loc)        
                sol_entera =  depots_enteros and num_rutas_entero and flujos_enteros
                if sol_entera:
                #hace branching en flujos y rutas
                #if sol_entera==True:
                    for v in range(self.num_depots,c.variables.get_num()):
                        if c.solution.get_values(v)!= 0.0:
                            if abs(1-c.solution.get_values(v))>epsilon and abs(c.solution.get_values(v))>epsilon:
                            #if round(c.solution.get_values(v)+epsilon)!=c.solution.get_values(v): #veo si la variable es igual a su cajon inferior  OJO variable puede ser mayor a 1
                                sol_entera=False
                                if c.variables.get_names(v) not in variable_rutas_ya_brancheadas:
                                    route_var_branch[c.variables.get_names(v)]=c.solution.get_values(v) #di vuelta
                                    print("Para ver que es:")
                                    print("key: "+str(c.solution.get_values(v)) + "  value: " + str(c.variables.get_names(v)) )
                                    print("route_var_branch: " + str(route_var_branch))
                                else:
                                    print c.variables.get_names(v)
                                    print 'ya se proceso 1 vez!'
                print("route_var_branch FINAL: " + str(route_var_branch))

                #ACA SE AGREGAN LOS NODOS
                #MODI MARZO2016

                if sol_entera and c.solution.get_status()==1:
                    if c.solution.get_objective_value()<UB:
                        print '\nEsta solucion cambio el UB:'
                        self.report()
                        UB = c.solution.get_objective_value()
                        print'\nLa solucion es ENTERA!!!, actualizo el UB'
                        #MODI MARZO2016

                        #como report, pero guarda la info del incumbente en una string
                        print("Guardo incumbente: \n\n")
                        Mejor_c = self.guarda_incumbente()
                        print(Mejor_c)
                        mejora_incumbente += 1



                else:
                    if c.solution.get_status()==1:
                        print '\nLas variables de rutas a branchear son: '+str(route_var_branch)+'\n'


                if len(loc_var_branch)>0  and c.solution.get_status()==1 and c.solution.get_objective_value()<UB:

                    ldep = loc_var_branch.keys()
                    lvalue = loc_var_branch.values()
                    maxtemp = -1
                    maxind = -1
                    for i in range(len(lvalue)):
                         frac = lvalue[i]-math.floor(lvalue[i])
                         ff = min(frac, 1-frac)
                         if ff > maxtemp:
                              maxtep = ff
                              maxind = ldep[i]
                    depot = maxind
                    #Resolver con var=0
                    depot_numero = int(depot[5:])
                    ###rama=1
                    #MAR 2016 SOLO SI NO FIJAMOS LA COTA INF SUBIENDO MINRU
                    aux_rules_depots = rules_depots[:]
                    aux_rules_depots[depot_numero] = 1
                    #mod marzo2016
                    #poner al menos en 1 lower bounds de depot abierto
                    mminru = minru[:]
                    mminru[depot_numero] = max(mminru[depot_numero],1) 
                    Nodo_nuevo = Nodo_branch(Nodo,rule,aux_rules_depots,LB,UB,mminru,maxru,total_ru)
                    if Nodo_nuevo not in nodos_abiertos:
                         nodos_abiertos.add(Nodo_nuevo)
                         LISTA.append(Nodo_nuevo)
                         nodos_creados=nodos_creados+1
                         nodos_depot += 1
                         print ('agregamos nuevo NODO: ' + str(nodos_creados) + ' DEPOT ABIERTO: '+str(depot_numero)+" "+str(Nodo_nuevo) )
                    else:
                         print ('IGNORAMOS nuevo NODO: '  + ' DEPOT ABIERTO: '+str(depot_numero)+" "+str(Nodo_nuevo) )
                    ###rama=0
                    #MAR 2016 SOLO SI NO FIJAMOS LA COTA SUP SUBIENDO MAXRU
                    aux_rules_depots=rules_depots[:]
                    aux_rules_depots[depot_numero]=0
                    #mod marzo2016
                    #poner en cero upper bounds de depot cerrado
                    mmaxru = maxru[:]
                    mmaxru[depot_numero] = 0 
                    Nodo_nuevo=Nodo_branch(Nodo,rule,aux_rules_depots,LB,UB,minru,mmaxru,total_ru)                 
                    if Nodo_nuevo not in nodos_abiertos:
                         nodos_abiertos.add(Nodo_nuevo)
                         LISTA.append(Nodo_nuevo)
                         nodos_creados=nodos_creados+1
                         nodos_depot += 1
                         print('agregamos nuevo NODO ' + str(nodos_creados) + ' DEPOT CERRADO: '+str(depot_numero)+" "+str(Nodo_nuevo) ) 
                    else:
                         print('IGNORAMOS nuevo NODO ' + ' DEPOT CERRADO: '+str(depot_numero)+" "+str(Nodo_nuevo) ) 

                    """
                    #brancheo en todos los depots fraccionarios NO
                    for depot in loc_var_branch.keys():
                         #Resolver con var=0
                         depot_numero = int(depot[5:])
                         ###rama=1
                         #MAR 2016 SOLO SI NO FIJAMOS LA COTA INF SUBIENDO MINRU
                         aux_rules_depots = rules_depots[:]
                         aux_rules_depots[depot_numero] = 1
                         #mod marzo2016
                         #poner al menos en 1 lower bounds de depot abierto
                         mminru = minru[:]
                         #mminru[depot_numero] = max(mminru[depot_numero],1) 
                         Nodo_nuevo = Nodo_branch(Nodo,rule,aux_rules_depots,LB,UB,mminru,maxru,total_ru)
                         if Nodo_nuevo not in nodos_abiertos:
                              nodos_abiertos.add(Nodo_nuevo)
                              LISTA.append(Nodo_nuevo)
                              contador=contador+1
                              print ('agregamos nuevo NODO: ' + str(contador) + ' DEPOT ABIERTO: '+str(depot_numero)+" "+str(Nodo_nuevo) )
                         else:
                              print ('IGNORAMOS nuevo NODO: '  + ' DEPOT ABIERTO: '+str(depot_numero)+" "+str(Nodo_nuevo) )
                         ###rama=0
                         #MAR 2016 SOLO SI NO FIJAMOS LA COTA SUP SUBIENDO MAXRU
                         aux_rules_depots=rules_depots[:]
                         aux_rules_depots[depot_numero]=0
                         #mod marzo2016
                         #poner en cero upper bounds de depot cerrado
                         mmaxru = maxru[:]
                         #mmaxru[depot_numero] = 0 
                         Nodo_nuevo=Nodo_branch(Nodo,rule,aux_rules_depots,LB,UB,minru,mmaxru,total_ru)                 
                         if Nodo_nuevo not in nodos_abiertos:
                              nodos_abiertos.add(Nodo_nuevo)
                              LISTA.append(Nodo_nuevo)
                              contador=contador+1
                              print('agregamos nuevo NODO ' + str(contador) + ' DEPOT CERRADO: '+str(depot_numero)+" "+str(Nodo_nuevo) ) 
                         else:
                              print('IGNORAMOS nuevo NODO ' + ' DEPOT CERRADO: '+str(depot_numero)+" "+str(Nodo_nuevo) ) 
                    """




                #MARZO 2016

                if (not num_rutas_entero) and c.solution.get_status()==1 and c.solution.get_objective_value()<UB:
                    print("Branchear en total de rutas fraccionario ")
                    #rama hacia arriba
                    ttotal_ru = total_ru[:]
                    ttotal_ru[0] = int(math.ceil(flujo_total))
                    Nodo_nuevo=Nodo_branch(Nodo,rule,rules_depots,LB,UB,minru,maxru,ttotal_ru) 
                    if Nodo_nuevo not in nodos_abiertos:
                         nodos_abiertos.add(Nodo_nuevo)
                         LISTA.append(Nodo_nuevo)
                         nodos_creados=nodos_creados+1
                         nodos_flujos += 1
                         print ('agregamos nuevo NODO ' + str(nodos_creados) + ' FLUJO TOTAL RAMA ARRIBA: ' +  str(dd) + " Flujo: " + str(flujo_total) +  " a "  + str(math.ceil(flujo_total)) + " " +str(Nodo_nuevo)) 
                    else:
                         print ('IGNORAMOS nuevo NODO ' + ' FLUJO TOTAL RAMA ARRIBA: ' +  str(dd) + " Flujo: " + str(flujo_total) +  " a "  + str(math.ceil(flujo_total)) + " " +str(Nodo_nuevo)) 
                         
                    #rama hacia abajo
                    ttotal_ru = total_ru[:]
                    ttotal_ru[1] = int(math.floor(flujo_total))
                    Nodo_nuevo=Nodo_branch(Nodo,rule,rules_depots,LB,UB,minru,maxru,ttotal_ru) 
                    if Nodo_nuevo not in nodos_abiertos:
                         nodos_abiertos.add(Nodo_nuevo)
                         LISTA.append(Nodo_nuevo)
                         nodos_creados=nodos_creados+1
                         nodos_flujos += 1
                         print ('agregamos nuevo NODO ' + str(nodos_creados) + ' FLUJO TOTAL RAMA ABAJO: ' +  str(dd) + " Flujo: " + str(flujo_total) +  " a "  + str(math.floor(flujo_total)) + " " +str(Nodo_nuevo)) 
                    else:
                         print ('IGNORAMOS nuevo NODO ' + ' FLUJO TOTAL RAMA ABAJO: ' +  str(dd) + " Flujo: " + str(flujo_total) +  " a "  + str(math.floor(flujo_total)) + " " +str(Nodo_nuevo)) 
                         
                
                #MARZO 2016
                
                #if len(depot_flow_branch) > 0  and c.solution.get_status()==1 and c.solution.get_objective_value()<UB:
                if len(depot_flow_branch) > 0 and (not flujos_enteros) and c.solution.get_status()==1 and c.solution.get_objective_value()<UB:
                    """
                    print("Depots a branchear por flujo fracionario: ")
                    print(depot_flow_branch)
                    #branching en todos los depots fraccionarios
                    for dd in depot_flow_branch.keys(): 
                         #rama hacia arriba
                         minru0 = minru[:]
                         minru0[dd] = int(math.ceil(depot_flow_branch[dd]))
                         #si hay rutas, entonces hay que fijar el depot en 1
                         aux_rules_depots = rules_depots[:]
                         if minru0[dd] > 0:
                              aux_rules_depots[dd] = 1                
                         Nodo_nuevo=Nodo_branch(Nodo,rule,aux_rules_depots,LB,UB,minru0,maxru,total_ru) 
                         if Nodo_nuevo not in nodos_abiertos:
                              nodos_abiertos.add(Nodo_nuevo)
                              LISTA.append(Nodo_nuevo)
                              contador=contador+1
                              print ('agregamos nuevo NODO ' + str(contador) + ' FLUJOS RAMA ARRIBA: ' +  str(dd) + " Flujo: " + str(depot_flow_branch[dd]) +  " a "  + str(math.ceil(depot_flow_branch[dd])) + " " +str(Nodo_nuevo)) 
                         else:
                              print ('IGNORAMOS nuevo NODO ' + ' FLUJOS RAMA ARRIBA: ' +  str(dd) + " Flujo: " + str(depot_flow_branch[dd]) +  " a "  + str(math.ceil(depot_flow_branch[dd])) + " " +str(Nodo_nuevo)) 
                         
                         #rama hacia abajo
                         maxru0 = maxru[:]
                         maxru0[dd] = int(math.floor(depot_flow_branch[dd]))                    
                         #no abrir SI fijamos flujo 0 a un depot abierto
                         if (maxru0[dd] > epsilon) or (c.variables.get_lower_bounds(dd) < 1):
                              #si ponemos maxru en cero, cerrar depot
                              aux_rules_depots = rules_depots[:]
                              if maxru0[dd] == 0:
                                   aux_rules_depots[dd] = 0                
                              Nodo_nuevo=Nodo_branch(Nodo,rule,aux_rules_depots,LB,UB,minru,maxru0,total_ru)                 
                              if Nodo_nuevo not in nodos_abiertos:
                                   nodos_abiertos.add(Nodo_nuevo)
                                   LISTA.append(Nodo_nuevo)
                                   contador=contador+1
                                   print ('agregamos nuevo NODO ' + str(contador) + ' FLUJOS RAMA ABAJO: '+ str(dd) + " Flujo: " + str(depot_flow_branch[dd]) +  " a " + str(math.floor(depot_flow_branch[dd])) + " " +str(Nodo_nuevo))
                              else: 
                                   print ('IGNORAMOS nuevo NODO ' + ' FLUJOS RAMA ABAJO: '+ str(dd) + " Flujo: " + str(depot_flow_branch[dd]) +  " a " + str(math.floor(depot_flow_branch[dd])) + " " +str(Nodo_nuevo))

                    depot_flow_branch.clear()

                

                   """
                    #branching en depot mas fraccionario
                    ldep = depot_flow_branch.keys()
                    lvalue = depot_flow_branch.values()
                    maxtemp = -1
                    maxind = -1
                    for i in range(len(lvalue)):
                         frac = lvalue[i]-math.floor(lvalue[i])
                         ff = min(frac, 1-frac)
                         if ff > maxtemp:
                              maxtep = ff
                              maxind = ldep[i]
                    dd = maxind
                    #rama hacia arriba
                    minru0 = minru[:]
                    minru0[dd] = int(math.ceil(depot_flow_branch[dd]))
                    #si hay rutas, entonces hay que fijar el depot en 1
                    aux_rules_depots = rules_depots[:]
                    if minru0[dd] > 0:
                         aux_rules_depots[dd] = 1                
                    Nodo_nuevo=Nodo_branch(Nodo,rule,aux_rules_depots,LB,UB,minru0,maxru,total_ru) 
                    if Nodo_nuevo not in nodos_abiertos:
                         nodos_abiertos.add(Nodo_nuevo)
                         LISTA.append(Nodo_nuevo)
                         nodos_creados=nodos_creados+1
                         nodos_flujosd += 1
                         print ('agregamos nuevo NODO ' + str(nodos_creados) + ' FLUJOS RAMA ARRIBA: ' +  str(dd) + " Flujo: " + str(depot_flow_branch[dd]) +  " a "  + str(math.ceil(depot_flow_branch[dd])) + " " +str(Nodo_nuevo)) 
                    else:
                         print ('IGNORAMOS nuevo NODO ' + ' FLUJOS RAMA ARRIBA: ' +  str(dd) + " Flujo: " + str(depot_flow_branch[dd]) +  " a "  + str(math.ceil(depot_flow_branch[dd])) + " " +str(Nodo_nuevo)) 

                    
                    #rama hacia abajo
                    maxru0 = maxru[:]
                    maxru0[dd] = int(math.floor(depot_flow_branch[dd]))                    
                    #no abrir SI fijamos flujo 0 a un depot abierto
                    if (maxru0[dd] > epsilon) or (c.variables.get_lower_bounds(dd) < 1):
                         #si ponemos maxru en cero, cerrar depot
                         aux_rules_depots = rules_depots[:]
                         if maxru0[dd] == 0:
                              aux_rules_depots[dd] = 0                
                         Nodo_nuevo=Nodo_branch(Nodo,rule,aux_rules_depots,LB,UB,minru,maxru0,total_ru)                 
                         if Nodo_nuevo not in nodos_abiertos:
                              nodos_abiertos.add(Nodo_nuevo)
                              LISTA.append(Nodo_nuevo)
                              nodos_creados=nodos_creados+1
                              nodos_flujosd += 1

                              print ('agregamos nuevo NODO ' + str(nodos_creados) + ' FLUJOS RAMA ABAJO: '+ str(dd) + " Flujo: " + str(depot_flow_branch[dd]) +  " a " + str(math.floor(depot_flow_branch[dd])) + " " +str(Nodo_nuevo))
                         else: 
                              print ('IGNORAMOS nuevo NODO ' + ' FLUJOS RAMA ABAJO: '+ str(dd) + " Flujo: " + str(depot_flow_branch[dd]) +  " a " + str(math.floor(depot_flow_branch[dd])) + " " +str(Nodo_nuevo))

                    depot_flow_branch.clear()



                if len(route_var_branch)>0  and c.solution.get_status()==1 and c.solution.get_objective_value()<UB:
                    l=len(route_var_branch)
                    
                    #ARREGLAR ACA RANDOM
                    #ruta=route_var_branch[random.choice(route_var_branch.keys())]
                    """
                    ruta=random.choice(route_var_branch.keys())
                    print("Elegimos ruta: " + str(ruta) + " para branchear")
                    print("Visitados: " + str(self.dicc_rutas[ruta].visitados()))
                    print("D: " + str(self.D))
                    """

                    # hacemos el branching en la ruta mas corta fraccionaria, y en caso de empate, en la que tiene el set "visitados" mas chico... vaya a saber que hash usa...
                    # voy a modificarlo para: hacer el branching en la ruta mas fraccionaria, en caso de empate, la mas corta de las mas fraccionarias y si no por hash
                    largo_min = 1000
                    parte_frac = -1.0
                    for r in route_var_branch.keys():
                        frac_r = min([abs(route_var_branch[r]),abs(1.0-route_var_branch[r])])
                        if frac_r - 0.0001 > parte_frac:
                            parte_frac = frac_r
                            largo_min = len(self.dicc_rutas[r].visitados())
                            ruta = r
                        elif abs(parte_frac - frac_r) < 0.0001:
                            if len(self.dicc_rutas[r].visitados()) < largo_min:
                                parte_frac = frac_r
                                largo_min = len(self.dicc_rutas[r].visitados())
                                ruta = r
                            elif len(self.dicc_rutas[r].visitados()) == largo_min:
                                if self.dicc_rutas[r].visitados() < self.dicc_rutas[ruta].visitados():
                                    parte_frac = frac_r
                                    ruta = r

                    print("Elegimos ruta: " + str(ruta) + " para branchear")
                    print("Visitados: " + str(self.dicc_rutas[ruta].visitados()))
                    print("D: " + str(self.D))

                    variable_rutas_ya_brancheadas.append(ruta)
                    branch0 = branch_rule(self.dicc_rutas[ruta].visitados(), self.D)



                    for regla in branch0:
                        aux_rule = rule.copy()
                        aux_rule.update(regla)
                        #mod marzo2016
                        Nodo_nuevo=Nodo_branch(Nodo,aux_rule,rules_depots,LB,UB,minru,maxru,total_ru)
                        if Nodo_nuevo not in nodos_abiertos:
                             nodos_abiertos.add(Nodo_nuevo)
                             LISTA.append(Nodo_nuevo)
                             nodos_creados=nodos_creados+1
                             nodos_ruta[len(self.dicc_rutas[ruta].visitados())] += 1
                             print 'agregamos nuevo NODO ' + str(nodos_creados) + ' RUTAS: '+str(Nodo_nuevo)
                        else:
                             print 'IGNORAMOS nuevo NODO '  + ' RUTAS: '+str(Nodo_nuevo)
            except CplexError, exc:
                print exc

            print("FIN LOOP con len(LISTA): " + str(len(LISTA)) + " UB: " + str(UB)  + " LB: " + str(LB)  + " UB/LB: " + str(UB/LB) + " tiempo: " + str(time.time()-t_branch) + " contador: " + str(nodos_creados)) 
        #while route_var_branch: #mientras queden variables en la pila
        #    ruta=route_var_branch.pop(0) 

        f = open(self.path+self.prefix+str(self.num_clientes)+'_'+str(self.version)+'c='+str(self.costo_depot)+'_Resultado.dat', 'w')
        # self.report(f)
        
        #NO RESOLVER MIP AL FINAL
        #self.BB()
        
        #actualizar UB si mejor entera final, 

        #AGOSTO 2017 DESACTIVE ESTO: OJO REVISAR
        """
        for i in range(self.num_depots):
          if abs(1-c.solution.get_values(i))>epsilon and abs(c.solution.get_values(i))>epsilon: #veo si la variable es igual a su cajon inferior  OJO variable puede ser mayor a 1
              print("Analizando variable de depot " + str(i) + "valor = " + str(c.solution.get_values(i)))
              loc_var_branch[c.variables.get_names(i)]= c.solution.get_values(i)# di vuelta
              depots_enteros=False
              print '\nLas variables de localizacion (2) a branchear son: '+str(loc_var_branch)+'\n'
        
        if c.solution.get_status()==1 and c.solution.get_objective_value()<UB:
           sol_entera = True
           #verificar si es entera
           for xx in c.solution.get_values():
              frac = xx - math.floor(xx)
              ff = min(frac, 1-frac)
              if ff > epsilon:
                  sol_entera = False
                  break
           if sol_entera:
              print '\nEsta solucion final cambio el UB:'
              self.report()
              UB = c.solution.get_objective_value()
              print'\nLa solucion es ENTERA!!!, actualizo el UB'
              #MODI MARZO2016
        """
        #actualizar LB si se termino por acabarse el arbol        
        #if len(LISTA) == 0 and nodos_creados >= 1:
        #    LB = UB 


        print >>f, 'UB: '+str(UB)+', LB: '+str(LB)+', GAP: '+str(100*(UB/LB-1))+', Nodos B&B: '+str(nodos_creados)
        print >>f,'Tiempos (Total, Raiz, Branching): (%d,%d,%d)' %(-self.hora_inicio+time.time(), t_raiz, -t_branch+time.time())
        print >>f,'Total de variables (Total, Raiz, Iniciales): (%d,%d,%d)'%(c.variables.get_num(), variables_raiz, variables_iniciales)
        
        if c.solution.get_status()==1:
             self.report(f)
        else: 
             print("PROBLEMAS PARA IMPRIMIR")
             print("\n*************  Incumbente ************* \n")
             f.write(Mejor_c)


        #Modif Marzo2016
        """
        if c.solution.get_objective_value() > UB:
             f.write("\n **********Mejor incumbente que IP final************* \n")
             f.write(Mejor_c)
        """
        f.write("\n\n\n")
        f.write("Nodos depot: " + str(nodos_depot) + "\n")
        f.write("Nodos flujos: " + str(nodos_flujos)+ "\n")
        f.write("Nodos flujos depot: " + str(nodos_flujosd)+ "\n")
        #f.write("Nodos ruta: " + str(nodos_ruta)+ "\n")
        imprimir_nodos_ruta(f,nodos_ruta)
        f.write("Mejora incumbente: " + str(mejora_incumbente)+ "\n")
        f.write("LB root: " + str(LB_root) + "\n")



        f.close()
        



if __name__=='__main__':
    
    #try instancia de 5 clientes, ejemplo base     
    plr = LRP()
    plr.branch_and_price()
     
        

        
    

