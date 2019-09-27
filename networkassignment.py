import time
import sys
import pathlib
import socket
import pickle
import threading
from collections import defaultdict
from queue import Queue
known_nodes_link=[]
n_nodes=dict()
neighbours=[]
thelist=[]
known_nodes_link_dict=dict()
transfer_limit=defaultdict(int)
q=Queue()
#lock=threading.Lock()
def readfile(filename):
    filepath = pathlib.Path(filename)
    with open(filepath) as f:
        filelinebyline = f.readlines()
    #n_nodes = dict()
    for line in filelinebyline:
        temp=line.split()
        if(len(temp)==3):
            n_nodes[temp[0]]=(float(temp[1]),int(temp[2]))
            neighbours.append(temp[0])
        if(len(temp)==2):
           n_nodes["router"]=(temp[0]) #key is router 
           n_nodes["port"]=int(temp[1])  #key is port
        if(len(temp)==1):
            n_nodes["no_of_neighbours"]=int(temp[0])#key is no_of_neighbours

   # return n_nodes

def displaydict():
    for x in n_nodes:
        print(x,n_nodes[x])

readfile(sys.argv[1])
displaydict()


known_nodes_link.append((n_nodes["port"],n_nodes["router"]))


def broadcasting_thread():
    sock2=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    
    msg=pickle.dumps(n_nodes)
    
    while True:
        for i in n_nodes:
            if len(i)==1:
                adress=(socket.gethostname(),n_nodes[i][1])
                print("sending to :", adress)
                sock2.sendto(msg,adress)
        time.sleep(1)

def create_dictionary():
    for x in known_nodes_link:
        known_nodes_link_dict[x[0]]=x[1]

        
        
    



def listening_thread():
    sock=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    adress=(socket.gethostname(),int(n_nodes["port"]))
    sock.bind(adress)
    #q=Queue()

    
    #adress=(socket.gethostname(),int(n_nodes["port"]))
    while True:

        data,addr=sock.recvfrom(2048)
        diction=pickle.loads(data)
        #print("dictionary:",diction)
        #print("from port address:",addr[1])
        q.put(diction)
        print("recieved packet of" ,diction["router"])

        #sock2=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        #adress=(socket.gethostname(),n_nodes["port"])
        #diction2=q.get()
        if (diction["port"],diction["router"]) not in known_nodes_link:
            known_nodes_link.append((diction["port"],diction["router"]))
            thelist.append(diction)
            print("known_nodes_link:",known_nodes_link)
            
        
                        


def transfering():
    sock3=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    while True:
        print("queue:",q)
        if q.empty()!=0:
            diction2=q.get()
            for x in n_nodes:
                if (len(x)==1):
                    if (int(diction2["port"]) != int(n_nodes[x][1])):
                        if (transfer_limit[int(n_nodes[x][1])]<50):
                            transfer_limit[int(n_nodes[x][1])]+=1
                            print("transfer_limit",transfer_limit)
                            add=(socket.gethostname(),int(n_nodes[x][1]))
                            data=pickle.dumps(diction2)

                            print("transfering packet of ",diction2["router"],"to ",x)
                            sock3.sendto(data,add)
        

def dijkstra_compute():
    class Graph:
        def __init__(self):
            # dictionary containing keys that map to the corresponding vertex object
            self.vertices = {}
 
        def add_vertex(self, key):
            """Add a vertex with the given key to the graph."""
            vertex = Vertex(key)
            self.vertices[key] = vertex
     
        def get_vertex(self, key):
            """Return vertex object with the corresponding key."""
            return self.vertices[key]
 
        def __contains__(self, key):
            return key in self.vertices
 
        def add_edge(self, src_key, dest_key, weight=1):
            """Add edge from src_key to dest_key with given weight."""
            self.vertices[src_key].add_neighbour(self.vertices[dest_key], weight)
 
        def does_edge_exist(self, src_key, dest_key):
            """Return True if there is an edge from src_key to dest_key."""
            return self.vertices[src_key].does_it_point_to(self.vertices[dest_key])
 
        def __iter__(self):
            return iter(self.vertices.values())
 
 
    class Vertex:
        def __init__(self, key):
            self.key = key
            self.points_to = {}
 
        def get_key(self):
            """Return key corresponding to this vertex object."""
            return self.key
 
        def add_neighbour(self, dest, weight):
            """Make this vertex point to dest with given edge weight."""
            self.points_to[dest] = weight
 
        def get_neighbours(self):
            """Return all vertices pointed to by this vertex."""
            return self.points_to.keys()
 
        def get_weight(self, dest):
            """Get weight of edge from this vertex to dest."""
            return self.points_to[dest]
 
        def does_it_point_to(self, dest):
            """Return True if this vertex points to dest."""
            return dest in self.points_to
 
 
    def dijkstra(g, source):
        """Return distance where distance[v] is min distance from source to v.
 
        This will return a dictionary distance.
 
        g is a Graph object.
        source is a Vertex object in g.
        """
        unvisited = set(g)
        distance = dict.fromkeys(g, float('inf'))
        distance[source] = 0
 
        while unvisited != set():
            # find vertex with minimum distance
            closest = min(unvisited, key=lambda v: distance[v])
 
            # mark as visited
            unvisited.remove(closest)
 
            # update distances
            for neighbour in closest.get_neighbours():
               if neighbour in unvisited:
                   new_distance = distance[closest] + closest.get_weight(neighbour)
                   if distance[neighbour] > new_distance:
                       distance[neighbour] = new_distance

        return distance




    g=graph()
    g.add_vertex(n_nodes[port])
    for x in known_nodes_link:
        g.add_vertex(x[0])
    for x in thelist:
        if (x["port"],x["router"]) in known_nodes_link:
            for w in x:
                if len(w)==1 and( (x[w][1],w) in known_nodes_link):
                    if( g.does_edge_exist(x["port"],x[w][1])==0 and g.does_edge_exist(x["port"],x[w][1])==0):
                        g.add_edge(x["port"], x[w][1], x[w][0])
                    
        
        
    
    
    
th1=threading.Thread(target=broadcasting_thread)
th2=threading.Thread(target=transfering)   
th=threading.Thread(target=listening_thread)
th1.start()
th.start()
th2.start()

        
                    

#listening_thread()
#t1 = threading.Thread(target=listening_thread)
#t2 = threading.Thread(target=broadcasting_thread)
#t1.start()
#t2.start()
