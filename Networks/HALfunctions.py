def get_all_elements(request_core,page_size=1000):
    df_complet=pd.DataFrame()
    
    #en faisant la requête en json, on peut obtenir le nombre de réponses à récupérer
    nb_reponses=requests.get(request_core).json()["response"]["numFound"]
    print("Nombre d'éléments au total : ",nb_reponses)

    #Cette boucle incrémente le curseur de début, par pas de 1000, jusqu'à atteindre le dernier élément
    for i in range(0,nb_reponses,page_size):
        #On récupére le résultat, en rajoutant des options à la requete de base
        response =requests.get(requete+"&wt=csv&sort=docid asc&start="+str(i)+"&rows="+str(page_size))
        df_temp =pd.read_csv(io.StringIO(response.text),sep=",")

        #On ajoute les réponses les plus récentes à celles que l'on a déjà
        df_complet=df_complet.append(df_temp,ignore_index=True)
        print("Éléments récupérés : ",len(df_complet))
    
    return df_complet #la fonction renvoie le tableau complet

def co_occurence_network(request,column,threshold=1):
    collab_list=[]
    node_list=[] #To make the network more insteresting, we also collect the number of articles by author:




    for collab in list(request[column]): #pour tous les articles
        nodes=str(collab).replace("\\,","_").split(",") #on crée une liste des noms d'auteurs
        nodes=set(nodes)
        if len(nodes)<=5: #s'il y a entre 2 et 5 elements (pour éviter une explostion de liens)
            
            for node in nodes:#remember we have seen that node
                node_list.append(node)
                
            for node1,node2 in combinations(nodes,2): #pour chaque paire d'auteurs possible dans la liste
                collab_list.append(frozenset((node1,node2))) #on ajoute une collaboration. 
                #noter l'usage du set (frozenset), qui dit qu'il n'y a pas d'ordre entre les éléments: 
                #set((lab1,lab2))==set((lab2,lab1)) alors que [aut1,aut2]!=[aut2,aut1]
    
    #We count how many times each node appears:
    nodes=[]
    occurences=node_list
    for n,occ in dict(collections.Counter(occurences)).items(): #collections.Counter count occurences by item
        if occ>threshold: #we filter out singleton to keep important actors
            nodes.append((n,{"occurences":occ})) #we store the result in a format convenient for networkx
    
    #We count how many times each link appears:
    edges=[]
    occurences=collab_list
    for n,occ in dict(collections.Counter(occurences)).items(): #collections.Counter count occurences by item
        if occ>threshold: #we filter out singleton to keep important relations
            n1,n2=n
            edges.append((n1,n2,{"occurences":occ})) #we store the result in a format convenient for networkx
            
    #En utilisant networkx, nous créons un objet graphe
    g = nx.Graph()
    g.add_nodes_from(nodes)
    g.add_edges_from(edges)
    return g


def co_occurence_network_laboratory(request,column,threshold=1):
    collab_list=[]
    node_list=[]
    
    struct_names=list(request[column])
    struct_types=list(request["structType_s"]) # We also get types of structures
    struct_countries=list(request["structCountry_s"]) #and countries
    
    for i,collab in enumerate(struct_names):
        nodes_unfiltered=str(collab).replace("\\,","_").split(",") 
        
        #We split them the same way
        types=str(struct_types[i]).replace("\\,","_").split(",") 
        countries=str(struct_countries[i]).replace("\\,","_").split(",") 
        
        #We filter the structure (nodes) to keep only french laboratories
        nodes=set()
        try:
            for j,name in enumerate(nodes_unfiltered):
                if types[j]=="laboratory" and countries[j]=="fr":
                    nodes.add(name)
        except:#if there is a problem
            pass # ignore this item
        
        if len(nodes)>1:
            for node in nodes:
                node_list.append(node)

            if len(nodes)<=10: 
                for node1,node2 in combinations(nodes,2): 
                    collab_list.append(frozenset((node1,node2))) 

    nodes=[]
    occurences=node_list
    for n,occ in dict(collections.Counter(occurences)).items(): 
        if occ>threshold: 
            nodes.append((n,{"occurences":occ})) 
    
    edges=[]
    occurences=collab_list
    for n,occ in dict(collections.Counter(occurences)).items(): 
        if occ>threshold:
            n1,n2=n
            edges.append((n1,n2,{"occurences":occ}))
            
    g = nx.Graph()
    g.add_nodes_from(nodes)
    g.add_edges_from(edges)
    return g

def bi_partite_network(request,article_column,other_column,threshold=1,article_attributes=[],other_attributes=[]):
    authorship=[]
    node_list=[] 
    article_attributes+=[article_column]


    for index,row in request.iterrows(): #pour tous les articles
        #print(row)
        nodes=row[other_column].replace("\\,","_").split(",") #on crée une liste des noms d'auteurs
        article_id=index
        if len(nodes)<=5: #s'il y a entre 2 et 5 elements (pour éviter une explostion de liens)
            
            for i,node in enumerate(nodes):#pour chaque auteur
                authorship.append((node,index))
                #node_list.append(node)
                
                attributes = {at:row["at"][i] for at in other_attributes}
                attributes["type"]="other"
                node_list.append((node,attributes))
        
        attributes = {at:row[at] for at in article_attributes}
        attributes["type"]="article"
        node_list.append((index,attributes))
    #En utilisant networkx, nous créons un objet graphe
    g = nx.Graph()
    g.add_nodes_from(node_list)
    g.add_edges_from(authorship)
    return g


def column_most_common(df,previous_name,new_name):
    def most_common(l):
        count = collections.Counter(l)
        most = count.most_common(1)[0][0]
        return most
    df[new_name]=df.apply(lambda row: most_common(str(row[previous_name]).split(",")), axis=1)