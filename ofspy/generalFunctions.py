import matplotlib.pyplot as plt
import numpy as np
import networkx as nx
import re
import math
from collections import Counter, defaultdict
# from .bundle import PathBundle

def checkEqual2(iterator):
   return len(set(iterator)) <= 1

def findbestxy(N):
    if N % 2 != 0:
        N += 1
    temp = int(N ** 0.5)
    while N % temp != 0:
        temp -= 1

    return (temp, N // temp)

def convertPath2Edge(pathlist):
    tuplist = []
    for i in range(len(pathlist) - 1):
        tuplist.append((pathlist[i], pathlist[i + 1]))

    return tuplist

def convertLocation2xy(location):
    if 'SUR' in location:
        r = 0.5
    elif 'LEO' in location:
        r = 1.5
    elif 'MEO' in location:
        r = 2
    else:
        r = 2.25

    sect = int(re.search(r'.+(\d)', location).group(1))
    tetha = +math.pi / 3 - (sect - 1) * math.pi / 3

    x, y = (r * math.cos(tetha), r * math.sin(tetha))
    # print location, x, y
    return (x, y)


def convertPath2StaticPath(path):
    temppath = [e[:-2] for e in path.nodelist]
    ends = [e[-1] for e in path.nodelist]
    seen = set([])
    seen_add = seen.add
    staticpath = [e for e in temppath if not (e in seen or seen_add(e))]
    # print "convert path 2 static path:", path, staticpath
    deltatime = path.deltatime
    assert len(set(ends[deltatime:])) == 1
    return (staticpath, deltatime)

def fillBetween3Points(a, b, c):
    sortedpoints = sorted([a,b,c])
    # print sortedpoints
    z = zip(a,b,c)
    x1 = np.linspace(sortedpoints[0][0], sortedpoints[1][0], num=2)
    x2 = np.linspace(sortedpoints[1][0], sortedpoints[2][0], num=2)
    # print x1, x2
    y1 = (sortedpoints[0][1]-sortedpoints[1][1])*(x1-sortedpoints[0][0])/float(sortedpoints[0][0]-sortedpoints[1][0]) + sortedpoints[0][1] if sortedpoints[0][0]-sortedpoints[1][0] != 0 else None
    y2 = (sortedpoints[0][1]-sortedpoints[2][1])*(x1-sortedpoints[0][0])/float(sortedpoints[0][0]-sortedpoints[2][0]) + sortedpoints[0][1] if sortedpoints[0][0]-sortedpoints[2][0] != 0 else None
    y3 = (sortedpoints[0][1]-sortedpoints[2][1])*(x2-sortedpoints[2][0])/float(sortedpoints[0][0]-sortedpoints[2][0]) + sortedpoints[2][1] if sortedpoints[0][0]-sortedpoints[2][0] != 0 else None
    y4 = (sortedpoints[1][1]-sortedpoints[2][1])*(x2-sortedpoints[2][0])/float(sortedpoints[1][0]-sortedpoints[2][0]) + sortedpoints[2][1] if sortedpoints[1][0]-sortedpoints[2][0] != 0 else None
    # plt.fill_betweenx(X, Y, interpolate=True)
    col = 'yellow'
    if y1 is None:
        # plt.plot(x2, y3, 'g')
        # plt.plot(x2, y4, 'g')
        plt.fill_between(x2, y3, y4, color = col)
    elif y4 is None:
        # plt.plot(x1, y1, 'g')
        # plt.plot(x1, y2, 'g')
        plt.fill_between(x1, y1, y2, color= col)

    elif y2 is None or y3 is None:
        print("there is error with points")

    else:
        # plt.plot(x1, y1, 'g')
        # plt.plot(x1, y2, 'g')
        # plt.plot(x2, y3, 'g')
        # plt.plot(x2, y4, 'g')
        plt.fill_between(x1, y1, y2, color= col)
        plt.fill_between(x2, y3, y4, color= col)

def drawGraph(graph, context):
    G = graph.graphList[graph.graphOrder]

    if not plt.fignum_exists(1):
        plt.figure(1)
        plt.ion()
        plt.show()

    plt.clf()
    nodes = [e.name for e in graph.elements]
    nameselementdict = {x: y for (x, y) in zip(nodes, graph.elements)}
    # print "nodes:", nodes
    satellites = [n for n in nodes if 'GS' not in n]
    # alltuples = set([])
    # for s in satellites:
    #     path = graph.findcheapestpath(s)
    #     pathedges = convertPath2Edge(path)
    #     # print "graphorder & source & path:", s, pathedges
    #     alltuples = alltuples.union(pathedges)

    alltuples = set([])
    print("Number of saved tasks:", [len(element.savedTasks) for element in graph.elements])
    currenttasks = [e for l in [element.savedTasks for element in graph.elements] for e in l]
    assert len(set(currenttasks)) == len(currenttasks)
    activetasks = [t for t in currenttasks if t.activationTime == context.time]
    for actives in activetasks:
        path = [a.name for a in actives.pathlist]
        pathedges = convertPath2Edge(path)
        alltuples = alltuples.union(pathedges)

    # for s in satellites:
    #     path = graph.findcheapestpath(s)
    #     pathedges = convertPath2Edge(path)
    #     # print "graphorder & source & path:", s, pathedges
    #     alltuples = alltuples.union(pathedges)
    recenttasks = [t.taskid for t in currenttasks if t.initTime == context.time-1]
    # print "recent tasks:", recenttasks
    elementswithrecenttasks = [e for e in graph.elements if set([t.taskid for t in e.savedTasks]).intersection(recenttasks)]
    # print "elementlist with recent tasks:", elementswithrecenttasks

    section2pointsdict = {1: [(0, 1), (0.866, 0.5)], 2: [(0.866, 0.5), (0.866, -0.5)], 3: [(0.866, -0.5), (0, -1)], 4: [(0, -1), (-0.866, -0.5)], 5: [(-0.866, -0.5), (-0.866, 0.5)], 6: [(-0.866, 0.5), (0, 1)]}

    nodeLocations = [e.getLocation() for e in graph.elements]
    pos = {e.name: convertLocation2xy(nodeLocations[i]) for i, e in enumerate(graph.elements)}

    positionsection = [[pos[e.name]]+section2pointsdict[e.section] for e in elementswithrecenttasks]
    # print "position and section :", positionsection

    sec = {e.name: nodeLocations[i] for i, e in enumerate(graph.elements)}
    labels = {n: n[0] + n[-3:] for n in nodes}
    labelpos = {n: [v[0], v[1] + 0.3] for n, v in pos.items()}
    x = np.linspace(-1.0, 1.0, 50)
    y = np.linspace(-1.0, 1.0, 50)
    X, Y = np.meshgrid(x, y)
    F = X ** 2 + Y ** 2 - 0.75
    plt.contour(X, Y, F, [0])
    # print nodes
    nx.draw_networkx_nodes(G, pos, nodelist=[n for n in nodes if 'GS' not in n and nameselementdict[n].savedTasks],
                           node_color='r', node_size=100)

    nx.draw_networkx_nodes(G, pos, nodelist=[n for n in nodes if 'GS' not in n and not nameselementdict[n].savedTasks],
                           node_color='g', node_size=100)

    # nx.draw_networkx_nodes(Graph, pos, nodelist=[n for n in nodes if 'GS' not in n and 'LE' in sec[n]], node_color='g', node_size=100)

    nx.draw_networkx_nodes(G, pos, nodelist=[n for n in nodes if 'GS' in n], node_color='b', node_size=100)

    # print "Graph all tuples: ", alltuples
    for ps in positionsection:
        fillBetween3Points(*ps)

    nx.draw_networkx_edges(G, pos, edgelist=list(alltuples))
    # nx.draw_networkx_edges(Graph, pos)
    nx.draw_networkx_labels(G, labelpos, labels, font_size=8)

    plt.xticks([])
    plt.yticks([])
    plt.xlim(-2.5, 2.5)
    plt.ylim(-2.5, 2.5)
    # plt.draw()
    plt.draw()
    plt.waitforbuttonpress()
    # plt.pause(0.5)


# Figure is closed

def drawGraphs(graph):
    # pos = None

    plt.figure()
    n1, n2 = findbestxy(len(graph.graphList))
    # print n1,n2
    earth = plt.Circle((0, 0), 1.1, color='k', fill=True)

    for j, g in enumerate(graph.graphList):
        nodes = [e.name for e in graph.elements]
        pos = {e.name: convertLocation2xy(graph.nodeLocations[j][i]) for i, e in enumerate(graph.elements)}
        sec = {e.name: graph.nodeLocations[j][i] for i, e in enumerate(graph.elements)}
        labels = {n: n[0] + n[-3:] for n in nodes}
        labelpos = {n: [v[0], v[1] + 0.3] for n, v in pos.items()}
        ax = plt.subplot('%d%d%d' % (n1, n2, j + 1))
        x = np.linspace(-1.0, 1.0, 50)
        y = np.linspace(-1.0, 1.0, 50)
        X, Y = np.meshgrid(x, y)
        F = X ** 2 + Y ** 2 - 0.75
        plt.contour(X, Y, F, [0])
        # print nodes
        nx.draw_networkx_nodes(g, pos, nodelist=[n for n in nodes if 'Ground' not in n and 'LE' not in sec[n]],
                               node_color='r', node_size=100)
        nx.draw_networkx_nodes(g, pos, nodelist=[n for n in nodes if 'Ground' not in n and 'LE' in sec[n]],
                               node_color='g', node_size=100)
        nx.draw_networkx_nodes(g, pos, nodelist=[n for n in nodes if 'Ground' in n], node_color='b', node_size=100)
        nx.draw_networkx_edges(g, pos)
        nx.draw_networkx_labels(g, labelpos, labels, font_size=8)
        plt.xticks([])
        plt.yticks([])
        plt.xlim(-2.5, 2.5)
        plt.ylim(-2.5, 2.5)
        # ax.set_title('Graph:'+str(j))
        # print j, graph.shortestPathes[j]

    # plt.savefig("Networks_elements%d_.png"%len(graph.elementlist), bbox_inches='tight')
    plt.show()


def bfs_paths(G, source, destination):
    queue = [(source, [source])]
    while queue:
        v, path = queue.pop(0)
        for next in set(G.neighbors(v)) - set(path):
            if next == destination:
                yield path + [next]
            else:
                queue.append((next, path + [next]))

def findAllPaths(G, sources, destinations):
    allpathes = []
    for s in sources:
        for d in destinations:
            allpathes.extend(bfs_paths(G, s, d))

    return allpathes

#
# class Path():
#     def __init__(self, l):
#         self.linklist = l
def findClosestIndex(value, valulist):
    abslist = [abs(v-value) for v in valulist]
    return abslist.index(min(abslist))


def addDict2Dict(dict1, dict2):
    dict3 = dict1.copy()
    for d, c in dict2.items():
        dict3[d] += c
    return dict3

def returnCompatiblePaths(pathlist, linkcounter, maxlink = 1):
    # for path in pathlist[0]

    # print("length of pathlist:", len(pathlist))
    if pathlist:
        queue = [(0, [], linkcounter)]
        while queue:
            n, histpath, s = queue.pop(0)
            # print("length of pathlist and n:", len(pathlist), n)
            # if n == len(pathlist) - 1:
            #     yield histpath
            # else:
            nextpaths = []
            for path in pathlist[n]:
                newcounter = Counter(path.linklist)
                combinedcounter = addDict2Dict(s, newcounter)
                valueset = list(combinedcounter.values())
                # print("counter value set:", valueset)
                # print(combinedcounter)
                if max(valueset) <= maxlink:
                    nextpaths.append(path)
                # else:
                #     print(max(valueset))

            # print(len(pathlist[n]), len(nextpaths))
            # print("current path, next pathf:\n", [e.linklist for e in histpath],'\n', [p.linklist for p in nextpaths])
            # print("set:", s)
            n += 1
            for np in nextpaths:
                # print("new path:", np.linklist)
                if n == len(pathlist):
                    yield histpath + [np]
                else:
                    # scopy = s.union(set(np.linklist))
                    combinedcounter = addDict2Dict(s, newcounter)
                    queue.append((n, histpath + [np], combinedcounter))


def returnAvgPathCost(taskPathDict):
    tasksumcostnum = [(min([p.pathCost for p in paths]), len(paths), taskid) for taskid, paths in taskPathDict.items()]
    # tasksumcostnum = [(min([len(p.nodelist) for p in paths]), len(paths), taskid) for taskid, paths in taskPathDict.items()]
    avgcosttask = sorted([(x, z) for x,y,z in tasksumcostnum])
    # print("avg cost task:", avgcosttask)
    return avgcosttask

def combineBundles(bundles):
    alltasks = []
    allpaths = []
    for b in bundles:
        alltasks.extend(list(b.tasklist))
        allpaths.extend(list(b.pathlist))

    return alltasks, allpaths


def generateFops(costrange, storange):
    fops = []
    for cost in costrange:
        costsgl = cost
        costisl = cost

        for sto in storange:
            stopen = sto
            for sto2 in storange:
                stopen2 = sto2
                yield ["x%d,%d,%d" % (costsgl, costisl, stopen2), "x%d,%d,%d" % (costsgl, costisl, stopen), "x%d,%d,%d" % (costsgl, costisl, sotpen)]

    #
    # for path in pathlist[0]:
    #     print(path)
    #     tempset = set(path.linklist)
    #     print("Linkset and temp set:", linkset, tempset)
    #     inter = linkset.intersection(tempset)
    #     print(inter)
    #     if inter:
    #         continue
    #     else:
    #         nextset = linkset.union(tempset)
    #         print("nextset:", nextset)
    #         print("length:", len(pathlist))
    #         if len(pathlist)>1:
    #
    #             yield returnCompatiblePaths(pathlist[1:], nextset, histpath + [path])
    #         else:
    #             yield histpath + [path]

# l1 = [(1,2), (2,3), (3,4)]
# l2 = [(2,4), (4,9)]
# l3 = [(1,3), (4,5)]
#
#
# p1 = Path(l1)
# p2 = Path(l2)
# p3 = Path(l3)
# p4 = Path([(1,4),(5,6)])
#
# gen = returnCompatiblePaths([[p1, p2, p3, p4], [p1, p2, p3, p4],[p1, p2, p3, p4]])
# print(len(list(gen)))
# for g in gen:
#     print([e.linklist for e in g])

# nodes = range(1,12)
# edges = [(1,7), (4,7), (4,2), (6,2), (4,7), (7,3), (7,5), (2,5), (2,8), (3,11), (3,9), (5,11), (5,9), (8,9), (8,10)]
# sources = [1, 4, 6]
# destinations = [9, 10, 11]
#
# Graph = nx.DiGraph()
# Graph.add_nodes_from(nodes)
# Graph.add_edges_from(edges)
#
# # for s in sources:
# #     print s
# #     gen = findAllPaths(Graph, [s], destinations)
# #     print gen
#
#
# print findAllPathes(Graph, sources, destinations)