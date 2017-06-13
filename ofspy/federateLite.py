
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
        self.costDic = {'oSGL': 1, 'oISL': 1}
        self.tasks = {}
        self.transcounter = 0
        self.transrevenue = 0.
        self.time = None


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


    def ticktock(self):
        """
        Ticks this federate in a simulation.
        @param sim: the simulator
        """
        for element in self.elements:
            element.ticktock()

    def setCost(self, protocol, cost):
        self.costDic[protocol] = cost

    def getCost(self, protocol, federate=None, type=None):
        if type:
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

    def discardTask(self, element, task):
        pass

    def finishTask(self, element, task):
        self.cash += task.getValue(self.time)

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




