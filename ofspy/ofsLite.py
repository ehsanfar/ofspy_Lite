
from .contextLite import ContextLite
import re
import json
import matplotlib.pyplot as plt
import time


class OFSL(object):
    def __init__(self, elements, numPlayers,
                 numTurns, seed, fops, capacity):

        self.context = ContextLite()

        self.time = 0
        self.initTime = 0
        self.maxTime = numTurns
        self.elements = elements
        # print("fops:", fops)
        # args = re.search('x(\d+),(\d+),([-v\d]+)', fops)
        fops = json.loads(fops)
        self.costSGL = [int(re.search('x(\d+),(\d+),([-\d]+)', f).group(1)) for f in fops]
        self.costISL = [int(re.search('x(\d+),(\d+),([-\d]+)', f).group(2)) for f in fops]
        self.storagePenalty = [int(re.search('x(\d+),(\d+),([-\d]+)', f).group(3)) for f in fops]
        self.capacity = int(capacity)

        # print "OFSL elementlist:", elementlist

        self.context.init(self)
        # results = self.execute()


    def execute(self):
        """
        Executes an OFS.
        @return: L{list}
        """
        self.time = self.initTime
        for t in range(self.initTime, self.maxTime):
            # print self.time
            self.time = t
            self.context.ticktock(self)

        if not plt.fignum_exists(1):
            plt.figure(1)
            plt.ion()
            plt.show()

        plt.clf()

        # plt.figure()
        for f in self.context.federates:
            if f.storagePenalty == -2:
                actionlist = f.qlearner.actionlist
        #
        plt.plot(actionlist)
        plt.draw()
        plt.waitforbuttonpress()

        # plt.show()
        # time.sleep(1)
        # plt.close()


        # self.context.Graph.drawGraphs()
        # for e in self.context.elementlist:
        #     print(e.name, len(e.savedTasks))

        results = []
        for f in self.context.federates:
            results.append((f.name, f.cash))
            # print("task duration and value dictionary and counter:")
            # print(f.taskduration)
            # print(f.taskvalue)
            # print(f.taskcounter)

        return sorted(results)







