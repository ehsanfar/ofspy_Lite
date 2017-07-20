import re
from collections import defaultdict
from .bundle import PathBundle
import itertools

class Auction():
    def __init__(self, auctioneer, time, taskslist):
        self.auctioneer = auctioneer
        self.tasklist = taskslist
        self.time = time
        self.pathlist = []
        self.taskPathDict = defaultdict(list) #{t.taskid: [] for t in taskslist}
        self.taskDict = {t.taskid: t for t in taskslist}
        self.compatibleBundles = []
        self.bestPathBundle = None


    def inquirePrice(self):
        federateBundleDict = {}
        seen = set([])
        seen_add = seen.add
        elementlist = [t.elementOwner for t in self.tasklist]
        elementset = [e for e in elementlist if e.name not in seen or seen_add(e.name)]
        federatelist = [e.federateOwner for e in elementset]
        seen = set([])
        seen_add = seen.add
        federateset = [f for f in federatelist if f.name not in seen or seen_add(f.name)]


        self.pathlist = [e.elementG.orderPathDict[self.time%6] for e in elementset]
        self.pathlist = [e for l in self.pathlist for e in l]
        # print("pathlist:", self.pathlist)
        for path in self.pathlist:
            ownername = path.elementOwner.federateOwner.name
            linkbids = []
            for link in path.linklist:
                fname = re.search(r'.+\.(F\d)\..+', link[1]).group(1)
                if fname == ownername:
                    cost = 0.
                else:
                    cost = self.auctioneer.costSGLDict[fname] if 'GS' in link[1] else self.auctioneer.costISLDict[fname]

                linkbids.append(cost)
            path.updateBid(linkbids)
            # print("all tasks:", [t.taskid for t in self.tasklist])
            for taskid in [t.taskid for t in self.tasklist]:

                if self.taskDict[taskid].elementOwner.name == path.elementOwner.name:
                    self.taskPathDict[taskid].append(path)


    def findBestBundle(self, compatiblebundles = []):
        if compatiblebundles:
            possible_bundles = compatiblebundles
        else:
            if self.compatibleBundles:
                possible_bundles = self.compatibleBundles
            else:
                self.findCompatiblePaths()
                possible_bundles = self.compatibleBundles

        if not possible_bundles:
            # self.bestPathBundle = None
            return False

        # print("length of compatible bundles:", len(self.compatibleBundles))

        path_bundle_cost = [b.bundleCost for b in possible_bundles]
        path_bundle_revenue = [b.bundleRevenue for b in possible_bundles]
        path_bundle_profit = [x-y for (x,y) in zip(path_bundle_revenue, path_bundle_cost)]
        # path_bundle_length = [b.length for b in possible_bundles]
        # print("pathbundle cost:", path_bundle_cost)
        # sortedcost = sorted(list(zip(path_bundle_cost, path_bundle_length)))
        # print("sorted cost:", sortedcost)
        sorted_revenue = sorted(list(zip(path_bundle_profit, possible_bundles)), reverse = True)
        # print("sorted revenue:", [(x, [p.nodelist for p in y.pathlist]) for x,y in sorted_revenue[:1]])
        self.bestPathBundle = sorted_revenue[0][1]
        # print("best path bundle:", self.bestPathBundle)
        for path in self.bestPathBundle.pathlist:
            path(next((task for task in self.tasklist if task.elementOwner.name == path.elementOwner.name)))
            path.task.updatePath(path)
            # path.updateTime()
            timelink = list(zip([path.task.initTime + dt for dt in path.deltatimelist], path.linklist))
            for time, link in timelink:
                # print(time, link)
                # print(defaultdict)
                self.auctioneer.updateTimeLinks(time, link)
        return True

    def findCompatiblePaths(self):
        # print("Compatible paths: tasks:", [(t, len(p)) for t, p in self.taskPathDict.items()])
        all_paths = list(self.taskPathDict.items())
        # print("Update compatible bundles: all paths:", all_paths)
        # print("All paths:", self.pathdict)
        taskpathgenerator = self.uniquePermutations(all_paths)
        # print("find compatible, length of products:", len(taskpathgenerator))
        possible_bundles = []
        for taskids, paths in taskpathgenerator:
            print("tasks id:", taskids, len(paths))
            if self.checkPathCombinations(paths):
                possible_bundles.append(PathBundle(tuple([self.taskDict[id] for id in taskids]), paths))
        # possible_bundles = [PathBundle([self.taskDict[id] for id in taskids], paths) for taskids, paths in taskpathgenerator if self.checkPathCombinations(paths)]
        # print
        # print("Auctioneer: possible path combinations:", [p.pathlist for p in possible_bundles])
        print("Length of possible bundles:", len(possible_bundles))
        # print([t.length for t in possible_bundles])
        self.compatibleBundles = possible_bundles
        # return possible_bundles

    def checkPathCombinations(self, plist):
        self.auctioneer.timeOccupiedLinkDict = {t: v for t, v in self.auctioneer.timeOccupiedLinkDict.items() if t>=self.time}
        # print("time:", self.time)
        # print("Check compatible: ", self.auctioneer.timeOccupiedLinkDict.keys())
        alledges = set([a for alllinks in self.auctioneer.timeOccupiedLinkDict.values() for a in alllinks])
        # print("check path combination:", [p.nodelist for p in pathlist])
        for path in plist:
            newlinks = set(path.linklist)
            # print("new edges:", newedges)
            intersection = alledges.intersection(newlinks)
            # print("intersection:", intersection)
            if intersection:
                # print(False)
                return False

            alledges = alledges.union(newlinks)
        # print(True)
        return True

    def uniquePermutations(self, taskpathlist):
        # print("taskpathlist:", taskpathlist)
        # print("uniquePermulations:", [[p.nodelist for p in pathlist] for pathlist in taskpathlist])
        taskpathlist = [tp for tp in taskpathlist if tp[1]]
        ntasks = len(taskpathlist)
        permutations = []
        combinations =  []
        for n in range(1,ntasks+1):
            tempcombinations = itertools.combinations(range(ntasks), n)
            combinations += list(tempcombinations)

        for c in combinations:
            tasks = [taskpathlist[i][0] for i in c]
            paths = [taskpathlist[i][1] for i in c]
            # print("newlist:", newlist)
            pathproducts = itertools.product(*paths)
            # print("Permutations:", [p.nodelist for p in list(tempproducts)])
            for paths in pathproducts:
                yield tasks, paths
        # print("Unique products:", )

        #     tempdict = self.updatePathFederateBundleDict(path)
        #     # print("Auctioneer: path edge dict:", [(a, bundle.edgelist) for (a,bundle) in tempdict.items()])
        #     federateBundleDict = self.setDict2Dict(federateBundleDict, tempdict)
        #
        # # print("auctioneer: federateBundleDict:", federateBundleDict)
        # # print("Auctioneer: federate and bundles:", [(f, [b.edgelist for b in bundles]) for (f,bundles) in federateBundleDict.items()])
        # self.bundleBidDict = {}
        # for fed, bundleset in federateBundleDict.items():
        #     bundlelist = list(bundleset)
        #     # print("Federate:", fed)
        #     # print("bundle list:", edgebundlelist)
        #     # print("Inquireprice: bundle list federates:", [[(self.nodeFederateDict[x].name, self.nodeFederateDict[y].name) for (x,y) in bundle.edgelist] for bundle in edgebundlelist])
        #     # print("Auctioneer: fed and bundleset", fed, [b.edgelist for b in edgebundlelist])
        #     tempdict = self.namefederatedict[fed].getBundleBid(bundlelist)
        #     # print("Auctioneer: asker federate protocol cost:", [(b.federateAsker.name, fed, c) for (b,c) in tempdict.items()])
        #
        #     for b in tempdict:
        #         assert b not in self.bundleBidDict
        #         self.bundleBidDict[b] = tempdict[b]
        #
        #     # bundleBidDict = {x: y for x,y in zip(edgebundlelist, costlist)}
        # self.updateBundleBid()
        # self.updateBundles()
        # self.updateCompatibleBundles()