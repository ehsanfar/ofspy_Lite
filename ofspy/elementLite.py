
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

        if task.datasize <= (self.capacity - self.contentzize):
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

    def transmitTask(self, task, pathlist = None):
        if self.isGround():
            self.saveTask(task)
            return True

        if len(pathlist)<2:
            federate = task.federateOwner
            federate.discardTask(self, task)

        task.nextstop = pathlist[1]
        received = pathlist[0].transmitTask(task, pathlist[1:])
        return received


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

    def getCapacity(self):
        return self.capacity

    def getContentsSize(self):
        return self.content

    def isGround(self):
        return False

    def isSpace(self):
        return True

    def pickupTask(self, task):
        if self.canReceive(task):
            self.queuedTasks.put(task)

    def transmit(self, task, pathlist):
        pathlist[0].transmitTask(task, pathlist[1:])

    def deliverTasks(self, pathlist):
        task = self.queuedTasks.get()
        self.transmitTask(task, pathlist)


