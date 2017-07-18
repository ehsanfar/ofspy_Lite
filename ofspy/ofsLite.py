
from .contextLite import ContextLite
import re


class OFSL(object):
    def __init__(self, elements, numPlayers,
                 numTurns, seed, ops, fops):

        self.context = ContextLite()

        self.time = 0
        self.initTime = 0
        self.maxTime = numTurns
        self.elements = elements

        args = re.search('x(\d+),(\d+),([-v\d]+)', fops)
        self.costSGL = int(args.group(1))
        self.costISL = int(args.group(2))
        self.storagePenalty = int(args.group(3))

        # print "OFSL elements:", elements

        self.context.init(self)
        # results = self.execute()


    def execute(self):
        """
        Executes an OFS.
        @return: L{list}
        """
        self.time = self.initTime
        for i in range(self.initTime, self.maxTime):
            # print self.time
            self.time += 1
            self.context.ticktock(self)

        # self.context.Graph.drawGraphs()
        # for e in self.context.elements:
        #     print(e.name, len(e.savedTasks))

        results = []
        for f in self.context.federates:
            results.append((f.name, f.cash))
            # print("task duration and value dictionary and counter:")
            # print(f.taskduration)
            # print(f.taskvalue)
            # print(f.taskcounter)

        return sorted(results)







