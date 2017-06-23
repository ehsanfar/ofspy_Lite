import random
import numpy as np
from .task import Task
import Queue
from .federateLite import FederateLite
import re

from .Graph import Graph

class ContextLite():
    def __init__(self):
        """
        @param locations: the locations in this context
        @type locations: L{list}
        @param events: the events in this context
        @type events: L{list}
        @param federations: the federations in this context
        @type federations: L{list}
        @param seed: the seed for stochastic events
        @type seed: L{int}
        """
        self.initTime = 0
        self.maxTime = 0
        self.time = 0
        self.federates = []
        self.elements = []
        self.masterfederate = []
        self.seed = 0
        self.currentTasks = {i: Queue.Queue(maxsize = 3) for i in range(1,7)}
        self.graph = []
        self.nodeLocations = []
        self.shortestPathes = []
        self.Graph = None



    def init(self, ofs):
        self.time = ofs.initTime
        self.initTime = ofs.initTime
        self.maxTime = ofs.maxTime

        self.masterStream = random.Random(self.seed)
        self.shuffleStream = random.Random(self.masterStream.random())
        self.orderStream = random.Random(self.masterStream.random())


        self.generateFederates(ofs.elements)
        self.generateTasks(N = 6)
        self.elements = self.getElements()

        self.Graph = Graph()
        self.Graph.createGraph(self)



    def getElementOwner(self, element):

        return next((federate for federate in self.federates
                     if element in federate.elements), None)

    def getTaskOwner(self, task):
        return task.federateOwner

    def findTask(self, task):

        return next((element for federate in self.federates
                     for element in federate.elements
                     if task in element.savedTasks), None)

    def executeOperations(self, scheme = 'federated'):
        """
        Executes operational models.
        """
        if scheme == 'federated':
            federates = self.federates
            random.shuffle(federates, random=self.orderStream.random)
            for federate in federates:
                # print "Pre federate operation cash:", federate.cash
                federate.ticktock()
                # print "Post federate operation cash:", federate.cash
        elif scheme == 'centralized':
            self.masterfederate.ticktock()


    def ticktock(self, ofs):
        """
        Tocks this context in a simulation.
        """
        self.time = ofs.time

        self.executeOperations()
        self.Graph.createGraph(self)
        # self.Graph.drawGraphs()
        print self.time, [a.getLocation() for a in self.elements]


    def generateTasks(self, N=6):
        tasklocations = np.random.choice(range(1,7), N)
        for l in tasklocations:
            if self.currentTasks[l].full():
                self.currentTasks[l].get()

            self.currentTasks[l].put(Task(self.time))

    def generateFederates(self, elements):
        # elist = elements.split(' ')
        elementgroups = []
        for e in elements:
            elementgroups.append(re.search(r'\b(\d+)\.(\w+)@(\w+\d).+\b', e).groups())
        fedset = sorted(list(set([e[0] for e in elementgroups])))
        # print elementgroups
        print fedset
        self.federates = [FederateLite(name = 'F'+i) for i in fedset]
        for element in elementgroups:
            index = fedset.index(element[0])
            self.federates[index].addElement(element[1], element[2])

    def getElements(self):
        elements = []
        for f in self.federates:
            elements += f.getElements()[:]

        return elements









