
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
neighbours_list=dict()
thelist=[]
known_nodes_link_dict=dict() # to keep track of nodes known by the router.
transfer_limit=defaultdict(int) # to keep track of the number of times packets are transfered
rq=Queue() # queue to recieve packets
sq=Queue()  #queue to broadcast packets
tq=Queue()  # queue to transfer recieved packets
hbq=Queue()  # queue to recieve heartbeats
emq=Queue()   # queue to send error messages
emqr=Queue()  #queue to recieve error messages

heartbeatlist=dict()
heartbeatcount=defaultdict()

lock=threading.Lock()

def readfile(filename):  #funtion to reading the text file and create a dictionary out of it
    filepath = pathlib.Path(filename)
    with open(filepath) as f:
        filelinebyline = f.readlines()
    #n_nodes = dict()
    for line in filelinebyline:
        temp=line.split()
        if(len(temp)==3):
            n_nodes[temp[0]]=(float(temp[1]),int(temp[2]))
            neighbours_list[temp[0]]=int(temp[2])
        if(len(temp)==2):
            n_nodes["router"]=(temp[0]) 
            n_nodes["port"]=int(temp[1])  
            n_nodes["transporter"]=(temp[0])
            n_nodes["type"]=0
            n_nodes["TTL"]=0
        if(len(temp)==1):
            n_nodes["no_of_neighbours"]=int(temp[0])

    

# return n_nodes


def displaydict():
    for x in n_nodes:
        print(x,n_nodes[x])

readfile(sys.argv[1])




for x in neighbours_list:
    heartbeatcount[x]=-1
    



known_nodes_link.append((n_nodes["port"],n_nodes["router"]))


def broadcasting_thread():  #thread to broadcast packets
    
    while True:
        for i in n_nodes:
            if len(i)==1:
                adress=(socket.gethostname(),n_nodes[i][1])
                sq.put((n_nodes,adress,n_nodes[i][1]))
        time.sleep(1)

def create_dictionary(): #thread to create a dictionary for routers
    for x in known_nodes_link:
        known_nodes_link_dict[x[0]]=x[1]




def check_alive(): #thread to check if a node is killed.
    while True:
        #flag=0
        if (hbq.empty()==0):
            x=hbq.get()
            #print("heart beat of" ,x, "recieved")
            
            #if heartbeatlist[x]==0:
            #heartbeatlist[x]=time.time();
            heartbeatcount[x]=0
            #flag=1
            
            
            #print("heartbeatcount",heartbeatcount)

            for r in heartbeatcount:
                if heartbeatcount[r]!=-1:
                    if r!=x:
                        heartbeatcount[r]+=1
                if heartbeatcount[r]!=-1:
                    if r==x:
                        heartbeatcount[r]=0
                        

        for n in heartbeatcount:
            if heartbeatcount[n]!=-1:
            
                if (heartbeatcount[n]>(n_nodes["no_of_neighbours"]*3)):
                    #print("hertbeatcount[n]:",heartbeatcount[n])
                    transfer_limit[n_nodes[n][1]]=0
                
                    heartbeatcount[n]=-1
                    if (neighbours_list[n],n) in known_nodes_link:
                        known_nodes_link.remove((neighbours_list[n],n))
                    #print("updated known_nodes_link")
                    #print("known_nodes_link:",known_nodes_link)

                    error_msg={"type":1,"router":n,"transporter":n_nodes["router"],"port":neighbours_list[n],"TTL":0}
                    for x in n_nodes:
                        if len(x) == 1:
                            if x!=n:
                                adress=(socket.gethostname(),n_nodes[x][1])
                                #print("sending error message packet of ",n ,"to" , x)
                                emq.put((error_msg,adress,x))
                    
                    
                
            
            
        
    
    


def listening_thread(): # thread to recieve packets
    sock=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    adress=(socket.gethostname(),int(n_nodes["port"]))
    sock.bind(adress)
    
    
    
    
    while True:
        
        data,addr=sock.recvfrom(2048)
        diction=pickle.loads(data)

        if diction["type"]==0:
            rq.put(diction)
        else:
            emqr.put(diction)
        #print("recieved packet of" ,diction["router"],"from",diction["transporter"])
        
        
        

def sending_thread(): # thread to send packets from queues to their destinations
    sock2=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    while True:
        if(sq.empty()==0):
            msg,adress,to=sq.get()
            #if msg["type"]==1:
                #print("sending error msg of",msg["router"],"to", to)
            #else:
                #print("broadcasting packet of ",msg["router"], "to port",to)
            data=pickle.dumps(msg)
            
            sock2.sendto(data,adress)

        if(tq.empty()==0):
            msg,adress,to=tq.get()
            data=pickle.dumps(msg)
            #print("transfering packet of ",msg["router"], "to port",to)
            sock2.sendto(data,adress)

        if(emq.empty()==0):
            msg,adress,to=emq.get()
            data=pickle.dumps(msg)
            #print("sending error packet of",msg["router"],"to port", to)
            sock2.sendto(data,adress)
            
            
            
            
            




def transferring_thread(): # thread to transfer recieved packets
    
    
    while True:
        if(emqr.empty()==0):
            diction=emqr.get()
            diction["TTL"]=diction["TTL"]+1

            if diction["type"]==1:
                #print("error msg of ",diction["router"], "recieved from",diction["transporter"])
                if (diction["port"],diction["router"]) in known_nodes_link:
                    known_nodes_link.remove((diction["port"],diction["router"]))
                    #print("updated known_list:",known_nodes_link)
                for x in n_nodes:
                    if len(x)==1:
                      if (x!=diction["transporter"]):
                          if(x!=diction["router"]):
                              if diction["TTL"]<10:
                                  #print("TTL value:",diction["TTL"])
                                  diction["transporter"]=n_nodes["router"]
                                  transfer_limit[int(n_nodes[x][1])]=0
                                  adress=(socket.gethostname(),n_nodes[x][1])
                                  emq.put((diction,adress,x))
                          


    
                      
                        
                        
                        

        if(rq.empty()==0):
            diction=rq.get()
            diction["TTL"]=diction["TTL"]+1
            
            if diction["transporter"]==diction["router"]:
                hbq.put(diction["router"])

            if (diction["port"],diction["router"]) not in known_nodes_link:
                known_nodes_link.append((diction["port"],diction["router"]))
                thelist.append(diction)
                #print("known_nodes_link:",known_nodes_link)
                
            for x in n_nodes:
                if (len(x)==1):
                    if (int(diction["port"]) != int(n_nodes[x][1])):
                        if diction["router"]  in n_nodes:
                            if diction["transporter"]!=x:
                                if (transfer_limit[int(n_nodes[x][1])]<30):
                                #if diction["TTL"]<15:
                                    diction["transporter"]=n_nodes["router"]
                                    transfer_limit[int(n_nodes[x][1])]+=1
                                    #print("transfer_limit",transfer_limit)
                                    add=(socket.gethostname(),int(n_nodes[x][1]))
                                    tq.put((diction,add,x))
                                    #print("put in transfer queue")
                        else:
                            if diction["transporter"]!=x:
                                if (transfer_limit[int(n_nodes[x][1])]<60):
                                #if diction["TTL"]<15:
                                    diction["transporter"]=n_nodes["router"]
                                    transfer_limit[int(n_nodes[x][1])]+=1
                                    #print("transfer_limit",transfer_limit)
                                    add=(socket.gethostname(),int(n_nodes[x][1]))
                                    tq.put((diction,add,x))
                                    #print("put in transfer queue/rare")
                                    




   
class Graph:
    def __init__(self):
        # dictionary containing keys that map to the corresponding vertex object
        self.vertices = {}
        
    def add_vertex(self, key):
        """Add a vertex with the given key to the graph."""
        vertex = Vertex(key)
        self.vertices[key] = vertex

    def get_vertex(self, key):
        return self.vertices[key]
    """Return vertex object with the corresponding key."""
    def show_vertices(self):
        for x in self.vertices:
            print(self.vertices[x].key)

    def show_graph(self):
        for x in self.vertices:
            self.vertices[x].show_neighbours()
            
        
    def __contains__(self, key):
        return key in self.vertices
        
    def add_edge(self, src_key, dest_key, weight=1):
        self.vertices[src_key].add_neighbour(self.vertices[dest_key],weight)
        self.vertices[dest_key].add_neighbour(self.vertices[src_key],weight)
        #"""Add edge from src_key to dest_key with given weight."""

    def does_edge_exist(self, src_key, dest_key):
        if self.vertices[src_key].is_neighbour(self.vertices[dest_key]):
            return 1
        else:
            return 0
        """Return True if there is an edge from src_key to dest_key."""
        
    def __iter__(self):
        return iter(self.vertices.values())
    
    
class Vertex:
    def __init__(self, key):
        self.key = key
        self.points_to = {}
        
    def get_key(self):
        return self.key
     #"""Returns key corresponding to this vertex object."""
        
    def add_neighbour(self, dest, weight):
        self.points_to[dest] = weight
         #"""Make this vertex point to dest with given edge weight."""

    def show_neighbours(self):
        print(self.key,"connected to ")
        for x in self.points_to:
            print(x.key,self.points_to[x])
              
        
    def get_neighbours(self):
        x=self.points_to.keys()
        return x
    #"""Return all vertices pointed to by this vertex."""
        
    def get_weight(self, dest):
        if dest in self.points_to:
            x=self.points_to[dest]
            return x
        else:
            print("there is no weight to the given edge")

       # """Get weight of edge from this vertex to dest."""

    def is_neighbour(self, dest):  # is_neighbour for does_it_point_to
        #"""Return True if this vertex points to dest."""
        if dest in self.points_to:
            return 1
        else:
            return 0
    
    
def dijkstra(g, source): #function to calculate dijkstras
      
    distance=dict()
    visited =set()
    visited.add(source)
    final=set()

    for x in g.vertices:
        final.add(g.get_vertex(x))
        
    
    distance[source.get_key()]=(source.get_key(),0)
    near=source.get_neighbours()
    
    for x in g.vertices:
        if g.get_vertex(x) in near:
            distance[x]=(source.get_key(),source.get_weight(g.get_vertex(x)))
    
        else:
            distance[x]=(None,100000000000000)

    closest=source
    
    while visited!=final:
        temp=[]
        temp2=[]
        
        for x in final:
            if x not in visited:
                f=x.get_key()
                temp.append((distance[f][1],x))
                temp2.append(distance[f][1])
        
        d=min(temp2)
        for x in temp:
            if x[0]==d:
                closest=x[1]
        
    
        
        visited.add(closest)

        for x in closest.get_neighbours():
            #print("neighbours_of_closest:",x,x.get_key())
            if x not in visited:
                if d+closest.get_weight(x)<distance[x.get_key()][1]:
                    distance[x.get_key()]=(closest.get_key(),d+closest.get_weight(x))
        #print("dictionary_distance:",distance)
        
    cost_dict=dict()
    path_dict=dict()

    for x in distance:
        if x !=n_nodes["port"]:
            path=known_nodes_link_dict[x]
            node=x
            while(node!=n_nodes["port"]):
                path=path+known_nodes_link_dict[distance[node][0]]
                node=distance[node][0]

            path_dict[x]=path[::-1]

    for x in distance:
        if x!=n_nodes["port"]:
            cost_dict[x]=distance[x][1]

    

    print("I am Router ",n_nodes["router"])
    for x in distance:
        if x !=n_nodes["port"]:
            print("Least cost path to router",known_nodes_link_dict[x],":",path_dict[x],"and the cost is",cost_dict[x]) 
        

def dijkstra_thread(): # tread to calculate dijsktras
    while True:
        time.sleep(30)
        g=Graph()
        create_dictionary()
        # g.add_vertex(n_nodes[port])
        
        with lock:
            for x in known_nodes_link:
                #print("adding", x," to graph")
                g.add_vertex(x[0])
            for x in thelist:
                if (x["port"],x["router"]) in known_nodes_link:
                    for w in x:
                        if (len(w)==1 and( (x[w][1],w) in known_nodes_link)):
                            if g.does_edge_exist((x["port"]),(x[w][1]))==0:
                                g.add_edge((x["port"]), (x[w][1]), (x[w][0]))
                                #print("adding edge:",x["port"],x[w][1])

            source=g.get_vertex(n_nodes["port"])
            dijkstra(g,source)

        
        








a=threading.Thread(target=broadcasting_thread)
b=threading.Thread(target=transferring_thread)
c=threading.Thread(target=listening_thread)
d=threading.Thread(target=sending_thread)
e=threading.Thread(target=dijkstra_thread)
f=threading.Thread(target=check_alive)
a.start()
b.start()
c.start()
d.start()
e.start()
time.sleep(20)
f.start()



