import networkx as nx
import priorityq
import math

precision = 2

'''
Functions for FJ dynamics implementation
'''
def update_opinion(stubborness, belief, neighbors, opinions):
    avg = 0
    if len(neighbors) > 0:
        constant = 1/len(neighbors)

        for v in neighbors:
            avg += constant * opinions[v]

    opinion = stubborness*belief + (1 - stubborness)*avg

    return round(opinion, precision)


def FJ_initialization(G, S, beliefs, stubbornness, c):
    FJ_stubbornness = stubbornness.copy()
    FJ_beliefs = beliefs.copy()
    
    for node in G.nodes():
        if node in S:
            FJ_beliefs[node] = c
            stubbornness[node] = 1
        else:
            stubbornness[node] = 0.5

    return FJ_beliefs, stubbornness

def FJ_dynamics(beliefs, stubbornness, G):
    opinions = beliefs.copy()
    flag = False
    old_count = 0
    stall = 0

    while not flag:
        count = 0
        new_opinions = {}

        for u in G.nodes():
            new_opinions[u] = update_opinion(stubbornness[u], beliefs[u], list(G.neighbors(u)), opinions)
            if abs(new_opinions[u] - opinions[u]) >= 0.02:
                count += 1

        opinions = new_opinions.copy()

        if count <=2:
            flag = True
        elif count == old_count:
          stall += 1
          if stall >= 30:
            flag = True
        elif count != old_count:
          stall = 0
        old_count = count

    return opinions 

'''
Voting Function
'''
def voting(G, m, beliefs):
    votes = {}
    dict_of_voting={}
    
    for k in m.keys():
         votes[k] = 0

    for u in G.nodes():
        diff = math.inf
        for x in m.keys():
            if abs(beliefs[u] - m[x]) < diff:
                diff = abs(beliefs[u] - m[x])
                preferred_candidate = x

            elif abs(beliefs[u] - m[x]) == diff:
                if m[x] < m[preferred_candidate]:
                    preferred_candidate = x
        dict_of_voting[u]=preferred_candidate
        votes[preferred_candidate] = votes[preferred_candidate] + 1
    return votes,dict_of_voting

'''
Functions for calculating Shapley values
'''
def non_increasing_function(distance):
    return 1/(1+distance)

def shapley_threshold(G,k,beliefs,weight,c):
    pq = priorityq.PriorityQueue()
    ShapleyV = {}
    for v in G.nodes():
        ShapleyV[v] = min(1,k/(1+G.degree[v]))
        for u in G.neighbors(v):
            ShapleyV[v] += max(0, (G.degree[u]-k+1)/(G.degree[u]*(1+G.degree[u])))
        pq.add(v,-((ShapleyV[v]*weight)+(abs(beliefs[v]-c))))

    return pq


def shapley_threshold_centrality(graph, budget, candidate, m, beliefs):
    votes = {}
    dict_of_voting = {}
    weight= 0.2
    threshold=1
    
    ShapleyV_pq = shapley_threshold(graph,threshold,beliefs,weight,m[candidate])
    ShapleyV_pq_reserve = ShapleyV_pq
    votes, dict_of_voting = voting(graph,m,beliefs)
    

    seeds = []

    while budget > 0:
      if len(ShapleyV_pq.pq) > 0:
          v=ShapleyV_pq.pop()
          if dict_of_voting[v] != candidate:
            seeds.append(v)
            budget -= 1
      else:
        v=ShapleyV_pq_reserve.pop()
        if v not in seeds:
            seeds.append(v)
            budget -= 1

    return seeds


'''
Manipulation function, where:

G is the graph;
p is the candidates list
c is the chosen candidate
B is the budget
b is the beliefs list
'''
def manipulation(G, p, c, B, b):

    candidate_index = c
    budget = B
    candidates_dict = {index: p[index] for index in range(0, len(p))}
    beliefs = {str(index): b[index] for index in range(0, len(b))}

    pure_votes, _ = voting(G, candidates_dict, beliefs.copy())

    seeds = shapley_threshold_centrality(G, budget, candidate_index, candidates_dict, beliefs.copy())

    stubbornness = {}
    manipulated_b, manipulated_s = FJ_initialization(G, seeds, beliefs.copy(), stubbornness.copy(), candidates_dict[candidate_index])
    manipulated_opinions = FJ_dynamics(manipulated_b, manipulated_s, G)
    manipulated_votes, _ = voting(G, candidates_dict, manipulated_opinions)
    
    print("7,", pure_votes[candidate_index], ',', manipulated_votes[candidate_index])
