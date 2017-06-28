import networkx as nx
import re
import matplotlib.pyplot as plt
import networkx.algorithms.isomorphism as iso
import math
import numpy as np
import time
from itertools import cycle


class Graph():
    def __init__(self):
        self.graphList = []
        self.nodeLocations = []
        self.shortestPathes = []
        self.shortestPathCost = []
        self.elements = []
        self.federates = []
        self.elementOwners = {}
        self.graphOrder = None

    def findbestxy(self, N):
        if N%2 != 0:
            N += 1
        temp = int(N**0.5)
        while N%temp != 0:
            temp -= 1

        return (temp, N//temp)


    def convertLocation2xy(self, location):
        if 'SUR' in location:
            r = 0.5
        elif 'LEO' in location:
            r = 1
        elif 'MEO' in location:
            r = 2
        else:
            r = 2.25

        sect = int(re.search(r'.+(\d)', location).group(1))
        tetha = +math.pi/3-(sect-1)*math.pi/3

        x, y = (r*math.cos(tetha), r*math.sin(tetha))
        # print location, x, y
        return (x,y)

    def convertPath2Edge(self, pathlist):
        tuplist = []
        for i in range(len(pathlist) - 1):
            tuplist.append((pathlist[i], pathlist[i+1]))

        return tuplist

    # def findShortestPathes(self, G):
    #     pathdict = {}
    #     costdict = {}
    #
    #     nodes = G.nodes()
    #     # print "nodes:", nodes
    #     satellites = [n for n in nodes if 'GS' not in n]
    #     groundstations = [n for n in nodes if 'GS' in n]
    #     for s in satellites:
    #         temppathlist = []
    #         pathcostlist = []
    #         for g in groundstations:
    #             if nx.has_path(G, source=s,target=g):
    #                 sh = nx.shortest_path(G, s, g)
    #                 temppathlist.append(sh)
    #                 tuplist = self.convertPath2Edge(sh)
    #                 # print tuplist
    #                 costlist = []
    #                 for (source, target) in tuplist:
    #                     cost = 0 if self.elementOwners[s] == self.elementOwners[target] else G[source][target]['weight']
    #                     costlist.append(cost)
    #
    #                 pathcostlist.append(costlist)
    #
    #
    #         pathdict[s] = temppathlist#min(temppathlist, key = lambda x: len(x)) if temppathlist else None
    #         costdict[s] = pathcostlist
    #         # print "pathtuplist:", tuplist
    #         # print "designCost:", costlist
    #
    #
    #     # print "graphList all paths:"
    #     # print pathdict[satellites[0]]
    #     # print costdict[satellites[0]]
    #     return pathdict, costdict
    #
    # def findcheapestpath(self, s):
    #     # print self.getShortestPathes(), s
    #     pathlist = self.getShortestPathes()[s]
    #     costlist = self.getShortestPathCost()[s]
    #     sortedpath = [x for (y,x) in sorted(zip([sum(c) for c in costlist], pathlist))]
    #     # print "cost vs path:", sorted(zip([sum(c) for c in costlist], pathlist))
    #
    #     # return self.convertPath2Edge(sortedpath[0])
    #     return sortedpath[0]

    def addNewGraph(self, G):
        nodes2 = G.nodes()
        out_deg2 = G.out_degree(nodes2)
        equallist = []
        for i, g in enumerate(self.graphList):
            nodes1 = g.nodes()
            out_deg1 = g.out_degree(nodes1)
            # print [(out_deg1[k], out_deg2[k]) for k in out_deg2]
            if out_deg1 == out_deg2:
                # print [(set(g.neighbors(n)), set(G.neighbors(n))) for n in nodes1]
                # print any(map(lambda x: x[0] != x[1], [(set(g.neighbors(n)), set(G.neighbors(n))) for n in nodes1]))
                # print map(lambda x: x[0] != x[1], [(set(g.neighbors(n)), set(G.neighbors(n))) for n in nodes1])
                if any(map(lambda x: x[0] != x[1], [(set(g.neighbors(n)), set(G.neighbors(n))) for n in nodes1])):
                    continue
                else:
                    if len(self.graphList) == 6:
                        return i

        # print "Not equal to eigther"
        self.graphList.append(G)
        # self.nodeLocations.append([e.getLocation() for e in self.elements])
        # pathdict, costdict = self.findShortestPathes(G)
        # self.shortestPathes.append(pathdict)
        # self.shortestPathCost.append(costdict)
        return len(self.graphList) - 1

        # print len(self.graphList), G.number_of_nodes(), G.number_of_edges()



    def canTransmit(self, txElement, rxElement):

        txsection = int(re.search(r'.+(\d)', txElement.getLocation()).group(1))
        rxsection = int(re.search(r'.+(\d)', rxElement.getLocation()).group(1))
        canT = False

        if txElement.isSpace() and rxElement.isSpace():
            if abs(txsection - rxsection) <= 1 or abs(txsection - rxsection) == 5:
                canT = True

        elif txElement.isSpace() and rxElement.isGround():
            if txsection == rxsection:
                canT = True

        return canT



    def createGraph(self, context):
        self.federates = context.federates[:]
        self.elements = elements = context.elements[:]
        self.elementOwners = {element: federate for (element, federate) in
                         zip([e.name for e in self.elements], [e.getOwner().name for e in self.elements])}

        elementlocations = [e.getLocation() for e in elements]
        # print elementlocations

        G = nx.DiGraph()
        elementsnames = ['%s.%d'%(e, len(self.graphList)) for e in elements]

        G.add_nodes_from(elementsnames)
        # print [e.name for e in elements]

        for tx in elements:
            for rx in elements:
                if tx == rx:
                    continue

                if self.canTransmit(tx, rx):
                    txowner = context.getElementOwner(tx)
                    rxowner = context.getElementOwner(rx)
                    cost = 0.
                    if txowner != rxowner:
                        if rx.isSpace():
                            cost = rxowner.getCost('oISL')
                        elif rx.isGround():
                            cost = rxowner.getCost('oSGL')

                    G.add_edge(tx.name, rx.name, weight=cost)

        self.graphOrder = self.addNewGraph(G)
        # print "graphList order:", self.graphOrder
        # self.drawGraph()

    def getGraph(self):
        return self.graphList[self.graphOrder]

    def getGraphList(self):
        return self.graphList

    def getGraphOrder(self):
        return self.graphOrder

    def getElementOwners(self):
        return self.elementOwners

    def getShortestPathes(self):
        return self.shortestPathes[self.graphOrder]

    def getShortestPathCost(self):
        return self.shortestPathCost[self.graphOrder]

    def drawGraph(self):
        G = self.graphList[self.graphOrder]

        if not plt.fignum_exists(1):
            plt.figure(1)
            plt.ion()
            plt.show()

        plt.clf()
        nodes = [e.name for e in self.elements]
        # print "nodes:", nodes
        # satellites = [n for n in nodes if 'GS' not in n]
        # alltuples = set([])
        # for s in satellites:
        #     path = self.findcheapestpath(s)
        #     pathedges = self.convertPath2Edge(path)
        #     # print "graphorder & source & path:", s, pathedges
        #     alltuples = alltuples.union(pathedges)


        nodeLocations = [e.getLocation() for e in self.elements]
        pos = {e.name: self.convertLocation2xy(nodeLocations[i]) for i, e in enumerate(self.elements)}
        sec = {e.name: nodeLocations[i] for i, e in enumerate(self.elements)}
        labels = {n: n[0] + n[-3:] for n in nodes}
        labelpos = {n: [v[0], v[1] + 0.3] for n, v in pos.items()}
        x = np.linspace(-1.0, 1.0, 50)
        y = np.linspace(-1.0, 1.0, 50)
        X, Y = np.meshgrid(x, y)
        F = X ** 2 + Y ** 2 - 0.75
        plt.contour(X, Y, F, [0])
        # print nodes
        nx.draw_networkx_nodes(G, pos, nodelist=[n for n in nodes if 'GS' not in n and 'LE' not in sec[n]],
                               node_color='r', node_size=100)
        nx.draw_networkx_nodes(G, pos, nodelist=[n for n in nodes if 'GS' not in n and 'LE' in sec[n]],
                               node_color='g', node_size=100)
        nx.draw_networkx_nodes(G, pos, nodelist=[n for n in nodes if 'GS' in n], node_color='b', node_size=100)

        # nx.draw_networkx_edges(G, pos, edgelist=list(alltuples))
        nx.draw_networkx_edges(G, pos)
        nx.draw_networkx_labels(G, labelpos, labels, font_size=8)
        plt.xticks([])
        plt.yticks([])
        plt.xlim(-2.5, 2.5)
        plt.ylim(-2.5, 2.5)
        # plt.draw()
        plt.draw()
        plt.pause(0.2)

    # Figure is closed

    def drawGraphs(self):
        # pos = None

        plt.figure()
        n1,n2 = self.findbestxy(len(self.graphList))
        # print n1,n2
        earth = plt.Circle((0, 0), 1.1, color='k', fill=True)

        for j, g in enumerate(self.graphList):
            nodes = [e.name for e in self.elements]
            pos = {e.name: self.convertLocation2xy(self.nodeLocations[j][i]) for i, e in enumerate(self.elements)}
            sec = {e.name: self.nodeLocations[j][i] for i, e in enumerate(self.elements)}
            labels = {n: n[0] + n[-3:] for n in nodes}
            labelpos = {n: [v[0], v[1] + 0.3] for n, v in pos.items()}
            ax = plt.subplot('%d%d%d'%(n1, n2, j+1))
            x = np.linspace(-1.0, 1.0, 50)
            y = np.linspace(-1.0, 1.0, 50)
            X, Y = np.meshgrid(x, y)
            F = X ** 2 + Y ** 2 - 0.75
            plt.contour(X, Y, F, [0])
            # print nodes
            nx.draw_networkx_nodes(g, pos, nodelist = [n for n in nodes if 'Ground' not in n and 'LE' not in sec[n]], node_color = 'r', node_size = 100)
            nx.draw_networkx_nodes(g, pos, nodelist=[n for n in nodes if 'Ground' not in n and 'LE' in sec[n]],node_color='g', node_size=100)
            nx.draw_networkx_nodes(g, pos, nodelist = [n for n in nodes if 'Ground' in n], node_color = 'b', node_size = 100)
            nx.draw_networkx_edges(g, pos)
            nx.draw_networkx_labels(g, labelpos, labels, font_size=8)
            plt.xticks([])
            plt.yticks([])
            plt.xlim(-2.5,2.5)
            plt.ylim(-2.5,2.5)
            # ax.set_title('Graph:'+str(j))
            # print j, self.shortestPathes[j]

        # plt.savefig("Networks_elements%d_.png"%len(self.elements), bbox_inches='tight')
        plt.show()


class SuperGraph(Graph):
    def __init__(self, element):
        Graph.__init__(self)
        self.storagePenalty = 6*[0]
        self.rawSuperGraph = None
        self.SuperGaph = None
        self.elementOwner = element
        self.superShorestPaths = None
        self.superPathsCost = None
        self.graphList = []


    def createGraph(self):
        G = nx.DiGraph()
        for i, g in enumerate(self.graphList):
            G = nx.compose(G, g)

        self.rawSuperGraph = G
        self.addStorgeEdges(self.rawSuperGraph)
        self.updatePaths()

    def addStorgeEdges(self, G):
        for i, s in enumerate(self.storagePenalty):
            name1 = '%s.%d'%(self.elementOwner.name, i%6)
            name2 = '%s.%d'%(self.elementOwner.name, (i+1)%6)
            G.add_edge(name1, name2, weight= s)

        self.SuperGaph = G

    def updateSuperGraph(self, storagepenalty):
        assert len(storagepenalty) <= len(self.storagePenalty)
        for i in range(len(self.graphOrder)):
            storagepenalty.append(storagepenalty.pop(0))

        self.storagePenalty[:len(storagepenalty)] = storagepenalty
        self.storagePenalty = storagepenalty
        self.addStorgeEdges(self.rawSuperGraph)
        self.updatePaths()

    def updatePaths(self):
        pathlist, costlist = self.findShortestPathes(self.SuperGaph)
        self.superShorestPaths = pathlist
        self.superPathsCost = costlist
        print "Updatepaths:", pathlist, costlist

    def findShortestPathes(self, G):
        nodes = G.nodes()
        # print "nodes:", nodes
        sourcename = '%s.%d'%(self.elementOwner.name, self.graphOrder-1)

        groundstations = [n for n in nodes if 'GS' in n]
        temppathlist = []
        pathcostlist = []
        for i in range(len(self.storagePenalty)):
            for g in groundstations:
                g = '%s.%d'%(self.elementOwner.name, i)
                if nx.has_path(G, source=sourcename,target=g):
                    sh = nx.shortest_path(G, sourcename, g)
                    temppathlist.append(sh)
                    tuplist = self.convertPath2Edge(sh)
                    # print tuplist
                    costlist = []
                    for (source, target) in tuplist:
                        cost = 0 if self.elementOwners[sourcename[:-2]] == self.elementOwners[target[:-2]] else G[source][target]['weight']
                        costlist.append(cost)

                    pathcostlist.append(costlist)


        return temppathlist, pathcostlist

    def findcheapestpath(self):
        pathlist = self.superShorestPaths
        costlist = self.superPathsCost
        sortedpath = [x for (y,x) in sorted(zip([sum(c) for c in costlist], pathlist))]
        # print "cost vs path:", sorted(zip([sum(c) for c in costlist], pathlist))

        # return self.convertPath2Edge(sortedpath[0])
        return sortedpath[0]

        # def setGraphList(self, context):
        #     self.graphList = context.Graph.graphList
        #     self.graphOrder = context.Graph.graphOrder









