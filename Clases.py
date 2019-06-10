
class Ruta:
    
    def __init__(self, j, S, T, R,id,*calidad): # j es el nodo terminal, S conjunto de nodos visitados,  T el tiempo hasta j, R el costo reducido
        self.j = j
        self.S = S
        self.T = T
        self.R = R
        self.id = id
        if len(calidad)==0:
            self.calidad=0
        else:
            self.calidad=calidad[0]
        

    def __str__(self):
        st= 'Ruta al nodo j=%d \nRuta: %s \nCon tiempo: %g \nCosto redu: %g\nID: %d\nCol: %s\nCalidad: %g\n' %(self.j,self.S,self.T,self.R,self.id,self.col(),self.calidad)
        return st
    
    def quality(self):
        return self.calidad
    
    def costo(self):
        return self.R
    
    def tiempo(self):
        return self.T
    
    def visitados(self):
        return self.S
    
    def terminal(self):
        return self.j
    
    def largo(self):
        return len(self.S)
            
    def iden(self):
        return self.id
    
    def col(self):
        N=self.j-1
        clientes=N/2
        co=[0]*clientes
        for n in range(1,clientes+1):
            if n in self.S:
                co[n-1]=1
        return(co)
        
        
        
class Label:
    
    def __init__(self,n,t,l,c,V,O,p,*pickup):#pickup es argumento opcional
        self.n = n   #nodo de llegada
        self.t = t   #tiempo de llegada a n
        self.l = l   #carga
        self.c = c   #costo reducido
        self.V = V   #pickups visitados
        self.O = O   #pickups empezados pero no terminados
        self.p = p   #puntero al label anterior
        if len(pickup)==0:
            self.pickup=-1
        else:
            self.pickup=pickup[0]
        
    
    def __str__(self):
        st= '(%d,%d,%d,%d,%s,%s,%s)' %(self.n,self.t,self.l,self.c,self.V,self.O,self.pickup)
        return st
    
    def DOM1(delf, other):
        if self.n==other.n and self.t<=other.t and self.c<=other.c and set(self.V)<=set(other.V) and set(self.O)<=set(other.O):
            return True
        else:
            return False
    
    def ruta(self):
        ruta=[self.n]
        pointer=self.p
        while pointer!='source':
            ruta.append(pointer.node())
            pointer=pointer.p
        ruta.reverse()
        #print ruta  
        return Ruta(self.n,ruta,self.t,self.c,0)
        
    def node(self):
        return self.n
    
    def V(self):
        return self.V