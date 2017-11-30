from genfigs.genfigs import *
# from ofspy.task import Task
# from ofspy.path import Path
import networkx as nx
import random
from collections import Counter
from scipy.optimize import minimize
# from matplotlib import pylab as plt
# import math
import numpy as np
import matplotlib.pyplot as plt
from gurobipy import Model, LinExpr, GRB, GurobiError
from itertools import product

def pickTask(task, time):
    element = task.element
    task.lastelement = element
    element.size += task.size
    task.init = time
    task.expiration = time + 5

def transTask(task, link, cost, epsilon):
    # link.source.size -= task.size
    # link.destin.size += task.size
    task.lastelement = link.destin
    task.element.owner.cash -= cost
    link.owner.cash += cost - epsilon

def resolveTask(task, value):
    task.element.owner.cash += value
    task.element.size -= task.size

class Federate():
    def __init__(self, name, cash, linkcost):
        self.name = name
        self.cash = cash
        self.linkcost = linkcost

class Link():
    def __init__(self, source, destin, capacity, size, owner):
        self.source = source
        self.destin = destin
        self.capacity = capacity
        self.size = size
        self.owner = owner

class Task():
    def __init__(self, id, element, lastelement, size, value, expiration, init, active, penalty):
        self.id = id
        self.element = element
        self.lastelement = lastelement
        self.size = size
        self.expiration =expiration
        self.init = init
        self.active = active
        self.penalty = penalty
        self.maxvalue = value

    def getValue(self, time):
        """
        Gets the current value of this contract.
        @return: L{float}
        """
        # print time, self.initTime
        duration = self.expiration - self.init + 1
        self.elapsedTime = time - self.init
        value = self.maxvalue if self.elapsedTime <= duration else self.penalty if self.elapsedTime > self.expiration \
            else self.maxvalue * (1. - self.elapsedTime) / (2. * self.expiration)
        return value


class Element():
    def __init__(self, name, capacity, size, owner):
        self.name = name
        self.capacity = capacity
        self.size = size
        self.owner = owner

def costfunction(f, l):
    f2 = l.destin.owner
    if f.name == f2.name:
        return 0
    else:
        return f2.linkcost

def optimizeMILP(elements, linklist, destinations, tasklist, time, federates):
    global storagepenalty, linkcost, epsilon, value, penalty, linkcapacity, elementcapacity

    print(time, [(task.id, task.element.name) for task in tasklist], [task.init for task in tasklist])
    print([(l.source.name, l.destin.name) for l in linklist])
    lp = Model('LP')
    steps =  10
    timesteps = range(time, time + steps)
    trans = [] # trans[t][i][l] transfer task i from link l at time t
    store = [] # store[i][j] store task i
    pick = []   # pick[i] if source i picks up the task
    resolve = []

    J = LinExpr()

    for i, task in enumerate(tasklist):
        store.insert(i, lp.addVar(vtype=GRB.BINARY))
        J.add(store[i], -1* storagepenalty)
        r = LinExpr()
        r.add(store[i], 1)
        lp.addConstr(r <= 1)
        # lp.addConstr(r == 0)

    for i, task in enumerate(tasklist):
        pick.append(lp.addVar(vtype=GRB.BINARY))
        J.add(pick[i], -1)
        element = task.element
        r = LinExpr()
        r.add(pick[i], 1)
        if task.init < time:
            lp.addConstr(r == 1)
        else:
            lp.addConstr(r <= 1)

    for i, t in enumerate(timesteps):
        trans.insert(i, [])
        resolve.insert(i, [])
        for k, task in enumerate(tasklist):
            # print(task.element.name, task.lastelement.name)
            trans[i].insert(k, [])
            resolve[i].insert(k, [])
            for j, e in enumerate(elements):
                resolve[i][k].insert(j, lp.addVar(vtype=GRB.BINARY))
                if e.name in destinations:
                    J.add(resolve[i][k][j], value)
                else:
                    J.add(resolve[i][k][j], penalty)

            if i == 0 and (task.expiration <= time):
                r = LinExpr()
                element = task.element
                j, e = next(((a, b) for a, b in enumerate(elements) if b.name == element.name))
                r.add(resolve[i][k][j], 1)
                lp.addConstr(r == 1)

            for l, link in enumerate(linklist):
                trans[i][k].insert(l, lp.addVar(vtype=GRB.BINARY))
                J.add(trans[i][k][l], -1*epsilon)

                r = LinExpr()
                r.add(trans[i][k][l], 1)
                lp.addConstr(r <= (1 if (task.size <= (link.capacity - link.size)
                                         and link.source.name not in destinations) else 0))

                r.add(pick[k], -1)
                lp.addConstr(r <= 0)

                r = LinExpr()
                r.add(sum(trans[i][k]))
                lp.addConstr(r <= 1)
                d = link.destin
                j, e = next(((a, b) for a, b in enumerate(elements) if b.name == d.name))
                # print(link.source.name, link.destin.name, d.name, j, e.name)
                r = LinExpr()
                r.add(resolve[i][k][j], 1)
                lp.addConstr(r <= (1 if (d.name in destinations) else 0))

    for i, t in enumerate(timesteps):
        for k, task in enumerate(tasklist):
            for j, element in enumerate(elements):
                inlinks = [(l, li) for l, li in enumerate(linklist) if li.destin.name == element.name]
                outlinks = [(l, li) for l, li in enumerate(linklist) if li.source.name == element.name]
                # print(i, k, element.name, [e[0] for e in inlinks], [e[0] for e in outlinks])
                if i == 0 and element.name == task.element.name:
                    # print("SOURCE:", i, element.name, [e[0] for e in inlinks], [e[0] for e in outlinks])
                    r = LinExpr()
                    for l, li in outlinks:
                        r.add(trans[i][k][l], -1)

                    r.add(resolve[i][k][j], -1)
                    r.add(store[k], -1)
                    r.add(pick[k], 1)
                    lp.addConstr(r == 0)
                elif element.name in destinations:
                    r = LinExpr()
                    # r2 = LinExpr()
                    for l, li in inlinks:
                        r.add(trans[i][k][l], 1)

                    r.add(resolve[i][k][j], -1)
                    lp.addConstr(r == 0)

                else:
                    r = LinExpr()
                    # r2 = LinExpr()
                    for l, li in inlinks:
                        r.add(trans[i][k][l], 1)

                    r.add(resolve[i][k][j], -1)
                    if i< len(timesteps) - 1:
                        for l, li in outlinks:
                            r.add(trans[i+1][k][l], -1)

                    lp.addConstr(r == 0)

    #
    for k, task in enumerate(tasklist):
        r = LinExpr()
        r.add(pick[k], -1)
        r.add(store[k], 1)
        for j, element in enumerate(elements):
            for i, t in enumerate(timesteps):
                r.add(resolve[i][k][j], 1)
        lp.addConstr(r == 0)


    for l, li in enumerate(linklist):
        r = LinExpr()
        for k in range(len(tasklist)):
            for i in range(len(timesteps)):
                r.add(trans[i][k][l])

        lp.addConstr(r <= linkcapacity)

    for j, e in enumerate(elements):
        r = LinExpr()
        for k, task in enumerate([t for t in tasklist if e.name == task.element.name]):
            r.add(pick[k], 1)
            for i in range(len(timesteps)):
                for v in range(len(elements)):
                    r.add(resolve[i][k][v], -1)

        lp.addConstr(r <=  elementcapacity)

    # for i in range(len(timesteps)):
    #     rl = [LinExpr() for e in elements]
    #     for k, task in enumerate(tasklist):
    #         element = task.element
    #         j, e = next(((a, b) for a, b in enumerate(elements) if b.name == element.name))
    #         rl[j].add(store[k], 1)
    #         rl[j].add(resolve[0][k][j], -1)
    #
    #     for r in rl:
    #         lp.addConstr(r <= elementcapacity)

    for k, task in enumerate(tasklist):
        r = LinExpr()
        fedtask = task.element.owner
        for i in range(len(timesteps)):
            for l, li in enumerate(linklist):
                r.add(trans[i][k][l], -1*(costfunction(fedtask, li)+epsilon))

        r.add(task.getValue(time), 1)
        lp.addConstr(r >= 0)


    lp.setObjective(J, GRB.MAXIMIZE)
    lp.setParam('OutputFlag', False)
    lp.optimize()

    # print("pick:", pick)
    # print("store:", store)
    # print("trans:", trans)
    # print("resolve:", resolve)

    # print("sum of trans:", [sum([sum([e.x for e in a]) for a in l]) for l in trans])

    for i, task in enumerate(newtasks):
        if pick[i].x>0.5:
            pickTask(task, time)

    edges = []

    for i, t in enumerate(timesteps):
        for k, task in enumerate(tasklist):
            for l, link in enumerate(linklist):
                if trans[i][k][l].x>0.5:
                    # print('trans is 1')
                    edges.append((link.source.name, link.destin.name))
                    print(i, task.id, task.element.name, (link.source.name,link.destin.name))
                    if task.element.owner == link.owner:
                        transTask(task, link, 0, epsilon)
                    else:
                        transTask(task, link, linkcost, epsilon)

            for j, e in enumerate(elements):
                if resolve[i][k][j].x>0.5:
                    print('time ', i, ' resolved task:', task.id, ' element ', j)
                    # if task.expiration <= time:
                    #     resolveTask(task, task.penalty)
                    # else:
                    #     resolveTask(task, task.value)
                    resolveTask(task, task.getValue(time))

    for k, task in enumerate(tasklist):
        net = 0
        fedtask = task.element.owner
        for i in range(len(timesteps)):
            for l, li in enumerate(linklist):
                net -= trans[i][k][l].x * (costfunction(fedtask, li) + epsilon)

        net += task.getValue(time)
        # print("task ", task.id, " net value ", net, " is stored:", store[k].x)



    storedtasks = []
    for k, task in enumerate(tasklist):
        # print([resolve[i][k][j].x for i, j in product(range(len(timesteps)), range(len(elements)))])
        if (pick[k].x and store[k].x) and not any([resolve[i][k][j].x for i, j in product(range(len(timesteps)), range(len(elements)))]):
            storedtasks.append(task)

    return storedtasks, edges

# def drawSampleNetwork():
#     global all_edges, satellites, stations, federate_cost_dict, taskids
#     plt.figure()
#     loc_dict = {e: loc for e, loc in zip(satellites + stations, [(-0.2-1, 2), (0.7-1,2), (1.5-0.8,2), (0.3-0.2,1), (1.1, 1),(0.5, 0), (1.5, 0)])}
#     sat_locs = [loc_dict[e] for e in satellites]
#     sta_locs = [loc_dict[e] for e in stations]
#
#     loc_element_dict = {loc: i+1 for i, loc in enumerate(sat_locs + sta_locs)}
#
#     all_edges_locs = [(loc_dict[e[0]], loc_dict[e[1]]) for e in all_edges]
#
#     for edge in all_edges_locs[:]:
#         if edge[1] not in sta_locs:
#             all_edges_locs.append((edge[1], edge[0]))
#     # textloc = zip(satellites[:3], ['$F_1, T_1, S1$', '$F_2, T_2, S2$', '$F_1, T_3, S3$']) +
#     textloc = [((sat_locs[0][0], sat_locs[0][1] + 0.2), '$F_1, e_1$'), ((sat_locs[1][0], sat_locs[1][1] + 0.2), '$F_2, e_2$'),
#                ((sat_locs[2][0], sat_locs[2][1] + 0.2), '$F_1, e_3$'), ((sta_locs[0][0], sta_locs[0][1] - 0.2), '$F1, e_6 (G)$'),
#                ((sta_locs[1][0], sta_locs[1][1] - 0.2), '$F2, e_7 (G)$') ,((sat_locs[3][0] - 0.2, sat_locs[3][1] - 0.1), '$F_2, e_4$'), ((sat_locs[4][0] + 0.2, sat_locs[4][1] - 0.1), '$F_1, e_5$')]
#
#     element_federate_dict = {s: v for s,v in zip(sat_locs+sta_locs, [1, 2, 1, 2, 1, 1, 2])}
#
#     plt.scatter(*zip(*sat_locs), marker='H', color='k', s=300, facecolors='w', linewidth='2')
#     plt.scatter(*zip(*sta_locs), marker='H', color='k', s=400, facecolors='w', linewidth='2')
#
#     edge_federate_dict = []
#     all_arrows = []
#     for edge in all_edges_locs:
#         # plt.plot(*zip(*edge), 'k:', linewidth = 0.7)
#         # if
#         e1e2 = (loc_element_dict[edge[0]], loc_element_dict[edge[1]])
#         legend = r'$l_{%d%d}$'%(e1e2[0], e1e2[1])
#         # print(label)
#         arr1 = plt.arrow(edge[0][0], edge[0][1], 0.9* (edge[1][0] - edge[0][0]), 0.9 * (edge[1][1] - edge[0][1]),
#                   head_width=0.03, head_length=0.05, linewidth=0.7, fc='k', ec='k', zorder=-1, linestyle = ':')
#         # arr2 plt.arrow(edge[1][0], edge[1][1], 0.9* (edge[0][0] - edge[1][0]), 0.9 * (edge[0][1] - edge[1][1]),
#         #           head_width=0.03, head_length=0.05, linewidth=0.7, fc='k', ec='k', zorder=-1, linestyle = ':')
#         x = (edge[0][0] + edge[1][0])/2.
#         y = (edge[0][1] + edge[1][1])/2.
#         nom , denom = ((edge[1][1] - edge[0][1]), (edge[1][0] - edge[0][0]))
#         r = 180/math.pi * np.arctan((edge[1][1] - edge[0][1])/(edge[1][0] - edge[0][0])) if (edge[1][0] - edge[0][0]) != 0 else 'vertical'
#         # print(edge, r)
#         all_arrows.append((arr1, legend))
#         if (nom>=0 and denom>0) or (nom<0 and denom>0):
#             x += 0.05
#             y += 0.05
#         elif (nom==0 and denom<0):
#             x -= 0.05
#             y -= 0.05
#         else:
#             x -= 0.05
#             y -= 0.05
#
#         plt.text(x, y, ha="center", va="center", s=legend, bbox=dict(fc="none", ec="none", lw=2), rotation = r)
#
#     for xy, text in textloc:
#         plt.text(*xy, ha="center", va="center", s=text, bbox=dict(fc="none", ec="none", lw=2))
#
#     plt.text(-0.3, 0.2, ha="left", va="center", s=r'$\zeta_{12}=%d$'%federate_cost_dict['F2'], bbox=dict(fc="none", ec="none", lw=2), rotation = 0)
#     plt.text(-0.3, 0.1, ha="left", va="center", s=r'$\zeta_{21}=%d$'%federate_cost_dict['F1'], bbox=dict(fc="none", ec="none", lw=2), rotation = 0)
#     plt.text(-0.3, 0.0, ha="left", va="center", s=r'$\zeta_{11}=  0$', bbox=dict(fc="none", ec="none", lw=2), rotation = 0)
#     plt.text(-0.3, -0.1, ha="left", va="center", s=r'$\zeta_{22}=  0$', bbox=dict(fc="none", ec="none", lw=2), rotation = 0)
#
#     font = FontProperties()
#     font.set_style('italic')
#     font.set_weight('bold')
#     font.set_size('small')
#
#     for i, (x, y) in enumerate([sat_locs[t-1] for t in taskids]):
#         plt.text(x, y, ha="center", va="center", s='$T_%s$'%str(i+1), bbox=dict(fc="none", ec="none", lw=2), fontproperties=font)
#     plt.xticks([])
#     plt.yticks([])
#     plt.axis('off')
#     plt.savefig('sample_network.pdf', bbox_inches='tight')


def plotDirectedNetworkx(elements, edge1, edge2, destinations = [], sources = [], selectedsources = None):
    global element_federate_dict
    G = nx.DiGraph()
    G.add_nodes_from(elements)
    G.add_edges_from(edge1)

    val_map = {'A': 1.0,
               'D': 0.5714285714285714,
               'H': 0.0}

    # othernodes = [val_map.get(node, 0.25) for node in G.nodes()]
    federates = []
    for f in set(element_federate_dict.values()):
        federates.append([e for e in elements if element_federate_dict[e] == f])

    othernodes = [e for e in elements if (e not in destinations and e not in sources)]
    destinationvalues = ['k' for node in destinations]
    sourcevalues = ['g' for node in sources]
    othervalues = ['r' for node in othernodes]
    # Specify the edges you want here
    red_edges = edge2
    edge_colours = ['black' if not edge in red_edges else 'red'
                    for edge in G.edges()]
    black_edges = [edge for edge in G.edges() if edge not in red_edges]

    # Need to create a layout when doing
    # separate calls to draw nodes and edges
    shapes = ['H', 's', 'o']
    colors = ['lightgreen', 'gold']
    node_shape_dict = {}
    node_color_dict = {}
    for e in elements:
        if e in federates[0]:
            node_color_dict[e] = colors[0]
        else:
            node_color_dict[e] = colors[1]

    for e in elements:
        if e in sources:
            node_shape_dict[e] = shapes[0]
        if e in destinations:
            node_shape_dict[e] = shapes[1]
        else:
            node_shape_dict[e] = shapes[2]

    pos = nx.circular_layout(G)
    for e in elements:
        node = nx.draw_networkx_nodes(G, pos, nodelist=[e], cmap=plt.get_cmap('jet'),
                               node_color=node_color_dict[e], node_size=800, node_shape=node_shape_dict[e], linewidths = 2)
        if e in sources:
            node.set_edgecolor('k')
    # for shape, fed in zip(shapes, federates):
    #     nx.draw_networkx_nodes(G, pos, nodelist=[e for e in destinations if e in fed], cmap=plt.get_cmap('jet'),
    #                            node_color=node_color_dict[e], node_size=800, node_shape=shape)
    #     nx.draw_networkx_nodes(G, pos, nodelist=[e for e in sources if e in fed], cmap=plt.get_cmap('jet'),
    #                            node_color=node_color_dict[e], node_size=800,node_shape=shape)
    #     nx.draw_networkx_nodes(G, pos, nodelist=[e for e in othernodes if e in fed],cmap=plt.get_cmap('jet'),
    #                            node_color=node_color_dict[e], node_size=800, node_shape=shape)
    nx.draw_networkx_labels(G, pos)
    nx.draw_networkx_edges(G, pos, edgelist=red_edges, edge_color='k', arrows=True, width = 2)
    nx.draw_networkx_edges(G, pos, style='dotted' ,edgelist=black_edges, arrows=False)
    plt.axis('off')
    # plt.savefig('sample_%d_%d.jpg'%(len(sources), len(edge1)), bbox_inches='tight')
    # plt.show()




if __name__ == '__main__':
    time = 0
    federatenames = ['F1', 'F2']
    elementnames = ['e1', 'e2', 'e3', 'e4', 'e5', 'e6', 'e7', 'e8', 'e9', 'e10']
    stations = elementnames[-2:]
    satellites = [e for e in elementnames if e not in stations]
    linkcapacity = 2
    elementcapacity = 2

    seed = 0
    random.seed(seed)

    element_federate_dict = {e: federatenames[0] if random.random()>0.5 else federatenames[1] for e in elementnames}
    # element_federate_dict = {'e1':federatenames[0], 'e2':federatenames[1], 'e3':federatenames[0], 'e4':federatenames[1], 'e5': federatenames[0], 'e6':federatenames[0], 'e7':federatenames[1]}

    # all_edges = [(satellites[0],satellites[1]), (satellites[3],stations[0]), (satellites[1],satellites[3]),
    #              (satellites[2],satellites[4]), (satellites[2],satellites[1]), (satellites[2],satellites[3]), (satellites[3],satellites[4]), (satellites[4],stations[1]), (satellites[2],stations[0])]
    # all_possible_edges = [(a,b) for a, b in list(product(elementnames, elementnames)) if (a != b and element_federate_dict[a] != element_federate_dict[b])]
    all_possible_edges = [(a,b) for a, b in list(product(elementnames, elementnames)) if (a != b and not (a in stations and b in stations))]
    all_edges = random.sample(all_possible_edges, int(len(all_possible_edges)//8))
    all_edge_set = set([])
    destin_count = 0

    for edge in all_edges:
        s, d = edge
        # if destin_count > len(satellites):
        #     continue
        if s in stations or d in stations:
            destin_count += linkcapacity
        all_edge_set.add((s,d))
        all_edge_set.add((d,s))

    all_edges = list(all_edge_set)

    id = 1
    SP = 100
    epsilon = 10
    linkcost = 1001
    storagepenalty = 100
    value = 1000
    penalty = -200
    size = 1


    for linkcost in [0, 400, 600, 1001]:
        federatenames = [element_federate_dict[e] for e in elementnames]
        federates = [Federate(name = f, cash = 0, linkcost = linkcost) for f in set(federatenames)]
        federateDict = {f.name: f for f in federates}
        elements = [Element(name = e, capacity=elementcapacity, size = 0, owner = federateDict[f]) for (e,f) in zip(elementnames, federatenames)]
        elementDict = {e.name: e for e in elements}
        sources = [e for e in elements if e.name not in stations]
        print([s.name for s in sources])
        linklist = [Link(source = elementDict[e1], destin = elementDict[e2], capacity = linkcapacity, size = 0, owner = elementDict[e2].owner) for (e1, e2) in all_edges]
        # print('sources:', [s.name for s in sources])
        # newtasks = [Task(id = n + id, element = s, lastelement = s, size = size, value = value, expiration=time + 3, init = time, active = True, penalty = penalty) for n, s in enumerate(sources)]
        id += len(sources)
        storedtasks = []

        for time in range(1):
            newtasks = [Task(id = id + n, element=s, lastelement=s, size=size, value=value, expiration=time + 5, init=time, active=True, penalty=penalty) for n, s in enumerate(sources)]
            id += len(sources)
            tasklist = storedtasks + newtasks
            for link in linklist:
                link.size = 0

            for e in elements:
                e.size = 0

            storedtasks, edges2 = optimizeMILP(elements = elements, linklist = linklist, destinations = elementnames[-2:], tasklist = tasklist, time = time, federates = federates)
            # print([(task.id, task.element.name) for task in storedtasks])
            print([f.cash for f in federates])

            plotDirectedNetworkx(elementnames, edge1=all_edges, edge2=edges2, destinations=elementnames[-2:], sources = [s.name for s in sources])
            plt.savefig('sample_%d_%d_cash_%d_%d_cost_%d_seed_%d.jpg' % (len(sources), len(all_edges),federates[0].cash, federates[1].cash, linkcost, seed), bbox_inches='tight')
            plt.close()