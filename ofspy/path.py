from .bundle import EdgeBundle
from .generalFunctions import *

class Path():
    def __init__(self, element, nodelist):
        self.nodelist = nodelist
        self.linklist = convertPath2Edge(nodelist)
        self.elementOwner = element
        self.elementlist = [element.federateOwner.context.nodeElementDict[n[:-2]] for n in nodelist]
        self.deltatimelist = self.updateDeltaTime()
        self.deltatime = max(self.deltatimelist)
        # self.timelist = []
        # self.federates = []
        # self.federateCost = {}
        # self.federatePrice = {}
        # self.federateBundleDict = {}
        # self.edgebundles = []
        self.task = None
        self.linkbidlist = []
        self.pathBid = None
        self.pathPrice = None

    def __call__(self, task):
        self.task = task

    def updateDeltaTime(self):
        orderlist = [int(n[-1]) for n in self.nodelist]
        time = 0 #self.elementOwner.federateOwner.context.time
        # print(orderlist, time)
        # assert orderlist[0] == time%6
        timelist = [time]
        for i, o in enumerate(orderlist):
            if i > 0:
                timelist.append(timelist[-1] + 1 if o != orderlist[i - 1] else timelist[-1])

        # print(timelist)
        # print(orderlist)
        # assert all([o == b%6 for o,b in zip(orderlist, timelist)])
        return timelist

    # def updateValues(self):
    #     bid_list = [b.bid for b in self.edgebundles]
    #     price_list = [b.price for b in self.edgebundles]
    #     # print("Path: nodelist and costlist:", self.nodelist, bid_list)
    #     if all(isinstance(c, float) or isinstance(c, int) for c in bid_list):
    #         self.pathBid = sum(bid_list)
    #         self.pathPrice = sum(price_list)
    #     else:
    #         self.pathBid = None
    #         self.pathPrice = None
    #     # print("update pathBid:", self.nodelist, self.pathBid)
    def updateBid(self, linkbids):
        self.linkbidlist = linkbids
        self.pathPrice = self.pathBid = sum(linkbids)

    def updatePrice(self, price):
        self.pathPrice = price

    def updateBundles(self, federatebundledict):
        self.federateBundleDict = federatebundledict
        self.edgebundles = list(federatebundledict.values())

    def getPathBid(self):
        if self.pathBid is None:
            self.updateValues()
        return self.pathBid

    def getPathPrice(self):
        return self.pathPrice

    def getNodeList(self):
        return self.nodelist

    def getFederateBundle(self):
        return self.federateEdge

    def __eq__(self, other):
        return tuple(self.nodelist) == tuple(other.nodelist)

    def __lt__(self, other):
        if len(self.nodelist) != len(other.nodelist):
            return len(self.nodelist) < len(other.nodelist)
        else:
            return self.nodelist < other.nodelist

    def __hash__(self):
        return hash(tuple(len(self.nodelist), self.nodelist))


