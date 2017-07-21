import re
from .elementLite import Satellite, GroundStation


class FederateLite():
    def __init__(self, name, context, initialCash=0, costSGL = 200., costISL = 100., storagePenalty = -1):
        """
        @param name: the name of this federate
        @type name: L{str}
        @param initialCash: the initial cash for this federate
        @type initialCash: L{float}
        @param elementlist: the elementlist controlled by this federate
        @type elementlist: L{list}
        @param contracts: the contracts owned by this federate
        @type contracts: L{list}
        @param operations: the operations model of this federate
        @type operations: L{Operations}
        """
        self.context = context
        self.name = name
        self.initialCash = initialCash
        self.cash = self.initialCash
        self.elements = []
        self.satellites = []
        self.stations = []
        # self.operation = operation
        self.costDic = {'oSGL': costSGL, 'oISL': costISL}
        self.storagePenalty = storagePenalty
        self.tasks = {}
        self.transcounter = 0
        self.transrevenue = 0.
        self.time = context.time

        self.taskduration  = {i: 2. for i in range(1,7)}
        self.taskvalue = {i: 500. for i in range(1,7)}
        self.taskcounter = {i: 0 for i in range(1,7)}
        self.pickupOpportunities = 0

        self.activeTasks = set([])
        self.supperGraph = None
        self.pickupProbability = context.pickupProbability
        self.uniqueBundles = []
        self.nodeElementDict = {}

    def getElements(self):
        """
        Gets the elementlist controlled by this controller.
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
        # print "federete tick tock"
        self.time = time
        for element in self.elements:
            element.ticktock()

    def setCost(self, protocol, cost):
        self.costDic[protocol] = cost

    def getCost(self, protocol, federate = None):
        # print(self.name, federate.name, self.name == federate.name, self.costDic[protocol])
        if federate and self.name == federate.name:
            return 0.

        return self.costDic[protocol]
        # key = '{}-{}'.format(federate, protocol)
        # return self.costDic[protocol] if key not in self.costDic else self.costDic[key]

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

    def getStorageCostList(self, taskvaluelist, section):
        # print("federate storage penalty:", self.storagePenalty)
        if self.storagePenalty>=0:
            return 6*[self.storagePenalty]

        assert section in range(1, 7)
        storagecostlist = []
        temptime = self.time
        # print("storage cost pickup probability:", self.pickupProbability)
        for i in range(1, 7):
            # print(i, section, len(self.taskduration), len(self.taskvalue),len(taskvaluelist))
            storagecostlist.append(self.pickupProbability*(self.taskvalue[section]/self.taskduration[section]) + taskvaluelist[i-1] - taskvaluelist[min(i, 5)])
            temptime += 1
            section = section%6+1

        # print("storage cost:", [int(e) for e in storagecostlist])
        return storagecostlist

    def discardTask(self):
        for e in self.elements:
            for stask in e.savedtasks:
                if stask.getValue(self.time)<=0:
                    self.defaultTask(self, stask)

    def reportPickup(self, task):
        self.activeTasks.add(task)

    def finishTask(self, task):
        path = task.path
        taskvalue = task.getValue(self.time) - path.getPathPrice()
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
        # print("finishtask: pickup opp and task counter:", sum(list(self.taskcounter.values())), self.pickupOpportunities)
        self.activeTasks.remove(task)

    def defaultTask(self, task):
        # print "defaulted task:", task.taskid
        element = task.elementOwner
        element.removeSavedTask(task)
        task.pathcost = 0.
        self.finishTask(task)

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
            # print "deliver task in Federate:", element
            if element.isSpace():
                # element.updateGraph(context)
                savedtasks = element.savedTasks[:]
                for task in savedtasks:
                    # print  "time and task activation time:", self.time, task.activationTime
                    assert task.activationTime >= self.time
                    if self.time >= task.activationTime:
                        element.deliverTask(task)
                        # print "len of saved tasks:", len(element.savedTasks),
                        element.removeSavedTask(task)
                        # print len(element.savedTasks)


    def getBundleBid(self, bundlelist):
        # print("Federates: bundellist:", edgebundlelist)
        alledges = [edge for bundle in bundlelist for edge in bundle.edgelist]
        assert all([re.search(r'.+\.(F\d)\..+', tup[1]).group(1) == self.name for tup in alledges])
        # edgeAskerDict = {edge: bundle.federateAsker for bundle in edgebundlelist for edge in bundle.edgelist}
        bundlecostdict = {}
        for bundle in bundlelist:
            edgeAskerDict = {}
            asker = bundle.federateAsker

            tuplecostdict = {edge: self.getCost('oISL', asker) if self.nodeElementDict[edge[1]].isSpace() else self.getCost('oSGL', asker) for edge in alledges}

            bundlecostdict[bundle] = sum([tuplecostdict[b] for b in bundle.edgelist])

        # print("federates: bundlecst:")
        #
        # for b in bundlecostdict:
        #     print(b.federateAsker.name, self.name, bundlecostdict[b])
        return bundlecostdict

    def grantBundlePrice(self, bundle):
        keybundle = UniqueBundle(bundle)
        if keybundle in self.uniqueBundles:
            ubundle = self.uniqueBundles[self.uniqueBundles.index(keybundle)]
            opportunitycost = bundle.price
            ubundle.setGenOppCost(opportunitycost)
        else:
            self.uniqueBundles.append(keybundle)





















