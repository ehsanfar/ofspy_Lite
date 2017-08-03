import socket
print(socket.gethostbyname("localhost"))
import argparse
import itertools
import logging
import pymongo
# from scoop import futures
import sys, os
import re
# import random

# add ofspy to system path
sys.path.append(os.path.abspath('..'))

db = None  # lazy-load if required

from ofspy.ofsLite import OFSL
import json



def execute(dbHost, dbPort, start, stop, design, numPlayers, numTurns, fops, capacity, links):
    executions = [(dbHost, dbPort,
                   [e for e in design.split(' ') if e != ''],
                   numPlayers, numTurns, seed, fops, capacity, links)
                  for seed in range(start, stop)]
    numComplete = 0.0
    logging.info('Executing {} design with seeds from {} to {} for {} total executions.'
                 .format(len(design), start, stop, len(executions)))
    # map(queryCase, executions)
    for execution in executions:
        argslist = list(execution)
        # print(argslist)
        queryCase(*argslist)

def queryCase(dbHost, dbPort, elements, numPlayers, numTurns, seed, fops, capacity, links):
    experiment = "Design Exploration"
    global db
    dbName = None
    dbHost = "127.0.0.1"
    # dbHost = '155.246.39.17'

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
        # db.results.remove(query) #this is temporary, should be removed afterwards
        doc = db.results.find_one(query)
        if doc:
            # print("Found in DB,elements, storage, sgl, isl, results: ")
            print([len(doc['elementlist'])]+[doc[k] for k in ['fops', 'capacity', 'links','results']])
        if doc is None:
            results = executeCase(elements, numPlayers, numTurns, seed, fops, capacity, links)

            doc = {u'experiment': experiment,
                   u'elementlist': ' '.join(elements),
                   u'fops': fops,
                   u'numTurns': numTurns,
                   u'seed': seed,
                   u'capacity': capacity,
                   u'links': links,
                   u'results': json.dumps(results),
                    }
            print([len(doc['elementlist'])] + [doc[k] for k in ['fops', 'capacity', 'links', 'results']])
            db.results.insert_one(doc)

        if dbName is not None:
            db[dbName].insert_one(doc)

    return [tuple(result) for result in doc[u'results']]


def executeCase(elements, numPlayers, numTurns, seed, fops, capacity, links):
    ofsl = OFSL(elements=elements, numPlayers=numPlayers, numTurns=numTurns, seed=seed, fops=fops, capacity = capacity, links = links)
    return ofsl.execute()


# def fopsGen(numplayers):
#     yield numplayers* ["x%d,%d"%(0, s)]

def leoGen(N):
    assert N<=3
    if N == 1:
        for i in [1,2]:
            yield (i,)
    elif N == 2:
        for i in [1,2]:
            for j in [1,2]:
                yield (i, i+j)
    elif N == 3:
        for i in [1,2]:
            for j in [1,2]:
                for k in [1,2]:
                    yield (i, i+j, i+j+k)

def meoGen(N):
    combinations = itertools.combinations(range(2, 7), N - 1)
    for c in combinations:
        yield (1,) + c

def designGen():
    designset = (
        "1.GroundSta@SUR1 2.GroundSta@SUR4 1.Sat@MEO# 1.Sat@MEO# 2.Sat@MEO# 2.Sat@MEO#",
        "1.GroundSta@SUR1 2.GroundSta@SUR4 1.Sat@MEO# 1.Sat@LEO# 2.Sat@MEO# 2.Sat@LEO#",
        "1.GroundSta@SUR1 2.GroundSta@SUR4 1.Sat@GEO1 1.Sat@MEO# 1.Sat@LEO# 2.Sat@MEO# 2.Sat@LEO#",
        "1.GroundSta@SUR1 2.GroundSta@SUR4 1.Sat@MEO# 1.Sat@MEO# 1.Sat@MEO# 2.Sat@MEO# 2.Sat@MEO#",
        "1.GroundSta@SUR1 2.GroundSta@SUR4 2.Sat@GEO4 1.Sat@MEO# 1.Sat@MEO# 1.Sat@MEO# 2.Sat@MEO# 2.Sat@MEO#",
        "1.GroundSta@SUR1 2.GroundSta@SUR4 1.Sat@MEO# 1.Sat@MEO# 1.Sat@LEO# 2.Sat@MEO# 2.Sat@LEO#",
        "1.GroundSta@SUR1 2.GroundSta@SUR4 2.Sat@GEO4 1.Sat@MEO# 1.Sat@MEO# 1.Sat@LEO# 2.Sat@MEO# 2.Sat@LEO#",
        "1.GroundSta@SUR1 2.GroundSta@SUR3 3.GroundSta@SUR5 1.Sat@MEO# 2.Sat@MEO# 3.Sat@MEO#",
        "1.GroundSta@SUR1 2.GroundSta@SUR3 3.GroundSta@SUR5 1.Sat@GEO1 1.Sat@MEO# 2.Sat@MEO# 3.Sat@MEO#",
        "1.GroundSta@SUR1 2.GroundSta@SUR3 3.GroundSta@SUR5 1.Sat@MEO# 1.Sat@MEO# 2.Sat@MEO# 3.Sat@MEO#",
        "1.GroundSta@SUR1 2.GroundSta@SUR3 3.GroundSta@SUR5 2.Sat@GEO3 1.Sat@MEO# 1.Sat@MEO# 2.Sat@MEO# 3.Sat@MEO#",
        "1.GroundSta@SUR1 2.GroundSta@SUR3 3.GroundSta@SUR5 1.Sat@MEO# 1.Sat@LEO# 2.Sat@MEO# 3.Sat@MEO#",
        "1.GroundSta@SUR1 2.GroundSta@SUR3 3.GroundSta@SUR5 2.Sat@GEO3 1.Sat@MEO# 1.Sat@LEO# 2.Sat@MEO# 3.Sat@MEO#",
        "1.GroundSta@SUR1 2.GroundSta@SUR3 3.GroundSta@SUR5 1.Sat@MEO# 1.Sat@MEO# 2.Sat@MEO# 2.Sat@MEO# 3.Sat@MEO#",
        "1.GroundSta@SUR1 2.GroundSta@SUR3 3.GroundSta@SUR5 3.Sat@GEO5 1.Sat@MEO# 1.Sat@MEO# 2.Sat@MEO# 2.Sat@MEO# 3.Sat@MEO#",
        "1.GroundSta@SUR1 2.GroundSta@SUR3 3.GroundSta@SUR5 1.Sat@MEO# 1.Sat@LEO# 2.Sat@MEO# 2.Sat@LEO# 3.Sat@MEO#",
        "1.GroundSta@SUR1 2.GroundSta@SUR3 3.GroundSta@SUR5 3.Sat@GEO5 1.Sat@MEO# 1.Sat@LEO# 2.Sat@MEO# 2.Sat@LEO# 3.Sat@MEO#",
        "1.GroundSta@SUR1 2.GroundSta@SUR3 3.GroundSta@SUR5 1.Sat@MEO# 1.Sat@MEO# 2.Sat@MEO# 2.Sat@MEO# 3.Sat@MEO# 3.Sat@MEO#",
        "1.GroundSta@SUR1 2.GroundSta@SUR3 3.GroundSta@SUR5 1.Sat@GEO1 1.Sat@MEO# 1.Sat@MEO# 2.Sat@MEO# 2.Sat@MEO# 3.Sat@MEO# 3.Sat@MEO#",
        "1.GroundSta@SUR1 2.GroundSta@SUR3 3.GroundSta@SUR5 1.Sat@MEO# 1.Sat@LEO# 2.Sat@MEO# 2.Sat@LEO# 3.Sat@MEO# 3.Sat@LEO#",
        "1.GroundSta@SUR1 2.GroundSta@SUR3 3.GroundSta@SUR5 1.Sat@GEO1 1.Sat@MEO# 1.Sat@LEO# 2.Sat@MEO# 2.Sat@LEO# 3.Sat@MEO# 3.Sat@LEO#"
    )
    for des in reversed(designset):
        # print(des)
        elements = des.split()
        meoelements = [e for e in elements if 'MEO' in e]
        leoelements = [e for e in elements if 'LEO' in e]
        # print(meoelements, leoelements)
        otherelements = [e for e in elements if e not in meoelements and e not in leoelements]
        for meocomb in meoGen(len(meoelements)):
            # print("meo:", meocomb)
            # print(list(zip(meoelements, meocomb)))
            meoelements = [meo[:-1]+str(c) for meo, c in zip(meoelements, meocomb)]
            if leoelements:
                for leocomb in leoGen(len(leoelements)):
                    # print("meo leo:", meocomb, leocomb)
                    leoelements = [leo[:-1] + str(c) for leo, c in zip(leoelements, leocomb)]
                    yield ' '.join(otherelements + meoelements + leoelements)
            else:
                yield ' '.join(otherelements + meoelements)

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
    parser.add_argument('-t', '--stop', type=int, default=20,
                        help='stopping random number seed')
    parser.add_argument('--dbHost', type=str, default=None,
                        help='database host')
    parser.add_argument('--dbPort', type=int, default=27017,
                        help='database port')

    args = parser.parse_args()

        # count number of players

    numPlayers = args.numPlayers if 'numPlayers' in args else 2

    experiment = 'auctioneer'
    j = 0
    for design in designGen():
        j += 1
        print(j, design)
        # print design
        if '4.' in design:
            numPlayers = 4
        elif '3.' in design:
            numPlayers = 3
        else:
            numPlayers = 2

        args.stop = args.start + 1
        argsdict = vars(args)
        argsdict['design'] = design

        argsdict['fops'] = json.dumps(numPlayers* ["x%d,%d"%(600, 800)])
        for capacity in [1,2]:
            for links in [1,2]:
                argsdict['capacity'] = capacity
                argsdict['links'] = links
                execute(**argsdict)

