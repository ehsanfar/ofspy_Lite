import socket
print(socket.gethostbyname("localhost"))
import argparse
import itertools
import logging
import pymongo
# from scoop import futures
import sys, os
import re
import random

# add ofspy to system path
sys.path.append(os.path.abspath('..'))

db = None  # lazy-load if required

from ofspy.ofsLite import OFSL
import json



def execute(dbHost, dbPort, start, stop, design, numPlayers, numTurns, fops, capacity):
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
    executions = [(dbHost, dbPort,
                   [e for e in elements.split(' ') if e != ''],
                   numPlayers, numTurns, seed, fops, capacity)
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

def queryCase(dbHost, dbPort, elements, numPlayers, numTurns, seed, fops, capacity):
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
    experiment = "Storage Penalty"
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
             u'numPlayers': numPlayers,
             u'numTurns': numTurns,
             u'seed': seed,
             u'capacity': capacity,
             }

    doc = None
    if dbName is not None:
        doc = db[dbName].find_one(query)
    if doc is None:
        db.results.remove(query) #this is temporary, should be removed afterwards
        doc = db.results.find_one(query)
        if doc:
            # print("Found in DB,elements, storage, sgl, isl, results: ")
            print([len(doc['elementlist'])]+[doc[k] for k in ['fops', 'capacity', 'results']])
        if doc is None:
            results = executeCase(elements, numPlayers, numTurns, seed, fops, capacity)

            doc = {u'experiment': experiment,
                   u'elementlist': ' '.join(elements),
                   u'fops': fops,
                   u'numPlayers': numPlayers,
                   u'numTurns': numTurns,
                   u'seed': seed,
                   u'capacity': capacity,
                   u'results': json.dumps(results),
                    }
            # print("Not Found in DB", doc['results'])
            # print("Not in DB,elements, storage, sgl, isl, results: ")
            print([len(doc['elementlist'])] + [doc[k] for k in ['fops', 'capacity','results']])
            db.results.insert_one(doc)

        if dbName is not None:
            db[dbName].insert_one(doc)

    return [tuple(result) for result in doc[u'results']]


def executeCase(elements, numPlayers, numTurns, seed, fops, capacity):
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
    ofsl = OFSL(elements=elements, numPlayers=numPlayers, numTurns=numTurns, seed=seed, fops=fops, capacity = capacity)
    return ofsl.execute()


def fopsGen(costrange, storange, numplayers):
    # costSGLList = list(range(0, 1001, 200))
    # # costISLList = [c/2. for c in costSGLList]
    # storagePenalty = list(range(0, 1001, 200))+[-1]
    for sgl in costrange:
        for s in storange:
            yield (numplayers-1)*["x%d,%d,%d"%(sgl, sgl, s)]+["x%d,%d,%d"%(sgl, sgl, -2)]

def generateFops(costrange, storange):
    fops = []
    for cost in costrange:
        costsgl = cost
        costisl = cost

        for sto in storange:
            stopen = sto
            for sto2 in storange:
                stopen2 = sto2
                yield ["x%d,%d,%d" % (costsgl, costisl, stopen2), "x%d,%d,%d" % (costsgl, costisl, stopen), "x%d,%d,%d" % (costsgl, costisl, stopen)]

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description="This program runs an OFS experiment.")
    # parser.add_argument('experiment', type=str, nargs='+',
    #                     help='the experiment to run: masv or bvc')
    parser.add_argument('-d', '--numTurns', type=int, default=24,
                        help='simulation duration (number of turns)')
    parser.add_argument('-p', '--numPlayers', type=int, default=None,
                        help='number of players')
    parser.add_argument('-c', '--capacity', type=int, default=2.,
                        help='satellite capacity')
    # parser.add_argument('-o', '--ops', type=str, default='d6',
    #                     help='federate operations model specification')
    parser.add_argument('-f', '--fops', type=str, default='',
                        help='federation operations model specification')
    # parser.add_argument('-l', '--logging', type=str, default='error',
    #                     choices=['debug', 'info', 'warning', 'error'],
    #                     help='logging level')
    parser.add_argument('-s', '--start', type=int, default=0,
                        help='starting random number seed')
    parser.add_argument('-t', '--stop', type=int, default=20,
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
        # "1.GroundSta@SUR1,oSGL 2.GroundSta@SUR3,oSGL 1.MediumSat@MEO3,VIS,SAR,oSGL,oISL  2.MediumSat@MEO5,VIS,SAR,oSGL,oISL",
        "1.Sat@MEO6 1.Sat@MEO4 2.Sat@MEO2 2.Sat@MEO1 1.GroundSta@SUR1 2.GroundSta@SUR4",
        "1.Sat@MEO6 1.Sat@MEO5 1.Sat@MEO4 2.Sat@MEO3 2.Sat@MEO2 2.Sat@MEO1 1.GroundSta@SUR1 2.GroundSta@SUR4",
        "1.Sat@LEO6 1.Sat@MEO5 1.Sat@MEO4 2.Sat@MEO3 2.Sat@MEO2 2.Sat@MEO1 1.GroundSta@SUR1 2.GroundSta@SUR4",
        "1.GroundSta@SUR%d 2.GroundSta@SUR%d 3.GroundSta@SUR%d 1.Sat@MEO%d 1.Sat@MEO%d 2.Sat@LEO%d 2.Sat@MEO%d 3.Sat@LEO%d 3.Sat@MEO%d"%(1,4,5,1,3,6,4,5,2),
        # "1.GroundSta@SUR%d 2.GroundSta@SUR%d 3.GroundSta@SUR%d 1.Sat@MEO%d 1.Sat@MEO%d 1.Sat@MEO%d 2.Sat@MEO%d 2.Sat@MEO%d 2.Sat@MEO%d 3.Sat@MEO%d 3.Sat@MEO%d 3.Sat@MEO%d"%(1,3,5,1,3,6,3,5,2,5,1,4),
         # "1.GroundSta@SUR%d,oSGL 2.GroundSta@SUR%d,oSGL 3.GroundSta@SUR%d,oSGL 1.SmallSat@MEO%d,oSGL,oISL 1.MediumSat@MEO%d,VIS,SAR,oSGL,oISL 1.LargeSat@MEO%d,VIS,SAR,DAT,oSGL,oISL 2.SmallSat@MEO%d,oSGL,oISL 2.MediumSat@MEO%d,VIS,SAR,oSGL,oISL 2.LargeSat@MEO%d,VIS,SAR,DAT,oSGL,oISL 3.SmallSat@MEO%d,oSGL,oISL 3.MediumSat@MEO%d,VIS,SAR,oSGL,oISL 3.LargeSat@MEO%d,VIS,SAR,DAT,oSGL,oISL"%(1,3,5,1,3,6,3,5,2,5,1,4),
        # "1.GroundSta@SUR%d,oSGL 2.GroundSta@SUR%d,oSGL 3.GroundSta@SUR%d,oSGL 1.MediumSat@MEO%d,VIS,oSGL,oISL 1.MediumSat@MEO%d,VIS,oSGL,oISL 1.LargeSat@MEO%d,VIS,SAR,DAT,oSGL,oISL 2.MediumSat@MEO%d,VIS,oSGL,oISL 2.MediumSat@MEO%d,VIS,oSGL,oISL 2.LargeSat@MEO%d,VIS,SAR,DAT,oSGL,oISL 3.MediumSat@MEO%d,VIS,oSGL,oISL 3.MediumSat@MEO%d,VIS,oSGL,oISL 3.LargeSat@MEO%d,VIS,SAR,DAT,oSGL,oISL"%(1,3,5,1,3,6,3,5,2,5,1,4),
        # "1.GroundSta@SUR%d,oSGL 2.GroundSta@SUR%d,oSGL 3.GroundSta@SUR%d,oSGL 1.MediumSat@MEO%d,VIS,oSGL,oISL 1.MediumSat@MEO%d,VIS,DAT,oSGL,oISL 1.LargeSat@MEO%d,VIS,SAR,DAT,oSGL,oISL 2.MediumSat@MEO%d,VIS,oSGL,oISL 2.MediumSat@MEO%d,VIS,DAT,oSGL,oISL 2.LargeSat@MEO%d,VIS,SAR,DAT,oSGL,oISL 3.MediumSat@MEO%d,VIS,oSGL,oISL 3.MediumSat@MEO%d,VIS,DAT,oSGL,oISL 3.LargeSat@MEO%d,VIS,SAR,DAT,oSGL,oISL"%(1,3,5,1,3,6,3,5,2,5,1,4),
        # "1.GroundSta@SUR%d,oSGL 2.GroundSta@SUR%d,oSGL 3.GroundSta@SUR%d,oSGL 1.MediumSat@MEO%d,VIS,SAR,oSGL,oISL 1.MediumSat@MEO%d,VIS,SAR,oSGL,oISL 1.LargeSat@MEO%d,VIS,SAR,DAT,oSGL,oISL 2.MediumSat@MEO%d,VIS,SAR,oSGL,oISL 2.MediumSat@MEO%d,VIS,SAR,oSGL,oISL 2.LargeSat@MEO%d,VIS,SAR,DAT,oSGL,oISL 3.MediumSat@MEO%d,VIS,SAR,oSGL,oISL 3.MediumSat@MEO%d,VIS,SAR,oSGL,oISL 3.LargeSat@MEO%d,VIS,SAR,DAT,oSGL,oISL"%(1,3,5,1,3,6,3,5,2,5,1,4),
    )
    experiment = 'auctioneer'
    # hardcoded_designs = list(hardcoded_designs)
    # random.shuffle(hardcoded_designs)
    for design in hardcoded_designs:
        print('')
        # print design
        if '4.' in design:
            numPlayers = 4
        elif '3.' in design:
            numPlayers = 3
        else:
            numPlayers = 2

        args.stop = args.start + 1
        argsdict = vars(args)
        argsdict['design'] = [design]
        # argsdict.pop('logging')
        # argsdict.pop('dbName')

        costrange = list(range(200, 301, 200))
        storange = list(range(200, 301, 200))
        for fops in fopsGen(costrange, storange, numPlayers):
            # print(fops)
            # print(argsdict)
            argsdict['fops'] = json.dumps(fops)

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
