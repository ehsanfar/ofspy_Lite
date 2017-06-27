
"""
Elements classes.
"""
import re
import Queue

class Element():
    def __init__(self, federate, name, location, cost=0):
        self.name = name
        self.location = re.search('(\w+)(\d)', location).group(1)
        self.section = int(re.search('(\w+)(\d)', location).group(2))
        self.designCost = cost
        self.federateOwner = federate
        self.savedTasks = []

    def getOwner(self):
        return self.federateOwner

    def getLocation(self):
        return str(self.location)+str(self.section)

    def getSection(self):
        return self.section

    def getSectionAt(self, time):
        if 'LEO' in self.location:
            return (time*2+self.section-1)%6+1

        elif 'MEO' in self.location:
            return (time+self.section-1)%6+1

        else:
            return self.section

    def ticktock(self):
        if 'LEO' in self.location:
            self.section = (self.section + 2 - 1)%6 + 1
        elif 'MEO' in self.location:
            self.section = (self.section + 1 - 1)%6 + 1


    def getDesignCost(self):
        return self.designCost


    def canReceive(self, task):
        if self.isGround():
            return True

        # print "capacity and content:", self.capacity, self.content
        if task.datasize <= (self.capacity - self.content):
            return True

        return False

    def canTransmit(self, rxElement, task):
        return rxElement.couldReceive(self, task)


    def saveTask(self, task, nextstop = None):
        if self.isGround():
            self.savedTasks.append(task)
            task.federateOwner.finishTask(self, task)
            return True

        if (nextstop or task.nextstop) and self.canSave(task):
            task.nextstop = nextstop
            self.savedTasks.append(task)
            self.content += task.datasize
            return True

        task.federateOwner.discardTask(self, task)
        return False

    def transmitTask(self, task, pathiter):
        # print self.name, task.taskid
        if self.isGround():
            self.saveTask(task)
            return True

        # assert len(pathlist)>=1
        # if len(pathlist)<2:
        #     federate = task.federateOwner
        #     federate.discardTask(self, task)
        task.nextstop = nextstop = next(pathiter)

        received = nextstop.transmitTask(task, pathiter)
        return received

    def isGEO(self):
        if self.isSpace() and 'GEO' in self.location:
            return True

        return False

    def pickupTask(self, currentTasks, taskid):
        # print "elementLite - taskid:", self.name, taskid, self.section
        if self.isSpace() and not self.isGEO():
            # print "it is satellite"
            # print "current tasks:", currentTasks
            # print self.section
            # print currentTasks[self.section].qsize()
            # assert not currentTasks[self.section].empty()
            nextTask = currentTasks[self.section].get()
            # print nextTask
            # print "task time:", nextTask.initTime, nextTask.federateOwner
            if self.canReceive(nextTask):
                nextTask.setID(taskid)
                nextTask.assignTask(self.federateOwner)
                nextTask.setSection(self.section)
                self.queuedTasks.put(nextTask)
                self.federateOwner.reportPickup(nextTask)
                return True

        return False


class GroundStation(Element):
    def __init__(self, federate, name, location, cost):
        Element.__init__(self, federate, name, location, cost)

    def isGround(self):
        return True

    def isSpace(self):
        return False




class Satellite(Element):
    def __init__(self, federate, name, location, cost, capacity=1.):
        Element.__init__(self, federate, name, location, cost)
        self.capacity = capacity
        self.content = 0.
        self.queuedTasks = Queue.Queue()
        self.graph = None

    def getCapacity(self):
        return self.capacity

    def getContentsSize(self):
        return self.content

    def isGround(self):
        return False

    def isSpace(self):
        return True

    def deliverTasks(self, pathlist):
        assert not self.queuedTasks.empty()
        task = self.queuedTasks.get()
        self.transmitTask(task, iter(pathlist[1:]))



