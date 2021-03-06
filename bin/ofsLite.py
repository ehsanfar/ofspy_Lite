import socket
print(socket.gethostbyname("localhost"))
import argparse
import itertools
import logging
import pymongo
# from scoop import futures
import sys, os
import re
from numpy import linspace
# import random

# add ofspy to system path
sys.path.append(os.path.abspath('..'))

db = None  # lazy-load if required

from ofspy.ofsLite import OFSL
import json



def execute(dbHost, dbPort, experiment, start, stop, design, numPlayers, numTurns, fops, capacity, links):
    """
    Executes a general experiment.
    @param dbHost: the database host
    @type dbHost: L{str}
    @param dbPort: the database port
    @type dbPort: L{int}
    @param dbName: the database collection name
    @type dbName: L{str}
    @param start: the starting seed
    @type start: L{int}
    @param stop: the stopping seed
    @type stop: L{int}
    @param design: the list of designs to execute
    @type design: L{list}
    @param numPlayers: the number of players
    @type numPlayers: L{int}
    @param initialCash: the initial cash
    @type initialCash: L{int}
    @param numTurns: the number of turns
    @param numTurns: the number of turns
    @type numTurns: L{int}
    @param ops: the operations definition
    @type ops: L{str}
    @param fops: the federation operations definition
    @type fops: L{str}
    """
    # print "design:", design
    # print start, stop
    executions = [(dbHost, dbPort, experiment,
                   [e for e in elements.split(' ') if e != ''],
                   numPlayers, numTurns, seed, fops, capacity, links)
                  for (seed, elements) in itertools.product(range(start, stop), design)]
    numComplete = 0.0
    logging.info('Executing {} design with seeds from {} to {} for {} total executions.'
                 .format(len(design), start, stop, len(executions)))
    # for results in futures.map(queryCase, executions):
    # results = futures.map(queryCase, executions)
    # print(len(list(executions)))
    # print([list(e) for e in executions])
    # map(queryCase, executions)
    for execution in executions:
        argslist = list(execution)
        # print(argslist)
        queryCase(*argslist)
    # print "results :", results
    # N = len(results[0])
    # This line calculates the average of each element of each tuple for all the lists in the results, in other words assuming that each tuple of each results shows one seed of the same identity
    # print [[sum(x)/float(N) for x in zip(*l)] for l in [[l[j] for l in results] for j in range(N)]]

def queryCase(dbHost, dbPort, experiment, elements, numPlayers, numTurns, seed, fops, capacity, links):
    """
    Queries and retrieves existing results or executes an OFS simulation.
    @param dbHost: the database host
    @type dbHost: L{str}
    @param dbPort: the database port
    @type dbPort: L{int}
    @param dbName: the database collection name
    @type dbName: L{str}
    @param elements: the design specifications
    @type elements: L{list}
    @param numPlayers: the number of players
    @type numPlayers: L{int}
    @param initialCash: the initial cash
    @type initialCash: L{int}
    @param numTurns: the number of turns
    @type numTurns: L{int}
    @param seed: the random number seed
    @type seed: L{int}
    @param ops: the operations definition
    @type ops: L{str}
    @param fops: the federation operations definition
    @type fops: L{str}
    @return: L{list}
    """
    # print "elementlist:", elementlist
    # executeCase(elementlist, numPlayers, initialCash,
    #              numTurns, seed, ops, fops)
    # experiment = experiment
    global db
    dbName = None
    # dbHost = socket.gethostbyname(socket.gethostname())
    dbHost = "127.0.0.1"
    # dbHost = "155.246.119.30"
    # print dbHost, dbPort, dbName, db
    # print "fops:", fops
    # print costISL, costSGL

    if db is None and dbHost is None:
        # print "db is None adn dbHOst is None"
        return executeCase(elements, numPlayers,
                 numTurns, seed, ops, fops, capacity)
    elif db is None and dbHost is not None:
        # print "read from database"
        db = pymongo.MongoClient(dbHost, dbPort).ofs

    query = {u'experiment': experiment,
             u'elementlist': ' '.join(elements),
             u'fops': fops,
             u'numTurns': numTurns,
             u'seed': seed,
             u'capacity': capacity,
             u'links': links,
             }

    doc = None
    if dbName is not None:
        doc = db[dbName].find_one(query)
    if doc is None:
        # if '-1' in doc['fops'] or '-2' in doc['fops']:
        # db.results.remove(query) #this is temporary, should be removed afterwards
        doc = db.results.find_one(query)
        if doc:
            # print("Found in DB,elements, storage, sgl, isl, results: ")
            print([doc[k] for k in ['seed', 'elementlist', 'experiment', 'fops', 'capacity', 'links','results']])
        if doc is None:
            if '-' not in fops:
                M = 10
            else:
                M = 1

            results = executeCase(experiment, elements, numPlayers, int(numTurns/M), seed, fops, capacity, links)

            doc = {u'experiment': experiment,
                   u'elementlist': ' '.join(elements),
                   u'fops': fops,
                   u'numTurns': numTurns,
                   u'seed': seed,
                   u'capacity': capacity,
                   u'links': links,
                   u'results': json.dumps([(a,b*M) for a,b in results]),
                    }
            # print("Not Found in DB", doc['results'])
            # print("Not in DB,elements, storage, sgl, isl, results: ")
            print([doc[k] for k in ['seed', 'elementlist', 'experiment', 'fops', 'capacity', 'links', 'results']])
            db.results.insert_one(doc)

        if dbName is not None:
            db[dbName].insert_one(doc)

    return [tuple(result) for result in doc[u'results']]


def executeCase(experiment, elements, numPlayers, numTurns, seed, fops, capacity, links):
    """
    Executes an OFS simulation.
    @param elements: the design specifications
    @type elements: L{list}
    @param numPlayers: the number of players
    @type numPlayers: L{int}
    @param initialCash: the initial cash
    @type initialCash: L{int}
    @param numTurns: the number of turns
    @type numTurns: L{int}
    @param seed: the random number seed
    @type seed: L{int}
    @param ops: the operations definition
    @type ops: L{str}
    @param fops: the federation operations definition
    @type fops: L{str}
    """
    # print "ofs-exp-vs elementlist: ", elementlist
    #
    # return OFSL(elementlist=elementlist, numPlayers=numPlayers, initialCash=initialCash, numTurns=numTurns, seed=seed, ops=ops, fops=fops).execute()
    ofsl = OFSL(experiment = experiment, elements=elements, numPlayers=numPlayers, numTurns=numTurns, seed=seed, fops=fops, capacity = capacity, links = links)
    return ofsl.execute()


def fopsGenStorage(costrange, storange, numplayers):
    # costSGLList = list(range(0, 1001, 200))
    # # costISLList = [c/2. for c in costSGLList]
    # storagePenalty = list(range(0, 1001, 200))+[-1]
    # yield numplayers * ["x%d,%d" % (-2, -2)]
    for sgl in costrange:
        for s in storange:
            # yield ["x%d,%d,%d"%(sgl, sgl, -2)] + (numplayers-1)*["x%d,%d,%d"%(sgl, sgl, s)]
            yield numplayers* ["x%d,%1.2f,%d"%(sgl, s, -1)]
            # yield numplayers* ["x%d,%d,%d"%(-3, s, -1)]

        # yield numplayers * ["x%d,%d,%d" % (sgl, -1, -1)]


def fopsGenAdaptive(costrange, numplayers):
    for sgl in costrange:
        if sgl == -2:
            yield numplayers * ["x%d,%d,%d" % (sgl, -1, -1)]
            yield numplayers * ["x%d,%d,%d" % (-2, -1, 1)]
        else:
            # if sgl == -3:
            #     print(["x%d,%d,%d"%(-2, -1, -1)] + (numplayers-1)*["x%d,%d,%d"%(sgl, -1, -1)])

            for n in range(numplayers):
                fops = []
                fops.extend(n*["x%d,%d,%d"%(-2, -1, -1)])
                fops.extend(["x%d,%d,%d" % (sgl, -1, -1)])
                fops.extend((numplayers-n-1)*["x%d,%d,%d"%(-2, -1, -1)])
                # yield n*[] + ["x%d,%d,%d"%(-2, -1, -1)] + (numplayers-1)*["x%d,%d,%d"%(sgl, -1, -1)]
                yield fops

            for n in range(numplayers):
                fops = []
                fops.extend(n*["x%d,%d,%d"%(sgl, -1, -1)])
                fops.extend(["x%d,%d,%d"%(-2, -1, -1)])
                fops.extend((numplayers-n-1)*["x%d,%d,%d"%(sgl, -1, -1)])
                # yield n*[] + ["x%d,%d,%d"%(-2, -1, -1)] + (numplayers-1)*["x%d,%d,%d"%(sgl, -1, -1)]
                yield fops

            # yield 2 * ["x%d,%d,%d"%(-2, -1, -1)] + (numplayers - 2) * ["x%d,%d,%d"%(sgl, -1, -1)]
            yield numplayers * ["x%d,%d,%d" % (sgl, -1, -1)]
            yield numplayers * ["x%d,%d,%d"%(-2, -1, -1)]

        # yield 2*["x%d,%d" % (-2, -1)] + (numplayers-2)*["x%d,%d"%(sgl, -1)]

# def generateFops(costrange, storange):
#     fops = []
#     for cost in costrange:
#         costsgl = cost
#         costisl = cost
#
#         for sto in storange:
#             stopen = sto
#             for sto2 in storange:
#                 stopen2 = sto2
#                 yield ["x%d,%d,%d" % (costsgl, costisl, stopen2), "x%d,%d,%d" % (costsgl, costisl, stopen), "x%d,%d,%d" % (costsgl, costisl, stopen)]
# def fopsGenStorage(numPlayers):
#     yield numPlayers * ["x%d,%1.2f,%d" % (600, 400, -1)]
#     yield numPlayers * ["x%d,%1.2f,%d" % (600, 800, -1)]
#     yield numPlayers * ["x%d,%1.2f,%d" % (-3, 400, -1)]
#     yield numPlayers * ["x%d,%1.2f,%d" % (-3, 800, -1)]
#     for k in linspace(0., 1.99, 19):
#         yield numPlayers * ["x%d,%1.2f,%d" % (-3, -1*k, -1)]
#         yield numPlayers * ["x%d,%1.2f,%d" % (600, -1*k, -1)]

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description="This program runs an OFS experiment.")
    # parser.add_argument('-e', help = 'experiment to run', type=str, nargs='+', default= 'Adaptive'
    #                     help='the experiment to run: adaptive, auctioneer')
    parser.add_argument('-d', '--numTurns', type=int, default=2400,
                        help='simulation duration (number of turns)')
    parser.add_argument('-p', '--numPlayers', type=int, default=None,
                        help='number of players')
    parser.add_argument('-c', '--capacity', type=int, default=2.,
                        help='satellite capacity')
    parser.add_argument('-l', '--links', type=int, default=2.,
                        help='links per edge')
    # parser.add_argument('-o', '--ops', type=str, default='d6',
    #                     help='federate operations model specification')
    parser.add_argument('-f', '--fops', type=str, default='',
                        help='federation operations model specification')
    # parser.add_argument('-l', '--logging', type=str, default='error',
    #                     choices=['debug', 'info', 'warning', 'error'],
    #                     help='logging level')
    parser.add_argument('-s', '--start', type=int, default=0,
                        help='starting random number seed')
    parser.add_argument('-t', '--stop', type=int, default=30,
                        help='stopping random number seed')
    parser.add_argument('--dbHost', type=str, default=None,
                        help='database host')
    parser.add_argument('--dbPort', type=int, default=27017,
                        help='database port')

    args = parser.parse_args()

        # count number of players

    numPlayers = args.numPlayers if 'numPlayers' in args else 2

    # with open('designs.txt', 'r') as f:
    #     hardcoded_designs = f.readlines()
    #     # for l in f:
    #     #     print l
    #     #     hardcoded_designs.append(l)
    # hardcoded_designs = [x.strip() for x in hardcoded_designs]
    hardcoded_designs = (
        # "1.GroundSta@SUR1 2.GroundSta@SUR4 1.Sat@MEO1 2.Sat@MEO3 1.Sat@LEO1 2.Sat@LEO2",
        # "1.GroundSta@SUR1 2.GroundSta@SUR4 1.Sat@GEO1 1.Sat@MEO1 2.Sat@MEO3 1.Sat@LEO1 2.Sat@LEO2",
        "1.GroundSta@SUR1 2.GroundSta@SUR4 1.Sat@MEO1 1.Sat@MEO4 2.Sat@MEO5 1.Sat@LEO1 2.Sat@LEO2",
        # "1.GroundSta@SUR1 2.GroundSta@SUR4 1.Sat@MEO1 1.Sat@MEO3 1.Sat@MEO4 2.Sat@MEO5 2.Sat@MEO6",
        "1.GroundSta@SUR1 2.GroundSta@SUR4 2.Sat@GEO4 1.Sat@MEO1 1.Sat@MEO4 2.Sat@MEO5 1.Sat@LEO1 2.Sat@LEO2",
        # "1.GroundSta@SUR1 2.GroundSta@SUR3 3.GroundSta@SUR5 2.Sat@GEO3 1.Sat@MEO1 2.Sat@MEO3 3.Sat@MEO6 1.Sat@LEO2",
        "1.GroundSta@SUR1 2.GroundSta@SUR3 3.GroundSta@SUR5 1.Sat@MEO1 1.Sat@MEO2 2.Sat@MEO3 2.Sat@MEO5 3.Sat@MEO6",
        "1.GroundSta@SUR1 2.GroundSta@SUR3 3.GroundSta@SUR5 3.Sat@GEO5 1.Sat@MEO1 1.Sat@MEO2 2.Sat@MEO3 2.Sat@MEO5 3.Sat@MEO6",
        #***"1.GroundSta@SUR1 2.GroundSta@SUR3 3.GroundSta@SUR5 1.Sat@MEO1 2.Sat@MEO2 3.Sat@MEO5 1.Sat@LEO2 2.Sat@LEO4 3.Sat@LEO6",
        # "1.GroundSta@SUR1 2.GroundSta@SUR3 3.GroundSta@SUR5 1.Sat@GEO1 1.Sat@MEO1 2.Sat@MEO4 3.Sat@MEO5 2.Sat@LEO4 3.Sat@LEO6",
        "1.GroundSta@SUR1 2.GroundSta@SUR3 3.GroundSta@SUR5 1.Sat@MEO1 2.Sat@MEO2 3.Sat@MEO3 1.Sat@LEO1 2.Sat@LEO2 3.Sat@LEO3",
    )

    experiment = 'auctioneer'
    # hardcoded_designs = list(hardcoded_designs)
    # random.shuffle(hardcoded_designs)
    for design in hardcoded_designs:
        # print design
        if '4.' in design:
            numPlayers = 4
        elif '3.' in design:
            numPlayers = 3
        else:
            numPlayers = 2

        args.stop = args.start + 10
        argsdict = vars(args)
        argsdict['design'] = [design]
        # argsdict.pop('logging')
        # argsdict.pop('dbName')

        # costrange = list(range(700, 701, 100))
        # costrange = [-3]
        # costrange = [-3, 0, 1200, 600]
        # costrange = [-2]
        costrange = [-3, 600]
        storange = list([400, 800, -1])
        # for fops in reversed(list(fopsGenAdaptive(costrange, numPlayers))):
        for fops in fopsGenStorage(costrange, storange, numPlayers):
            print(fops)
            # print(argsdict)
            reres = re.search(r'x([-\d]+),([-\.\d]+),([-\d]+)', fops[0])
            sgl = int(reres.group(1))
            strg = float(reres.group(2))
            auc = int(reres.group(3))

            # argsdict['experiment'] = 'Adaptive Cost V2'
            argsdict['experiment'] = 'Storage Penalty V2'
            # if sgl == -2 :
            #     argsdict['experiment'] = 'Adaptive Cost'
            #
            # elif strg == -1 and sgl > 0:
            #     argsdict['experiment'] = 'Fixed Cost Storage Penalty'
            #
            # elif strg == -1 and sgl == -1:
            #     argsdict['experiment'] = 'Stochastic Cost Storage Penalty'
            if auc == 1:
                argsdict['experiment'] += ' Auctioneer'

            argsdict['fops'] = json.dumps(fops)
            for capacity,links in [(2,2)]:
                # for links in [1,2]:
                argsdict['capacity'] = capacity
                argsdict['links'] = links
                execute(**argsdict)

            # execute(args.dbHost, args.dbPort, None, args.start, args.stop,
            #         [design],
            #         numPlayers, args.initialCash, args.numTurns,
            #         None, fops)

        # for ops, fops in [('d6,a,1', 'x')]:#[('n', 'd6,a,1'), ('d6,a,1', 'n'), ('d6,a,1', 'x')]:#[('d6,a,1', 'x')]:#
        #     if 'x' in fops:
        #         stop = args.start + 1
        #         # costsgl = costisl = 'v'
        #         for costsgl in [a for a in range(500, 601, 200)]:# if a not in range(0, 1501,100)]:
        #             # print "cost SGL:", costsgl
        #             costisl = costsgl//2
        #             fops = "x%s,%s,6,a,1"%(str(costsgl),str(costisl))
        #             # print "fops:", fops
        #             # print "ofs-exp-vs Design:",
        #             execute(args.dbHost, args.dbPort, None, args.start, stop,
        #                 [design],
        #                 numPlayers, args.initialCash, args.numTurns,
        #                 ops, fops, experiment)
        #     else:
        #         stop = args.start + 1
        #         # print "fops:", fops
        #         execute(args.dbHost, args.dbPort, None, args.start, stop,
        #                 [design],
        #                     numPlayers, args.initialCash, args.numTurns,
        #                     ops, fops, experiment)
        # else:
        #     execute(args.dbHost, args.dbPort, None, args.start, args.stop,
        #             [' '.join(args.experiment)],
        #             numPlayers, args.initialCash, args.numTurns,
        #             args.ops, args.fops, 0, 0)
