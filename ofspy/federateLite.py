
import re

from .operationLite import OperationLite
from .elementLite import Satellite, GroundStation


class FederateLite():
    def __init__(self, name=None, initialCash=0, operation =OperationLite()):
        """
        @param name: the name of this federate
        @type name: L{str}
        @param initialCash: the initial cash for this federate
        @type initialCash: L{float}
        @param elements: the elements controlled by this federate
        @type elements: L{list}
        @param contracts: the contracts owned by this federate
        @type contracts: L{list}
        @param operations: the operations model of this federate
        @type operations: L{Operations}
        """
        self.name = name
        self.initialCash = initialCash
        self.cash = self.initialCash
        self.elements = []
        self.satellites = []
        self.stations = []
        self.operation = operation
        self.costDic = {'oSGL': 1., 'oISL': 1.}
        self.tasks = {}
        self.transcounter = 0
        self.transrevenue = 0.
        self.time = None

        self.taskduration  = {i: 1. for i in range(1,7)}
        self.taskvalue = {i: 1000. for i in range(1,7)}
        self.taskcounter = {i: 10 for i in range(1,7)}

        self.activeTasks = set([])
        self.supperGraph = None


    def getElements(self):
        """
        Gets the elements controlled by this controller.
        @return L{list}
        """
        return self.elements[:]


    def getTasks(self):
        """
        Gets the contracts controlled by this controller.
        @return L{list}
        """
        return self.tasks


    def ticktock(self, time):
        """
        Ticks this federate in a simulation.
        @param sim: the simulator
        """
        self.time = time
        for element in self.elements:
            element.ticktock()

    def setCost(self, protocol, cost):
        self.costDic[protocol] = cost

    def getCost(self, protocol, federate=None, type=None):
        if self == federate:
            return 0.
        key = '{}-{}'.format(federate, protocol)
        return self.costDic[protocol] if key not in self.costDic else self.costDic[key]

    def addTransRevenue(self, protocol, amount):
        if protocol in self.transCounter:
            self.transrevenue[protocol] += amount
            self.transcounter[protocol] += 1
        else:
            self.transrevenue[protocol] = amount
            self.transcounter[protocol] = 1

    def getTransRevenue(self):
        return self.transrevenue

    def getTransCounter(self):
        return self.transcounter

    def getStorageCostList(self, task, section):
        assert section in range(1, 7)
        storagecostlist = []
        temptime = self.time
        while task.getValue(temptime+1)>0:
            storagecostlist.append(self.taskvalue[section]/self.taskduration[section] + task.getValue(temptime+1) - task.getValue(temptime))
            temptime += 1
            section = section%6+1

        return storagecostlist

    def discardTask(self, element, task):
        pass

    def reportPickup(self, task):
        self.activeTasks.add(task)

    def finishTask(self, element, task):
        taskvalue = task.getValue(self.time)
        self.cash += taskvalue
        assert task in self.activeTasks
        section = task.getSection()
        assert self.time >= task.initTime
        duration = max(1, self.time - task.initTime)
        assert section in range(1, 7)

        # print "Finished tasks (section, taskvalue, taskduration):", section, taskvalue, duration
        self.taskduration[section] = (self.taskduration[section]*self.taskcounter[section] + duration)/(self.taskcounter[section] + 1.)
        self.taskvalue[section]  = (self.taskvalue[section]*self.taskcounter[section] + taskvalue)/(self.taskcounter[section] + 1.)
        self.taskcounter[section] += 1
        self.activeTasks.remove(task)


    def addElement(self, element, location):
        orbit, section = (re.search(r'(\w)\w+(\d)', location).group(1), int(re.search(r'(\w)\w+(\d)', location).group(2)))
        if 'Ground' in element:
            gs = GroundStation(self, 'GS.%s.%d'%(self.name, len(self.stations)+1), location, 600)
            self.elements.append(gs)
            self.stations.append(gs)

        elif 'Sat' in element:
            ss = Satellite(self, 'S%s.%s.%d'%(orbit, self.name, len(self.satellites)+1), location, 800)
            self.elements.append(ss)
            self.satellites.append(ss)

    def deliverTasks(self, context):
        for element in self.elements:
            if element.isSpace():
                element.updateGraph(context)
                # element.Graph.setGraphList(context)
                pathname = element.Graph.findcheapestpath()
                print "element and path:    ", element, pathname
                path = [next((e for e in self.elements if e.name == p)) for p in pathname]
                element.deliverTasks(path)





