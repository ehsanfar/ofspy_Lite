
class Task():
    def __init__(self, time, value = 1000, computational = 1., expirationtime = 5, datasize = 1.):
        """
        @param demand: the demand for this contract
        @type demand: L{Demand}
        """
        self.value = value
        self.computationresource = computational
        self.datasize = datasize
        self.expirationtime = expirationtime
        self.duration = 2
        self.elapsedTime = 0
        self._initTime = time
        self.nextstop = None
        self.federateOwner = None

    def getValue(self, time):
        """
        Gets the current value of this contract.
        @return: L{float}
        """
        self.elapsedTime = time - self._initTime
        revisedvalue = self.value if self.elapsedTime<=self.duration else 0. if self.elapsedTime>self.expirationtime else self.value*(1. - (self.elapsedTime-self.duration)/(2.*(self.expirationtime-self.duration)))
        return revisedvalue

    def assignTask(self, federate):
        self.federateOwner = federate


