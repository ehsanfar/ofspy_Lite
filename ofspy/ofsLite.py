import logging

from .game import Game
from .simulator import Simulator
from .auctioneer import Auctioneer
from .contextLite import ContextLite


class OFSL(object):
    def __init__(self, elements, numPlayers,
                 numTurns, seed, ops, fops):

        self.context = ContextLite()

        self.time = 0
        self.initTime = 0
        self.maxTime = numTurns
        self.elements = elements
        # print "OFSL elements:", elements

        self.context.init(self)
        self.execute()


    def execute(self):
        """
        Executes an OFS.
        @return: L{list}
        """
        self.time = self.initTime
        for i in range(self.initTime, self.maxTime):
            self.time += 1
            self.context.ticktock(self)

        self.context.Graph.drawGraphs()
