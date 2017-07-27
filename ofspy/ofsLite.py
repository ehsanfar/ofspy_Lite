
from .contextLite import ContextLite
import re
import json
import matplotlib.pyplot as plt
import time


class OFSL(object):
    def __init__(self, elements, numPlayers,
                 numTurns, seed, fops, capacity, links):

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
        self.links = links

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

        # print("number of finished tasks:", len(self.context.pickeduptasks))
        # print("total cash of task values:", self.context.totalcash)
        # print("sum of cash of federates:", sum([f.cash for f in self.context.federates]))
        #
        # if not plt.fignum_exists(1):
        #     plt.figure(1)
        #     plt.ion()
        #     plt.show()
        #
        # plt.clf()
        figs = []
        for i, f in enumerate(self.context.federates):
            if not plt.fignum_exists(i):
                figs.append(plt.figure(i))
                plt.ion()
                plt.show()

            plt.clf()
            if f.storagePenalty == -2:
                actionlist = f.qlearner.actionlist
        #
                plt.plot(actionlist)
                plt.draw()
                plt.savefig("Evolution_%d_%s.png" % (sum(self.costSGL)/float(len(self.costSGL)), f.name), bbox_inches='tight')

        for f in figs:
            plt.close(f)

                # plt.waitforbuttonpress()

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







