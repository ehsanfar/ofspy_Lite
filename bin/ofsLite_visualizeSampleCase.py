from genfigs.genfigs import *
# from ofspy.task import Task
# from ofspy.path import Path
import networkx as nx
import random
from collections import Counter
from scipy.optimize import minimize
# from matplotlib import pylab as plt
# import math
# import numpy as np
from gurobipy import Model, LinExpr, GRB, GurobiError
from collections import namedtuple


def bfs_paths(G, source, destination):
    q = [(source, [source])]
    while q:
        v, path = q.pop(0)
        for next in set(G.neighbors(v)) - set(path):
            if next == destination:
                yield path + [next]
            else:
                q.append((next, path + [next]))


def findAllPaths(G, source, destinations):
    allpathes = []
    for d in destinations:
        allpathes.extend(bfs_paths(G, source, d))

    return allpathes

def addPaths(G, sources, destinations):
    nodes = G.nodes()
    orderPathDict = {}
    for s in sources:
        # print("source:", s)
        nodelist = findAllPaths(G, s, destinations)
        # print("nodelist:", nodelist)
        # print("order:", int(s[-1]))
        orderPathDict[s] = nodelist

    return orderPathDict

def convertPath2Edge(nodelist):
    tuplist = []
    for i in range(len(nodelist) - 1):
        tuplist.append((nodelist[i], nodelist[i + 1]))

    return tuplist

def returnPathCost(nodelist):
    global federate_cost_dict, element_federate_dict
    federate = element_federate_dict[nodelist[0]]
    edgelist = convertPath2Edge(nodelist)
    costlist = []
    for edge in edgelist:
        federate2 = element_federate_dict[edge[1]]
        if federate2 == federate:
            costlist.append(0)
        else:
            costlist.append(federate_cost_dict[federate2])

    return costlist

def returnBestBundle():
    global orderPathDict, taskrevenue, sources, maxlink
    orderCostDict = {}
    avgCostDict = defaultdict(float)
    avgRevenueDict = defaultdict(float)
    avgLength = defaultdict(float)

    for e, allnl in orderPathDict.items():
        costlist = [sum(returnPathCost(nl)) for nl in allnl]
        print(costlist)
        orderCostDict[e] = costlist
        avgCostDict[e] = sum(costlist) / float(len(costlist))
        avgLength[e] = sum([len(a) for a in allnl])/float(len(allnl))
        avgRevenueDict[e] = taskrevenue[e] - avgCostDict[e]

    print(avgCostDict)
    # print(avgLength)

    sortedtasks = sorted([(avgRevenueDict[e], e) for e in sources], reverse = True)
    edge_counter = defaultdict(int)
    orderedtasks = [e[1] for e in sortedtasks]

    pathbundle = []
    for e in orderedtasks:
        allnodelist = orderPathDict[e]
        allcostlist = orderCostDict[e]
        feasiblecostnodelist = []
        for nl, cl in zip(allnodelist, allcostlist):
            edgelist = convertPath2Edge(nl)
            if all([edge_counter[e]<maxlink for e in edgelist]):
                if taskrevenue[e] - cl > 0:
                    feasiblecostnodelist.append((cl, nl))

        # print(e, feasiblecostnodelist)
        if feasiblecostnodelist:
            sortedcostnodelist = sorted(feasiblecostnodelist, key = lambda x: (x[0], len(x[1])))
            mincost = sortedcostnodelist[0][0]
            minlen = len(sortedcostnodelist[0][1])
            selectedpath = random.choice([tup for tup in sortedcostnodelist if tup[0] == mincost and len(tup[1]) == minlen])[1]
            print("element and selected path:", e, selectedpath)
            pathbundle.append(selectedpath)
            for edge in convertPath2Edge(selectedpath):
                edge_counter[edge] += 1

    return pathbundle

def drawSampleNetwork():
    global all_edges, satellites, stations, federate_cost_dict, taskids
    plt.figure()
    loc_dict = {e: loc for e, loc in zip(satellites + stations, [(-0.2-1, 2), (0.7-1,2), (1.5-0.8,2), (0.3-0.2,1), (1.1, 1),(0.5, 0), (1.5, 0)])}
    sat_locs = [loc_dict[e] for e in satellites]
    sta_locs = [loc_dict[e] for e in stations]

    loc_element_dict = {loc: i+1 for i, loc in enumerate(sat_locs + sta_locs)}

    all_edges_locs = [(loc_dict[e[0]], loc_dict[e[1]]) for e in all_edges]

    for edge in all_edges_locs[:]:
        if edge[1] not in sta_locs:
            all_edges_locs.append((edge[1], edge[0]))
    # textloc = zip(satellites[:3], ['$F_1, T_1, S1$', '$F_2, T_2, S2$', '$F_1, T_3, S3$']) +
    textloc = [((sat_locs[0][0], sat_locs[0][1] + 0.2), '$F_1, e_1$'), ((sat_locs[1][0], sat_locs[1][1] + 0.2), '$F_2, e_2$'),
               ((sat_locs[2][0], sat_locs[2][1] + 0.2), '$F_1, e_3$'), ((sta_locs[0][0], sta_locs[0][1] - 0.2), '$F1, e_6 (G)$'),
               ((sta_locs[1][0], sta_locs[1][1] - 0.2), '$F2, e_7 (G)$') ,((sat_locs[3][0] - 0.2, sat_locs[3][1] - 0.1), '$F_2, e_4$'), ((sat_locs[4][0] + 0.2, sat_locs[4][1] - 0.1), '$F_1, e_5$')]

    element_federate_dict = {s: v for s,v in zip(sat_locs+sta_locs, [1, 2, 1, 2, 1, 1, 2])}

    # federate_cost_dict = {1: 400, 2: 300}
    # edge_cost_dict = {e: federate_cost_dict[element_federate_dict[e[1]]] if element_federate_dict[e[0]] != element_federate_dict[e[1]] else 0 for e in all_edges_locs}
    # for edge, cost in edge_cost_dict.items():
    #     print(edge, cost)
    plt.scatter(*zip(*sat_locs), marker='H', color='k', s=300, facecolors='w', linewidth='2')
    plt.scatter(*zip(*sta_locs), marker='H', color='k', s=400, facecolors='w', linewidth='2')

    edge_federate_dict = []
    all_arrows = []
    for edge in all_edges_locs:
        # plt.plot(*zip(*edge), 'k:', linewidth = 0.7)
        # if
        e1e2 = (loc_element_dict[edge[0]], loc_element_dict[edge[1]])
        legend = r'$l_{%d%d}$'%(e1e2[0], e1e2[1])
        # print(label)
        arr1 = plt.arrow(edge[0][0], edge[0][1], 0.9* (edge[1][0] - edge[0][0]), 0.9 * (edge[1][1] - edge[0][1]),
                  head_width=0.03, head_length=0.05, linewidth=0.7, fc='k', ec='k', zorder=-1, linestyle = ':')
        # arr2 plt.arrow(edge[1][0], edge[1][1], 0.9* (edge[0][0] - edge[1][0]), 0.9 * (edge[0][1] - edge[1][1]),
        #           head_width=0.03, head_length=0.05, linewidth=0.7, fc='k', ec='k', zorder=-1, linestyle = ':')
        x = (edge[0][0] + edge[1][0])/2.
        y = (edge[0][1] + edge[1][1])/2.
        nom , denom = ((edge[1][1] - edge[0][1]), (edge[1][0] - edge[0][0]))
        r = 180/math.pi * np.arctan((edge[1][1] - edge[0][1])/(edge[1][0] - edge[0][0])) if (edge[1][0] - edge[0][0]) != 0 else 'vertical'
        # print(edge, r)
        all_arrows.append((arr1, legend))
        if (nom>=0 and denom>0) or (nom<0 and denom>0):
            x += 0.05
            y += 0.05
        elif (nom==0 and denom<0):
            x -= 0.05
            y -= 0.05
        else:
            x -= 0.05
            y -= 0.05

        plt.text(x, y, ha="center", va="center", s=legend, bbox=dict(fc="none", ec="none", lw=2), rotation = r)

    for xy, text in textloc:
        plt.text(*xy, ha="center", va="center", s=text, bbox=dict(fc="none", ec="none", lw=2))

    plt.text(-0.3, 0.2, ha="left", va="center", s=r'$\zeta_{12}=%d$'%federate_cost_dict['F2'], bbox=dict(fc="none", ec="none", lw=2), rotation = 0)
    plt.text(-0.3, 0.1, ha="left", va="center", s=r'$\zeta_{21}=%d$'%federate_cost_dict['F1'], bbox=dict(fc="none", ec="none", lw=2), rotation = 0)
    plt.text(-0.3, 0.0, ha="left", va="center", s=r'$\zeta_{11}=  0$', bbox=dict(fc="none", ec="none", lw=2), rotation = 0)
    plt.text(-0.3, -0.1, ha="left", va="center", s=r'$\zeta_{22}=  0$', bbox=dict(fc="none", ec="none", lw=2), rotation = 0)

    font = FontProperties()
    font.set_style('italic')
    font.set_weight('bold')
    font.set_size('small')

    for i, (x, y) in enumerate([sat_locs[t-1] for t in taskids]):
        plt.text(x, y, ha="center", va="center", s='$T_%s$'%str(i+1), bbox=dict(fc="none", ec="none", lw=2), fontproperties=font)
    plt.xticks([])
    plt.yticks([])
    plt.axis('off')
    plt.savefig('sample_network.pdf', bbox_inches='tight')

    # plt.show()

def calTaskLinkRevenue(costlist, fi, federatelist, pathlist, pathLinkCount, linkCountDict, taskValueDict):
    global element_federate_dict
    federatelinkcost = 0.
    for path, federateCount in zip(pathlist, pathLinkCount):
        if element_federate_dict[path[0]] == federatelist[fi]:
            for fed, cost in zip(federatelist, costlist):
                federatelinkcost += cost * federateCount[fed]

    fed = federatelist[fi]
    # print("fed, linkcount, costlist: ", fed, costlist, linkCountDict)
    linkreveune = costlist[fi] * linkCountDict[fed]
    # print(taskValueDict[fed] , pathCostDict[fed])
    taskrevenue = taskValueDict[fed] - federatelinkcost

    return (taskrevenue, linkreveune)

class Constraint1():
    def __init__(self, fi, linkCountDict, pathlist, federatelist, pathLinkCount, taskValueDict, R_LiA, R_TiA):
        self.fi = fi
        self.linkCountDict = linkCountDict
        self.pathlist = pathlist
        # self.inicostlist = initcostlist
        self.federatelist = federatelist
        self.pathLinkCount = pathLinkCount
        self.taskValueDict = taskValueDict
        self.R_LiA = R_LiA
        self.R_TiA = R_TiA

    # def calTaskLinkRevenue(self, costlist, fi, federatelist, pathlist, pathLinkCount, linkCountDict, taskValueDict):
    #     federatelinkcost = 0.
    #     for path, federateCount in zip(pathlist, pathLinkCount):
    #         if path.elementOwner.federateOwner.name == federatelist[fi]:
    #             for fed, cost in zip(federatelist, costlist):
    #                 federatelinkcost += cost * federateCount[fed]
    #
    #     fed = federatelist[fi]
    #     linkreveune = costlist[fi] * linkCountDict[fed]
    #     # print(taskValueDict[fed] , pathCostDict[fed])
    #     taskrevenue = taskValueDict[fed] - federatelinkcost
    #
    #     return (taskrevenue, linkreveune)

    def __call__(self, costlist):
        R_Ti, R_Li = calTaskLinkRevenue(costlist, self.fi, self.federatelist, self.pathlist, self.pathLinkCount, self.linkCountDict, self.taskValueDict)
        # print(self.fi, R_Li + R_Ti, self.R_LiA[self.fi] + self.R_TiA[self.fi])
        return R_Li + R_Ti - self.R_LiA[self.fi] - self.R_TiA[self.fi]



class Constraint2():
    def __init__(self, pi, path, pathTaskValueList, pathLinkCount, federatelist):
        self.pi = pi
        self.path = path
        self.pathTaskValueList = pathTaskValueList
        self.pathLinkCount = pathLinkCount
        self.federatelist = federatelist
    def __call__(self, costlist):
        self.federateCount = self.pathLinkCount[self.pi]
        # pathcost = sum([c for c, f in zip(self.path.linkcostlist, self.path.linkfederatelist) if f is self.path.elementOwner.federateOwner])
        pathcost = 0.
        # print("Already path cost:", pathcost)
        value = self.pathTaskValueList[self.pi]
        for fed, cost in zip(self.federatelist, costlist):
            pathcost += cost * self.federateCount[fed]

        return value - pathcost

class Objective():
    def __init__(self, linkCountDict, pathlist, federatelist, pathLinkCount, taskValueDict, R_LiA, R_TiA):
        self.linkCountDict = linkCountDict
        self.pathlist = pathlist
        # self.inicostlist = initcostlist
        self.federatelist = federatelist
        self.pathLinkCount = pathLinkCount
        self.taskValueDict = taskValueDict
        self.R_LiA = R_LiA
        self.R_TiA = R_TiA
        self.R_A = [a+b for a,b in zip(R_LiA, R_TiA)]

    def __call__(self, costlist):
        R_T = []
        R_L = []
        for fi, _ in enumerate(self.federatelist):
            R_Ti, R_Li = calTaskLinkRevenue(costlist, fi, self.federatelist, self.pathlist, self.pathLinkCount, self.linkCountDict, self.taskValueDict)
            R_T.append(R_Ti)
            R_L.append(R_Li)

        print([a+b for a,b in zip(R_T, R_L)], self.R_A)
        print(sum([a+b for a,b in zip(R_T, R_L)]), sum(self.R_A))
        # return -1*(sum([abs(a+b-t-l) for a,b,t,l in zip(R_T, R_L, self.R_TiA, self.R_LiA)]))
        # return 1*(sum([abs(a+b-t-l) for a,b,t,l in zip(R_T, R_L, self.R_TiA, self.R_LiA)]))
        return 1*(sum([abs(a-b) for a,b,t,l in zip(R_T, R_L, self.R_TiA, self.R_LiA)]))

    # def __call__(self, costlist):
    #     # return -1*sum([a*b for a,b in zip(costlist, self.linkCountList)])
    #     print("costlist:", costlist)
    #     print("new revenue:", [a*b for a,b in zip(costlist, self.linkCountList)])
    #     return -1*sum([abs(a*b-c) for a,b,c in zip(costlist, self.linkCountList, self.Revenue)])
    #     # return -1*sum([abs(a-b)*2 for a,b in zip(costlist, self.initcostlist)])


def optimizeCost(adaptiveBestBundle, bestBundle):
    global linkCountList, federate_cost_dict, taskrevenue, element_federate_dict
    # global initcostlist, linkCountList, federatelist, pathLinkCount, taskValueDict, pathCostDict0, R_LiA, R_TiA
    # print("federate cost dict:", federate_cost_dict)
    initCostItems = sorted(list(federate_cost_dict.items()))
    federatelist = [e[0] for e in initCostItems]
    initcostlist = [e[1] for e in initCostItems]
    # print("federatelist & initcostlist: ", federatelist, initcostlist)


    # pathCostDict = defaultdict(int)
    pathLinkCount = []
    pathTaskValueList = []
    linkCountDict = defaultdict(int)
    taskValueDict = defaultdict(int)
    # pathCostDict0 = defaultdict(int)
    pathlist = bestBundle
    taskvalues = [taskrevenue[nl[0]] for nl in bestBundle]

    for taskvalue, path in zip(taskvalues, pathlist):
        federateOwner = element_federate_dict[path[0]]
        taskValueDict[federateOwner] += taskvalue
        linkfederates = [element_federate_dict[e] for e in path[1:] if federateOwner != element_federate_dict[e]]
        pathTaskValueList.append(taskvalue)
        # print(federateOwner, [e.name for e in path.linkfederatelist], linkfederates)
        federateCount = defaultdict(int, Counter(linkfederates))
        pathLinkCount.append(federateCount)
        for f, c in federateCount.items():
            linkCountDict[f] += c

    linkCountList = [e[1] for e in sorted(list(linkCountDict.items()))]
    # print(linkCountDict, linkCountList)

    pathLinkCount_A = []
    linkCountDict_A = defaultdict(int)
    taskValueDict_A = defaultdict(int)
    # pathCostDict0 = defaultdict(int)
    pathlist_A = adaptiveBestBundle
    taskvalues_A = [taskrevenue[nl[0]] for nl in adaptiveBestBundle]

    for taskvalue, path in zip(taskvalues_A, pathlist_A):
        federateOwner = element_federate_dict[path[0]]
        taskValueDict_A[federateOwner] += taskvalue
        linkfederates = [element_federate_dict[e] for e in path[1:] if federateOwner != element_federate_dict[e]]
        federateCount = defaultdict(int, Counter(linkfederates))
        pathLinkCount_A.append(federateCount)
        for f, c in federateCount.items():
            linkCountDict_A[f] += c

    # linkCountList_A = [e[1] for e in sorted(list(linkCountDict_A.items()))]
    # print("Federate link Count list:", linkCountList_A)

    # pathCostDict_A = defaultdict(int)
    # pathCostDict_A[federateOwner] = sum([federateCount[fed] * cost
    #                                        for federateCount, fed, cost in zip(pathLinkCount_A, federatelist, initcostlist)])
    # if len(pathlist) != len(pathlist_A):
    #     print(len(pathlist), len(pathlist_A))
    R_LiA = []
    R_TiA = []
    for i in range(len(federatelist)):
        Rt, Rl = calTaskLinkRevenue(initcostlist, i, federatelist, pathlist_A, pathLinkCount_A, linkCountDict_A, taskValueDict_A)
        R_LiA.append(Rl)
        R_TiA.append(Rt)

    # print("Revenue Adaptive:", sum(R_TiA) + sum(R_LiA))

    # print("zero and adaptive links:", linkCountDict, linkCountDict_A)

    # print("Adaptive task and link revenue:", R_TiA, R_LiA)
    # def objective(costlist):
    #     global linkCountList
    #     # print("objective funciton :", )
    #     # print(linkCountList)
    #     return -1*sum([a*b for a,b in zip(costlist, linkCountList)])
    objective = Objective(linkCountDict, pathlist, federatelist, pathLinkCount, taskValueDict, R_LiA, R_TiA)

    conslist1 = [{'type': 'ineq', 'fun': Constraint1(i, linkCountDict, pathlist, federatelist, pathLinkCount, taskValueDict, R_LiA, R_TiA)} for i in range(len(initcostlist))]
    conslist2 = [{'type': 'ineq', 'fun': Constraint2(i, path, pathTaskValueList, pathLinkCount, federatelist)} for i, path in enumerate(pathlist)]


    # con1 = {'type': 'ineq', 'fun': constraint1}
    # con2 = {'type': 'ineq', 'fun': constraint2}
    # con3 = {'type': 'ineq', 'fun': constraint3}

    cons = conslist1 + conslist2 # [con1, con2, con3][:len(initCostDict)]

    bnds = [(min(100, 1100), 1101) for c in initcostlist]
    # print("boundaries:", bnds)

    # print("length of constraints:", len(initCostDict), len(cons))
    templist = initcostlist[:]
    initcostlist = [0 for i in range(len(initcostlist))]

    sol = minimize(objective, initcostlist, method = 'SLSQP', bounds = bnds, constraints = cons)

    # print("solution:", sol.x)
    # print("constraints:")
    # for con in cons:
    cons_changes = [int(round(con['fun'](sol.x))) for con in cons]
    # print(cons_changes)
    # consresults = all([e >= 0 for e in [int(round(con['fun'](sol.x))) for con in cons]])
    if all([e >= 0 for e in cons_changes]) and sum(cons_changes[:2])>0:
        # if True:
        # print(templist, [int(e) for e in sol.x])


        # print("Revenue 2, 1:", [int(round(con['fun'](sol.x))) for con in cons])
        # print('')
        return {'F%d' % (i+1): c for i, c in enumerate(list(sol.x))}
    else:
        return False


if __name__ == '__main__':
    time = 0
    federates = ['F1', 'F2']
    elements = ['e1', 'e2', 'e3', 'e4', 'e5', 'e6', 'e7']
    satellites = elements[:5]
    stations = elements[5:]

    element_federate_dict = {'e1':federates[0], 'e2':federates[1], 'e3':federates[0], 'e4':federates[1], 'e5': federates[0], 'e6':federates[0], 'e7':federates[1]}
    taskids = [1,2,3,4]
    federates = [1,2,1,1]
    taskrevenue = {e: 1001 for e in elements}

    all_edges = [(satellites[0],satellites[1]), (satellites[3],stations[0]), (satellites[1],satellites[3]),
                 (satellites[2],satellites[4]), (satellites[2],satellites[1]), (satellites[2],satellites[3]), (satellites[3],satellites[4]), (satellites[4],stations[1]), (satellites[2],stations[0])]
    #
    # federate_cost_dict = {'F1': 600, 'F2': 500}
    # drawSampleNetwork()
    #
    # maxlink = 2
    # G = nx.DiGraph()
    # G.add_nodes_from(elements)
    # G.add_edges_from(all_edges)
    #
    # sources = [elements[i-1] for i in taskids]
    # destinations = [elements[i-1] for i in [6, 7]]
    # orderPathDict = addPaths(G, sources, destinations)
    # print(orderPathDict)
    #
    # pathbundle1 = returnBestBundle()
    # stored_federate_cost_dict = {f: v for f, v in federate_cost_dict.items()}
    # federate_cost_dict = {f: 0 for f in federate_cost_dict}
    #
    # pathbundle0 = returnBestBundle()
    #
    # print("path bundle current:", pathbundle1)
    #
    # print("path bundle zero:", pathbundle0)
    #
    # federate_cost_dict = {f: v for f,v in stored_federate_cost_dict.items()}
    #
    # newprice = optimizeCost(pathbundle1, pathbundle0)
    #
    # print(newprice)
    # # plt.figure()
    # # nx.draw(G)
    # # plt.show()

    # The new seciton for MILP


