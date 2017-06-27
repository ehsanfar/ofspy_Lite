
class Task():
    def __init__(self, time, id = None, value = 1000, computational = 1., expirationtime = 5, datasize = 1.):
        """
        @param demand: the demand for this contract
        @type demand: L{Demand}
        """
        self.taskid = id
        self.value = value
        self.computationresource = computational
        self.datasize = datasize
        self.expirationtime = expirationtime
        self.duration = 2
        self.elapsedTime = 0
        self.initTime = time
        self.nextstop = None
        self.federateOwner = None
        self.initSection = None

    def getValue(self, time):
        """
        Gets the current value of this contract.
        @return: L{float}
        """
        # print time, self.initTime
        self.elapsedTime = time - self.initTime
        revisedvalue = self.value if self.elapsedTime<=self.duration else 0. if self.elapsedTime>self.expirationtime else self.value*(1. - (self.elapsedTime-self.duration)/(2.*(self.expirationtime-self.duration)))
        return revisedvalue

    def assignTask(self, federate):
        self.federateOwner = federate

    def setID(self, id):
        self.taskid = id

    def getID(self):
        return self.taskid

    def setSection(self, loc):
        self.initSection = loc

    def getSection(self):
        return self.initSection



