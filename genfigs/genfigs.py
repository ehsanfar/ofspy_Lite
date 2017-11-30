import pymongo
import socket
import json
# import pandas as pd
import scipy.stats as stats
import matplotlib.pyplot as plt
import re
from collections import defaultdict, deque
import math
import numpy as np
from matplotlib.font_manager import FontProperties

hardcoded_designs = (
        "1.GroundSta@SUR1 2.GroundSta@SUR4 1.Sat@MEO1 1.Sat@MEO4 2.Sat@MEO5 1.Sat@LEO1 2.Sat@LEO2",
        "1.GroundSta@SUR1 2.GroundSta@SUR4 2.Sat@GEO4 1.Sat@MEO1 1.Sat@MEO4 2.Sat@MEO5 1.Sat@LEO1 2.Sat@LEO2",
        "1.GroundSta@SUR1 2.GroundSta@SUR3 3.GroundSta@SUR5 1.Sat@MEO1 1.Sat@MEO2 2.Sat@MEO3 2.Sat@MEO5 3.Sat@MEO6",
        "1.GroundSta@SUR1 2.GroundSta@SUR3 3.GroundSta@SUR5 3.Sat@GEO5 1.Sat@MEO1 1.Sat@MEO2 2.Sat@MEO3 2.Sat@MEO5 3.Sat@MEO6",
        # "1.GroundSta@SUR1 2.GroundSta@SUR3 3.GroundSta@SUR5 1.Sat@MEO1 2.Sat@MEO2 3.Sat@MEO5 1.Sat@LEO2 2.Sat@LEO4 3.Sat@LEO6",
        # "1.GroundSta@SUR1 2.GroundSta@SUR3 3.GroundSta@SUR5 1.Sat@GEO1 1.Sat@MEO1 2.Sat@MEO4 3.Sat@MEO5 2.Sat@LEO4 3.Sat@LEO6",
        "1.GroundSta@SUR1 2.GroundSta@SUR3 3.GroundSta@SUR5 1.Sat@MEO1 2.Sat@MEO2 3.Sat@MEO3 1.Sat@LEO1 2.Sat@LEO2 3.Sat@LEO3",
    )


design_dict = {d: i for i,d in enumerate(hardcoded_designs)}
xtickDict = {0: 'I', 1: 'II', 2: 'III', 3: 'IV', 4: 'V', 5: 'VI', 6: 'VII', 7: 'VIII', 8: 'XI', 9: 'X'}
xticklist = ['Design %s' % xtickDict[i] for i in range(len(hardcoded_designs))]
divider = 1000000

def filterInvalidDics(dictlist):
    return [dic for dic in dictlist if len(set(dic['costDictList'])) <= 2]

def findBalancedMembers(dictlist):
    return [dic for dic in dictlist if len(set(dic['costDictList'])) == 1]

def fops2costs(fops):
    costSGL, storagePenalty, auctioneer = re.search('x([-\d]+),([-\.\d]+),([-\d]+)', fops).groups()
    # print(costSGL, costISL, storagePenalty)
    return (int(costSGL), float(storagePenalty), int(auctioneer))

def fopsGen(des, test):
    # print("test:",test)
    numPlayers = 2
    if '3.' in des:
        numPlayers = 3

    if 'regular storage' in test:
        if 'stochastic' in test or 'random' in test:
            costsgl = [-3]
        else:
            costsgl = [600]

        storage = [-1, 400, 800]
        for sgl in costsgl:
            for stor in storage:
                fopslist = numPlayers*['x%d,%1.2f,%d'%(sgl, stor, -1)]
                yield fopslist
    # print("design:", des, numPlayers)

    elif 'storage' in test.lower():
        if 'stochastic' in test.lower():
            yield numPlayers * ["x%d,%1.2f,%d" % (-3, 400, -1)]
            yield numPlayers * ["x%d,%1.2f,%d" % (-3, 800, -1)]
            for k in np.linspace(0., 1.99, 19):
                yield numPlayers * ["x%d,%1.2f,%d" % (-3, -1*k, -1)]
        else:
            yield numPlayers * ["x%d,%1.2f,%d" % (600, 400, -1)]
            yield numPlayers * ["x%d,%1.2f,%d" % (600, 800, -1)]
            for k in np.linspace(0., 1.99, 19):
                yield numPlayers * ["x%d,%1.2f,%d" % (600, -1*k, -1)]

    elif 'federate adaptive' in test:
        costrange = [-3, 0, 1200, 600]
        for sgl in costrange:
            fops_adaptive = json.dumps(['x%d,%d,%d' % (-2, -1, -1)] + (numPlayers-1) * ['x%d,%d,%d' % (sgl, -1, -1)])
            fops = json.dumps(numPlayers * ['x%d,%d,%d' % (sgl, -1, -1)])
            yield (fops, fops_adaptive)

    elif 'total' in test:
        costrange = [0, 600, 1200]
        # print(costrange)
        for sgl in costrange:
            # print(sgl)
            if numPlayers == 2:
                fops_1 = ['x%d,%d,%d' % (sgl, -1, -1), 'x%d,%d,%d' % (sgl, -1, -1)]
                fops_2 = ['x%d,%d,%d' % (-2, -1, -1), 'x%d,%d,%d' % (sgl, -1, -1)]
                fops_3 = ['x%d,%d,%d' % (-2, -1, -1), 'x%d,%d,%d' % (-2, -1, -1)]
                print("new")
                yield (fops_1, fops_2, fops_3)
            elif numPlayers == 3:
                fops_1 = ['x%d,%d,%d' % (sgl, -1, -1), 'x%d,%d,%d' % (sgl, -1, -1), 'x%d,%d,%d' % (sgl, -1, -1)]
                fops_2 = ['x%d,%d,%d' % (-2, -1, -1), 'x%d,%d,%d' % (sgl, -1, -1), 'x%d,%d,%d' % (sgl, -1, -1)]
                fops_3 = ['x%d,%d,%d' % (-2, -1, -1), 'x%d,%d,%d' % (-2, -1, -1), 'x%d,%d,%d' % (sgl, -1, -1)]
                fops_4 = ['x%d,%d,%d' % (-2, -1, -1), 'x%d,%d,%d' % (-2, -1, -1), 'x%d,%d,%d' % (-2, -1, -1)]
                yield (fops_1, fops_2, fops_3, fops_4)

    elif 'auctioneer' in test:
        fops_1 = numPlayers * ['x%d,%d,%d' % (-2, -1, -1)]
        fops_2 = numPlayers * ['x%d,%d,%d' % (-2, -1, 1)]
        yield (fops_1, fops_2)



def fopsGenTotal(des):
    numPlayers = 2
    if '3.' in des:
        numPlayers = 3

    costrange = [0, 600, 1200]
    for sgl in costrange:
        if numPlayers == 2:
            fops_1 = ['x%d,%d,%d' % (sgl, -1, -1), 'x%d,%d,%d' % (sgl, -1, -1)]
            fops_2 = ['x%d,%d,%d' % (-2, -1, -1), 'x%d,%d,%d' % (sgl, -1, -1)]
            fops_3 = ['x%d,%d,%d' % (-2, -1, -1), 'x%d,%d,%d' % (-2, -1, -1)]
            yield (fops_1, fops_2, fops_3)
        elif numPlayers == 3:
            fops_1 = ['x%d,%d,%d' % (sgl, -1, -1), 'x%d,%d,%d' % (sgl, -1, -1), 'x%d,%d,%d' % (sgl, -1, -1)]
            fops_2 = ['x%d,%d,%d' % (-2, -1, -1), 'x%d,%d,%d' % (sgl, -1, -1), 'x%d,%d,%d' % (sgl, -1, -1)]
            fops_3 = ['x%d,%d,%d' % (-2, -1, -1), 'x%d,%d,%d' % (-2, -1, -1), 'x%d,%d,%d' % (sgl, -1, -1)]
            fops_4 = ['x%d,%d,%d' % (-2, -1, -1), 'x%d,%d,%d' % (-2, -1, -1), 'x%d,%d,%d' % (-2, -1, -1)]
            yield (fops_1, fops_2, fops_3, fops_4)

def convertLocation2xy(location):
    if 'SUR' in location:
        r = 0.5
    elif 'LEO' in location:
        r = 1.
    elif 'MEO' in location:
        r = 1.5
    elif "GEO" in location:
        r = 2
    else:
        r = 2.35

    sect = int(re.search(r'.+(\d)', location).group(1))
    tetha = +math.pi / 3 - (sect - 1) * math.pi / 3

    x, y = (r * math.cos(tetha), r * math.sin(tetha))
    # print location, x, y
    return (x, y)


def createPoints(letters, x, y, xdelta, ydelta, k):
    # print(letters)
    letterdict = defaultdict(list)
    d = 0.35
    k = (1.+k)/2.
    xdelta = k*xdelta
    ydelta = k*ydelta/1.5
    if len(letters) == 2:
        if letters == 'NN':
            delta = -d
        elif letters == 'AN':
            delta = 0
        elif letters == 'AA':
            delta = d

        xlist = [delta + x-xdelta/2., delta + x + xdelta/2.]
        ylist = 2*[y]
        for l, x, y in zip(letters, xlist, ylist):
            letterdict[l].append((x,y))
    elif len(letters) == 3:
        if letters == 'NNN':
            delta = -d
        elif letters == 'ANN':
            delta = -d/3.
        elif letters == 'AAN':
            delta = d/3.
        elif letters == 'AAA':
            delta = d

        xlist = [delta + x - xdelta/2., delta + x, delta + x + xdelta/2.]
        ylist = [y - ydelta*0.2886, y + ydelta/2., y - ydelta*0.2886]
        # ylist = 3*[y]
        for l, x, y in zip(letters, xlist, ylist):

            letterdict[l].append((x,y))

    return letterdict


def drawTotalAdaptive(query):
    global hardcoded_designs
    # print(hardcoded_designs)
    totalcash_dict = {}
    divider = 1000000.
    ydelta_dict = {0: 0.58575022518545405, 600: 0.9811286044285239, 1200: 2.111500681313383}
    my_dpi = 150

    fig = plt.figure(figsize=(800 / my_dpi, 800 / my_dpi), dpi=my_dpi)
    ax = fig.add_axes([0.1, 0.1, 0.9, 0.9])
    k = 0.5
    all_legends = []
    letter_dict = defaultdict(set)
    cost_color_dict = {600: 'b', 1200: 'm', 0: 'r'}
    cost_marker_dict = {600: 'H', 1200: '*', 0: '^'}


    totalcash_tuple_dict = defaultdict(list)
    color_dict = defaultdict(str)
    markerdict = defaultdict(str)
    order_dict = {'AA-AAA': 1, 'AAN': 2, 'AN-ANN': 3, 'NN-NNN': 4}
    design_point_dict = defaultdict(set)
    base_letter_dict = {(0, "A"): 'A', (600, "A"): "A", (1200, "A"): 'A', (0, "N"): 'Z', (600, "N"): "S", (1200, "N"): 'O'}
    letter_marker_dict = {'A': ('s', 'k', 'Federate Cost: Adaptive'),
                          'Z': (cost_marker_dict[0], cost_color_dict[0], 'Federate Cost: %d' % 0),
                          'S': (cost_marker_dict[600], cost_color_dict[600], 'Federate Cost: %d' % 600),
                          'O': (cost_marker_dict[1200], cost_color_dict[1200], 'Federate Cost: %d' % 1200)
                          }

    for basecost in [0, 600]:
        all_points = []
        for i, des in enumerate(hardcoded_designs):
            numPlayers = 2
            if '3.' in des:
                numPlayers = 3

            query['elementlist'] = des
            # print(query)
            # for sgl in costrange:
            # test = 'total adaptive'
            allfops = list(fopsGenTotal(des))

            if numPlayers == 2:
                allfops = list(fopsGenTotal(des))
                for tup in allfops:
                    # print(fops, fops_A6, fops_AA)
                    sgl = int(re.search(r'x([-\d]+).+', tup[0][0]).group(1))
                    if sgl != basecost:
                        continue
                    names = ['D%d_%s%s' % (i, 'N', 'N'), 'D%d_A%s' % (i, 'N'), 'D%d_AA' % i]
                    for fops, name in zip(tup, names):
                        query['fops'] = json.dumps(fops)
                        # print(query)
                        docs = list(db.results.find(query))[0]
                        results = json.loads(docs['results'])
                        totalcash = sum([e[1] for e in results])
                        # print(fops, results, totalcash)
                        totalcash_dict[name] = totalcash / divider

            elif numPlayers == 3:
                for tup in allfops:
                    # fops = tup[0]
                    sgl = int(re.search(r'x([-\d]+).+', tup[0][0]).group(1))
                    if sgl != basecost:
                        continue

                    # fops_list = [fops, fops_A66, fops_AA6, fops_AAA]
                    # names = ['D%d_%d%d%d'%(i, sgl//100, sgl//100, sgl//100), 'D%d_A%d%d'%(i, sgl//100, sgl//100), 'D%d_AA%d'%(i, sgl//100), 'D%d_AAA'%i]
                    names = ['D%d_%s%s%s' % (i, 'N', 'N', 'N'), 'D%d_A%s%s' % (i, 'N', 'N'), 'D%d_AA%s' % (i, 'N'),
                             'D%d_AAA' % i]
                    for fops, name in zip(tup, names):
                        query['fops'] = json.dumps(fops)
                        # print(query)
                        docs = list(db.results.find(query))[0]
                        results = json.loads(docs['results'])
                        totalcash = sum([e[1] for e in results])
                        # print(fops, results, totalcash)
                        totalcash_dict[name] = totalcash / divider

        # print(totalcash_dict)

        # totalcash_tuple_dict = defaultdict(list)
        # color_dict = defaultdict(str)
        # markerdict = defaultdict(str)
        # order_dict = {'AA-AAA': 1, 'AAN': 2, 'AN-ANN': 3, 'NN-NNN': 4}
        # plt.figure()

        design_point_dict = defaultdict(list)
        for D, y in totalcash_dict.items():
            # print(D,y)
            x = int(re.search(r'D(\d+)_(.+)', D).group(1)) + 1
            label = re.search(r'D(\d+)_(.+)', D).group(2)
            # print(label)
            # plt.annotate(label, xy=(x, y), xycoords='data', textcoords='offset points')
            # label_dict = ({'AA': r'$\clubsuit \clubsuit$', 'AN': r'$\clubsuit \blacksquare$',
            #                'NN':r'$\blacksquare \blacksquare$', 'AAA': r'$\clubsuit \clubsuit \clubsuit$',
            #                'ANN': r'$\clubsuit \blacksquare \blacksquare$', 'NNN':r'$\blacksquare \blacksquare \blacksquare$', 'AAN': r'$\clubsuit \clubsuit \blacksquare$'})
            # label2 = label_dict[label]
            # print(label2)
            # plt.text(x, y, ha="center", va="center", s = label2)
            xdelta = 0.14
            tempdict = createPoints(label, x, y, xdelta, xdelta*2.2, k)#ydelta_dict[basecost])
            values = [e for l in tempdict.values() for e in l]
            avgx = sum([e[0] for e in values]) / len(values)
            avgy = sum([e[1] for e in values]) / len(values)
            all_points.append((avgx, avgy))
            design_point_dict[x].append((round(avgx,2), round(avgy,2)))
            print(x, avgx, avgy)
            for l in tempdict:
                # print(l)
                l2 = base_letter_dict[(basecost, l)]
                letter_dict[l2] = letter_dict[l2].union(set(tempdict[l]))


            if label.count('A') == 0:
                lab = 'NN-NNN'
                color_dict[lab] = 'b'
                markerdict[lab] = '*'
                totalcash_tuple_dict[lab].append((x, y))

            elif label.count('A') == len(label):
                lab = 'AA-AAA'
                color_dict[lab] = 'k'
                markerdict[lab] = 's'
                totalcash_tuple_dict[lab].append((x, y))
            elif label.count('A') >= 2:
                lab = 'AAN'
                color_dict[lab] = 'g'
                markerdict[lab] = '^'
                totalcash_tuple_dict[lab].append((x, y))
            else:
                lab = 'AN-ANN'
                color_dict[lab] = 'r'
                markerdict[lab] = 'o'
                totalcash_tuple_dict[lab].append((x, y))

                # plt.scatter(x,y, color = color)
        legends = []
        # for label, points in sorted(totalcash_tuple_dict.items(), key = lambda x: order_dict[x[0]]):
        #     legends.append(label)
        #     plt.scatter(*zip(*points), color = color_dict[label], marker = markerdict[label], s = 40)
        #
        # plt.legend(legends, frameon=False,ncol=4, loc='upper center', bbox_to_anchor=(0.5, 1.15), labelspacing=2)

        # for letter, points in letter_dict.items():
        #     marker, color, legend = letter_marker_dict[letter]
        #     plt.scatter(*zip(*points), marker=marker, color=color, s=k*30, linewidths='2')
        #     legends.append(legend)
        #
        # plt.legend(legends)

        # for i in range(len(hardcoded_designs) - 1):
        #     plt.axvline(i + 1.5, color='k', linestyle=':', linewidth=0.6)
        #
        for d, points in design_point_dict.items():
            print(points)
            plt.plot(*zip(*points), 'k--', zorder = -3)

        plt.scatter(*zip(*all_points), marker='o', s=k * 400, facecolors='w', edgecolors='k', zorder=-2,
                        linewidths='1')
            # plt.xlim(0.5, len(hardcoded_designs) + 0.5)
        # # print("x lim and y lim:", ax.get_ylim(), ax.get_xlim())
        # xdelta = ax.get_xlim()[1] - ax.get_xlim()[0]
        # ydelta = ax.get_ylim()[1] - ax.get_ylim()[0]
        # # ydelta_dict[basecost] = ydelta/xdelta
        # plt.ylabel('total cash (M$)')
        # # plt.title('cost functions: $N = %d, A= adaptive$'%basecost)
        # xtickDict = {0: 'I', 1: 'II', 2: 'III', 3: 'IV', 4: 'V', 5: 'VI', 6: 'VII', 7: 'VIII', 8: 'XI', 9: 'X'}
        # xticklist = ['Design %s' % xtickDict[i] for i in range(len(hardcoded_designs))]
        # plt.xticks(range(1, len(hardcoded_designs) + 1), xticklist, rotation=0)
        # plt.savefig("Total_revenue_CostFunctions_Default%s.pdf" % str(basecost).zfill(4), bbox_inches='tight')
    legends = []
    lines = []
    for letter, points in letter_dict.items():
        marker, color, legend = letter_marker_dict[letter]
        newline = plt.scatter(*zip(*points), marker=marker, color=color, s=k * 30, linewidths='2')
        lines.append(newline)
        legends.append(legend)

    plt.legend(lines, legends)

    for i in range(len(hardcoded_designs) - 1):
        plt.axvline(i + 1.5, color='k', linestyle=':', linewidth=0.6)


    plt.xlim(0.5, len(hardcoded_designs) + 0.5)
    # print("x lim and y lim:", ax.get_ylim(), ax.get_xlim())
    xdelta = ax.get_xlim()[1] - ax.get_xlim()[0]
    ydelta = ax.get_ylim()[1] - ax.get_ylim()[0]
    # ydelta_dict[basecost] = ydelta/xdelta
    plt.ylabel('total cash (M$)')
    # plt.title('cost functions: $N = %d, A= adaptive$'%basecost)
    xtickDict = {0: 'I', 1: 'II', 2: 'III', 3: 'IV', 4: 'V', 5: 'VI', 6: 'VII', 7: 'VIII', 8: 'XI', 9: 'X'}
    xticklist = ['Design %s' % xtickDict[i] for i in range(len(hardcoded_designs))]
    plt.xticks(range(1, len(hardcoded_designs) + 1), xticklist, rotation=0)
    plt.savefig("Total_revenue_CostFunctions_Default.pdf", bbox_inches='tight')

    # print(ydelta_dict)
    plt.show()


def drawStorage(docslist, design, query):
    # fopslist = [d["fops"] for d in docslist]
    # print(docslist)
    storageset = sorted(list(set([d['storagePenalty'] for d in docslist])))
    # storageset = [-1, 0, 100, 300, 500]
    # storageset = [-2, -1]
    # plt.figure()
    storage_cashlist_dict = defaultdict(list)
    for s in storageset:
        # print("storage: ", s)
        tempdocs = [d for d in docslist if int(d["storagePenalty"]) == s]
        costlsit = [d['costSGL'] for d in tempdocs]
        resultlist = [json.loads(d["results"]) for d in tempdocs]
        cashlist = [sum([e[1] for e in r]) / 1000000. for r in resultlist]
        storage_cashlist_dict[s] =  [e[1] for e in sorted(list(zip(costlsit, cashlist)))]

    storage_residual_dict = defaultdict(int)
    baseline = storage_cashlist_dict[400]
    # print("base line 400:", baseline)
    # print(maxlist)
    for s in storageset:
        cashlist = storage_cashlist_dict[s]
        # print(s, ' cash list:', cashlist)
        residual = [100*(b-a)/a for a,b in zip(baseline, cashlist)]
        # residual = [b for a,b in zip(baseline, cashlist)]
        storage_residual_dict[s] = sum(residual)

    # print(storage_residual_dict)
    return storage_residual_dict

def calResidual(docslist, design, query):
    # fopslist = [d["fops"] for d in docslist]
    print(docslist)
    storageset = sorted(list(set([d['storagePenalty'] for d in docslist])))
    # storageset = [-1, 0, 100, 300, 500]
    # storageset = [-2, -1]
    # plt.figure()
    storage_cashlist_dict = defaultdict(list)
    for s in storageset:
        # print("storage: ", s)
        tempdocs = [d for d in docslist if int(d["storagePenalty"]) == s]
        print("length of tempdocs:", len(tempdocs))
        costlsit = [d['costSGL'] for d in tempdocs]
        # resultlist = [json.loads(d["results"]) for d in tempdocs]
        cashlist = [d["cashlist"] for d in tempdocs]
        storage_cashlist_dict[s] =  [e[1] for e in sorted(list(zip(costlsit, cashlist)))]
        print(s)
        print(len(storage_cashlist_dict[s]))
        print([len(a) for a in storage_cashlist_dict[s]])

    storage_residual_dict = defaultdict(list)
    baseline = [sum(a)/float(len(a)) for a in storage_cashlist_dict[400]]
    # print("base line 400:", baseline)
    # print(maxlist)
    for s in storageset:
        cashlist = storage_cashlist_dict[s]
        # print(s, ' cash list:', cashlist)
        residual = [[100*(b-a)/a for b in l] for a,l in zip(baseline, cashlist)]
        # residual = [b for a,b in zip(baseline, cashlist)]
        print("length of residual:", len(residual))
        storage_residual_dict[s] = residual

    # print(storage_residual_dict)

    return storage_residual_dict


def runQuery(db, query, test):
    global design_dict
    residual_dict = defaultdict(list)
    N = len(design_dict)
    numseeds = 30
    boxplot_dict = {}
    storage_dict = {400: 0, 800: 1, -1: 2}
    for des, i in sorted(design_dict.items(), key = lambda x: x[1]):
        query['elementlist'] = des
        query['numTurns'] = 240
        templist = []
        for fops in fopsGen(des, test):
            query['fops'] = json.dumps(fops)
            # print("query :", query['elementlist'])
            docsresult = list(db.results.find(query))
            sample = docsresult[0]
            # print(len(docsresult), len([d['numTurns'] for d in docsresult]))
            resultlist = sorted([(d['seed'], json.loads(d["results"])) for d in docsresult])
            cashlist = [sum([e[1] for e in r[1]]) / 1000000. for r in resultlist]
            row = {k: sample[k] for k in ['fops']}
            row['cashlist'] = cashlist[:numseeds]
            costsgl, storage, auctioneer = fops2costs(row['fops'])
            if costsgl not in [600, -3]:
                continue

            row['costSGL'] = costsgl
            row['costISL'] = costsgl
            row['storagePenalty'] = storage
            # print("row:", row)
            x = i * 3 + storage_dict[storage]
            print(i, des, sum(cashlist))
            boxplot_dict[x] = cashlist
            # templist.append(row)
            # if list(db.results.find(query)):
            #     templist.append(list(db.results.find(query))[0])
            # else:
            #     print(fops)
            #     termslist = [re.search(r"(x.+),([-\.\d]+),(.+)", f) for f in fops]
            #     newfops = ["%s,%1.2f,%s"%(terms.group(1), int(terms.group(2)), terms.group(3)) for terms in termslist]
            #     query['fops'] = json.dumps(newfops)
            #     print(query)
            #     templist.append(list(db.results.find(query))[0])


        # templist2 = []
        # # fopslist = [d['fops'] for d in templist]
        # for row in templist:
        #     # print("row: ", row)
        #     fops = row['fops']
        #     costsgl, storage, auctioneer = fops2costs(fops)
        #     if costsgl not in [600, -3]:
        #         continue
        #
        #     row['costSGL'] = costsgl
        #     row['costISL'] = costsgl
        #     row['storagePenalty'] = storage
        #     templist2.append(row)
        # print(len(templist))
        # storage_residual_dict = calResidual(templist, design=design_dict[des], query = query)
        # print("Storage residual dict:", len(storage_residual_dict), storage_residual_dict)
        # for s, v in storage_residual_dict.items():
        #     print(s)
        #     print(v)
        #     residual_dict[s].append(v)

    # print(boxplot_dict)
    typ = 'Stochastic' if 'stochastic' in test else 'Deterministic'
    xstick = list(range(1,16))
    xstick_minor = [2, 5, 8, 11, 14]
    xstick_design = ['Design %s'%s for s in ['I', 'II', 'III', 'IV', 'V']]
    xstick_storagepenalty = 5 * [400, 800, 'Marginal']
    xlines = [3.5, 6.5, 9.5, 12.5]

    # print(len(boxplot_dict))
    boxplot_list = [b[1] for b in sorted(boxplot_dict.items())]
    # print(boxplot_list)
    fig = plt.figure()
    ax1 = fig.add_subplot(111)
    plt.boxplot(boxplot_list, whis = 3)
    if typ == 'Stochastic':
        for i in range(1, 6):
            j = 3*i-1
            print(xstick_design[i-1])
            # print("800:", stats.f_oneway(boxplot_list[j], boxplot_list[j-1]))
            # print("400:", stats.f_oneway(boxplot_list[j], boxplot_list[j-2]))

            print("std:", np.std(boxplot_list[j-2]), np.std(boxplot_list[j-1]), np.std(boxplot_list[j]))
            print("mean:", np.mean(boxplot_list[j-2]), np.mean(boxplot_list[j-1]), np.mean(boxplot_list[j]))


    plt.xticks(xstick, xstick_storagepenalty,  rotation = 60)

    # plt.xticks(xstick_minor, xstick_design, minor = True)
    plt.ylabel('federation value (000)')
    for xline in xlines:
        plt.axvline(xline, color='k', linestyle='-', linewidth=0.3)

    plt.xlabel('Storage Penalty')
    ax2 = plt.twiny()
    ax2.set_xlim(ax1.get_xlim())
    ax2.set_xticks([a for a in xstick_minor])
    ax2.set_xticklabels(xstick_design)

    # plt.savefig("storagepenalty_%s.pdf" %(typ), bbox_inches='tight')
    plt.show()
    return boxplot_dict

def draw_Dictionary(residual_dict):
    plt.figure()
    legends = deque()
    dic = {e: 'SP:%d' % e for e in residual_dict if e >= 0}
    dic[-1] = 'SP:Marginal'
    dic[-2] = 'SP:QL'
    dic[-3] = 'SP:random'
    # dic[400] = 'SP: Fixed'
    dic[1200] = 'SP>1000'
    dic[0] = 'SP: Collaborative'
    baselist = [-1, 400, 800]
    # xy = sorted(zip(*[residual_dict[e] for e in baselist], list(range(len(residual_dict[-2])))), reverse=True, key=lambda x: x[1])
    xy = zip(*[residual_dict[e] for e in baselist], list(range(len(residual_dict[-1]))))
    legends = [dic[e] for e in baselist]
    Y = list(zip(*xy))
    designs = Y[-1]
    # print(designs)
    ls = iter(['--', ':', '-.', '-'])
    for s, y in zip(baselist, Y[:-1]):
        if s == 0:
            continue
        if s == -1:
            plt.scatter(range(len(y)), y, alpha = 0.5, color = 'k', marker = 's', label = dic[s], s = 80)
            # plt.plot(y, marker='o')
        elif s == 400:
            plt.scatter(range(len(y)), y, color = 'm', alpha = 0.5, marker = 'v', label = dic[s], s = 80)
            # plt.plot(y, marker='s')
        else:
            plt.scatter(range(len(y)), y, color = 'g', alpha=0.5, marker='o', label=dic[s], s = 80)


    xtickDict = {0: 'I', 1: 'II', 2:'III', 3:'IV', 4:'V', 5:'VI', 6:'VII', 7:'VIII', 8:'XI', 9:'X'}
    xticklist = ['Design %s'%xtickDict[i] for i in list(designs)]
    plt.xticks(list(range(len(residual_dict[-1]))),xticklist, rotation = 0)
    plt.legend(legends)
    for i in range(len(residual_dict[-1])-1):
        plt.axvline(i + 0.5, color='k', linestyle='-', linewidth=0.3)
    plt.xlim(-0.5, len(residual_dict[-1])-0.5)

def sumDics(db, query, test):
    typ = 'Stochastic' if 'stochastic' in test else 'Deterministic'
    residual_dict = defaultdict(list)
    # residual_dict = runQuery(db, query)

    for capacity, links in [(2,2)]:
        query['capacity'] = capacity
        query['links'] = links
        # print('Sum Dics query:')
        # print(query)
        tempdict = runQuery(db, query, test)
        print(len(tempdict))
        print([type(t) for t in tempdict])

        # for s in tempdict:
        #     # print("temp dict:", s)
        #     # print("tempdict seed:", s)
        #
        #     if s in residual_dict:
        #         residual_dict[s] = [a+b for a,b in zip(residual_dict[s], tempdict[s])]
        #     else:
        #         residual_dict[s] = tempdict[s]
        #
        #     print('residual dict s:', residual_dict[s])

        # draw_Dictionary(tempdict)
        # # plt.title('storage:%d, links:%d' % (capacity, links))
        # plt.ylabel('Improvement over baseline (%)')
        #
        #
        # plt.savefig("%s_storagepenalty_%d_%d.pdf" % (typ, capacity, links), bbox_inches='tight')
def avgQueryResults(query):
    # receives a query and calculates results as the average of all seeds (global variables)
    global db, seed1, seed2
    resultslist = []
    for seed in range(seed1, seed2):
        query['seed'] = seed
        # print(query)
        resultslist.append(json.loads(list(db.results.find(query))[0]['results']))

    final = resultslist[0]
    for i, _ in enumerate(final):
        # print(i, [len(r) for r in resultslist])
        final[i][1] = sum([r[i][1] for r in resultslist])/(seed2 - seed1)

    # print(final)
    return final



def drawAdaptiveSGL(query, test):
    global divider
    federatecash_dict_list1 = []
    federatecash_dict_list2 = []

    totalcash_dict_list = []

    for des in hardcoded_designs:
        query['elementlist'] = des
        numPlayers = 2
        if '3.' in des:
            numPlayers = 3

        federate_dict_1 = {}
        federate_dict_2 = {}
        totalcash_dict = {}
        # fopslist = list(fopsGen(des, test))
        for fops, fops_adaptive in fopsGen(des, test):
            print("fops:", fops, fops_adaptive)
            query['fops'] = fops
            # print(query)
            sgl = int(re.search(r"x([-\d]+),.+", fops).group(1))
            # print("length of query:", list(db.results.find(query)))
            # docs = list(db.results.find(query))[0]
            results = avgQueryResults(query)
            federatecash_1 = sum([e[1] for e in results])/len(results)

            cashlist_2 = []
            cashlist_a2 = []
            for n in range(len(results)):
                tempfops = json.loads(fops_adaptive)
                temp = tempfops[0]
                tempfops[0] = tempfops[n]
                tempfops[n] = temp
                query['fops'] = json.dumps(tempfops)
                results_adaptive = avgQueryResults(query)
                cashlist_a2.append(results_adaptive[n][1])
                cashlist_2.extend([r[1] for i, r in enumerate(results_adaptive) if i!=n])

            print(cashlist_2)
            print(cashlist_a2)
            federatecash_2 = sum(cashlist_2)/float(len(cashlist_2))
            federatecash_a2 = sum(cashlist_a2)/float(len(cashlist_a2))
            # print(query)
            # print("length of query:", list(db.results.find(query)))
            # docs_a = list(db.results.find(query))[0]

            # results = json.loads(docs['results'])
            # results = avgQueryResults(query)
            # results_adaptive = json.loads(docs_a['results'])
            # federatecash_a1 = results_adaptive[0][1]
            # federatecash_2 = sum([e[1] for e in results[1:]])/len(results[1:])
            # federetecash_a2 = sum([e[1] for e in results_adaptive[1:]])/len(results_adaptive[1:])

            totalcash = sum([e[1] for e in results])
            totalcash_adaptive = sum([e[1] for e in results_adaptive])
            print("Federate cash:", federatecash_1, federatecash_2, federatecash_a2)
            federate_dict_1[sgl] = (federatecash_1, federatecash_a2)
            federate_dict_2[sgl] = (federatecash_1, federatecash_2)
            # print(federatecash_1, federatecash_a1)
            # print(federatecash_2, federetecash_a2)
            totalcash_dict[sgl] = (totalcash, totalcash_adaptive)

        federatecash_dict_list1.append(federate_dict_1)
        federatecash_dict_list2.append(federate_dict_2)
        totalcash_dict_list.append(totalcash_dict)

    xtickDict = {0: 'I', 1: 'II', 2:'III', 3:'IV', 4:'V', 5:'VI', 6:'VII', 7:'VIII', 8:'XI', 9:'X'}
    xticklist = ['Design %s'%xtickDict[i] for i in range(len(hardcoded_designs))]

    delta = 0.3
    marker_dict = {-3: 'v', 0: '^', 600: 's', 1200: '*' ,'adaptive': 'o'}
    color_dict = {-3: 'g', 0: 'r', 600: 'b', 1200: 'm' ,'adaptive': 'k'}
    function_dict = {-3: 'CF=tri-random', 0: 'CF=   0', 600: 'CF= 600', 1200: 'CF>1000' ,'adaptive': 'CF=adaptive'}
    order_dict = {-3: 4.5, 0: 2, 600: 3, 1200: 4 ,'adaptive': 5}
    sp_list = [-3, 0, 600, 1200]

    all_points1 = defaultdict(list)
    all_points_adaptive1 = defaultdict(list)
    all_edges1 = defaultdict(list)
    all_points2 = defaultdict(list)
    all_edges2 = defaultdict(list)
    all_points_adaptive2 = defaultdict(list)

    for i, cash_dict in enumerate(federatecash_dict_list1):
        for k, v in cash_dict.items():
            print("adaptive cash: ", v)
            point1 = (i+1-delta, v[0]/divider)
            point2 = (i+1+delta, v[1]/divider)
            all_points1[k].append(point1)
            # all_points1['adaptive'].append(point2)
            all_points_adaptive1[k].append(point2)
            all_edges1[k].append((point1, point2))

    for i, cash_dict in enumerate(federatecash_dict_list2):
        for k, v in cash_dict.items():
            print("nonadaptive cash: ", v)
            point1 = (i+1-delta, v[0]/divider)
            point2 = (i+1+delta, v[1]/divider)
            all_points2[k].append(point1)
            # all_points2['adaptive'].append(point2)
            all_points_adaptive2[k].append(point2)
            # all_points2['adaptive'].append(point2)
            all_edges2[k].append((point1, point2))

    legends = []
    lines = []

    for s in sp_list:
        fig = plt.figure()
        ax1 = fig.add_axes([0.1, 0.5, 0.9, 0.35])
        points = all_points1[s]
        legends = []
        lines = []
        # for s, points in sorted(all_points.items(), key = lambda x: order_dict[x[0]]):
        lines.append(ax1.scatter(*zip(*points), marker = marker_dict[s], color = color_dict[s], s = 60, facecolors = 'w', linewidth='2'))
        legends.append(function_dict[s])

        points = all_points_adaptive1[s]
        lines.append(ax1.scatter(*zip(*points), marker = marker_dict['adaptive'], color = 'k', s = 60, facecolors = 'w', linewidth='2'))
        legends.append(function_dict['adaptive'])
        # plt.legend(legends, loc = 2)
        # fig.legend(lines, legends, frameon=False, ncol=3, loc='upper center', bbox_to_anchor=(0.4, 1.2), labelspacing=2)

        for edge in all_edges1[s]:
            # plt.plot(*zip(*edge), 'k:', linewidth = 0.7)
            ax1.arrow(edge[0][0], edge[0][1], 0.5*(edge[1][0]-edge[0][0]), 0.5*(edge[1][1]-edge[0][1]), head_width=0.07, head_length=0.2, linewidth = 0.4, fc ='k', ec = 'k', zorder = -1)

        plt.xticks(range(1, len(hardcoded_designs)+1), ['' for i in xticklist], rotation = 0)

        for i in range(len(hardcoded_designs)-1):
            ax1.axvline(i+1.5, color = 'k', linestyle = '-', linewidth = 0.3)

        plt.ylabel('adaptive cash (M$)')
        plt.xlim(0.5, len(hardcoded_designs)+0.5)
        ax2 = fig.add_axes([0.1, 0.1, 0.9, 0.35])

        # if s in all_edges2:
        points = all_points2[s]
        # print(s, points)
        # for s, points in sorted(all_points2.items(), key = lambda x: order_dict[x[0]]):
        lines.append(ax2.scatter(*zip(*points), marker = marker_dict[s], color = color_dict[s], s = 60, facecolors = 'w', linewidth='2'))
        legends.append(function_dict[s])

        # elif s in all_points_adaptive:
        points = all_points_adaptive2[s]
        # print(s, points)
        # for s, points in sorted(all_points_adaptive.items(), key = lambda x: order_dict[x[0]]):
        lines.append(ax2.scatter(*zip(*points), marker = marker_dict[s], color = 'k', s = 60, facecolors = 'w', linewidth='2'))
        legends.append(function_dict[s])

        # edge = all_edges2[s]
        for edge in all_edges2[s]:
            # plt.plot(*zip(*edge), 'k:', linewidth = 0.7)
            ax2.arrow(edge[0][0], edge[0][1], 0.5*(edge[1][0]-edge[0][0]), 0.5*(edge[1][1]-edge[0][1]), head_width=0.07, head_length=0.2, linewidth = 0.4, fc ='k', ec = 'k', zorder = -1)

        plt.xticks(range(1, len(hardcoded_designs)+1), xticklist, rotation = 0)
        for i in range(len(hardcoded_designs)-1):
            ax2.axvline(i+1.5, color = 'k', linestyle = '-', linewidth = 0.3)

        fig.legend(lines[:2]+lines[3:], legends[:2]+legends[3:], loc='upper center', ncol = 3)
        plt.ylabel('non-adaptive (M$)')
        plt.savefig("Federate_revenue_costfunction_V3_sp%s.pdf"%str(s), bbox_inches='tight')

    plt.show()

    # print(federatecash_dict_list1)
    # print(totalcash_dict_list)


def drawStoragePenalty(db):
    query = {'experiment': 'Storage Penalty V2'}
    test = 'regular storage deterministic'
    sumDics(db, query, test)

    test = 'regular storage stochastic'
    sumDics(db, query, test)
    plt.show()

def drawFederateAdaptive(db):
    global numTurns
    query = {'experiment': 'Adaptive Cost V2', 'capacity': 2, 'links': 2, 'numTurns': numTurns}
    test = 'federate adaptive'

    drawAdaptiveSGL(query, test)

# def drawTotalAdaptive(db):
#     query = {'experiment': 'Adaptive Cost', 'capacity': 2, 'links': 2}
#     drawTotalAdaptive(query)

def drawAdaptiveAuctioneer(db):
    global design_dict, xticklist
    query = {'capacity': 2, 'links': 2, 'numTurns': 2400}
    totalcash_dict = defaultdict(list)
    all_points1 = []
    all_points2 = []
    all_edges = []
    test = 'auctioneer'
    divider = 1000000
    all_federate_edges = []
    for des in hardcoded_designs:
        query['elementlist'] = des
        numPlayers = 2
        if '3.' in des:
            numPlayers = 3

        for fops_adaptive, fops_auctioneer in fopsGen(des, test):
            query['fops'] = json.dumps(fops_adaptive)
            query['experiment'] = 'Adaptive Cost'
            # print(query)
            docs_adaptive = list(db.results.find(query))[0]
            query['fops'] = json.dumps(fops_auctioneer)
            query['experiment'] = 'Adaptive Cost Auctioneer'
            # print(query)
            docs_auctioneer = list(db.results.find(query))[0]

            results1 = json.loads(docs_adaptive['results'])
            results2 = json.loads(docs_auctioneer['results'])

            totalcash1 = sum([e[1] for e in results1])
            totalcash2 = sum([e[1] for e in results2])

            points1 = [(1+design_dict[des]-0.3, e[1]/divider) for e in results1]
            points2 = [(1+design_dict[des]+0.3, e[1]/divider) for e in results2]

            all_points1.extend(points1)
            all_points2.extend(points2)

            all_federate_edges.extend(list(zip(points1, points2)))


            point1 = (1+design_dict[des]-0.3, totalcash1/divider)
            point2 = (1+design_dict[des]+0.3, totalcash2/divider)
            totalcash_dict['adaptive'].append(point1)
            totalcash_dict['auctioneer'].append(point2)
            all_edges.append((point1, point2))


    print(totalcash_dict)
    fig = plt.figure()
    ax1 = fig.add_axes([0.1, 0.5, 0.9, 0.35])

    ax1.scatter(*zip(*totalcash_dict['adaptive']), marker='s', color='k', s=70, facecolors='w', linewidth='2')
    ax1.scatter(*zip(*totalcash_dict['auctioneer']), marker='s', color='k', s=70, facecolors='k', linewidth='2')

    plt.legend(['Adaptive (A)', 'A with Auctioneer'])

    for i in range(len(hardcoded_designs)-1):
        plt.axvline(i+1.5, color = 'k', linestyle = '-', linewidth = 0.3)

    for edge in all_edges:
        # plt.plot(*zip(*edge), 'k:', linewidth = 0.7)
        plt.arrow(edge[0][0], edge[0][1], 0.8*(edge[1][0]-edge[0][0]), 0.8*(edge[1][1]-edge[0][1]), head_width=0.1, head_length=0.1,
                  linewidth = 1., fc ='k', ec = 'k', zorder = -1, linestyle = ':')

    plt.xticks(range(1, len(hardcoded_designs) + 1), ['' for i in xticklist], rotation=0)
    plt.ylabel("total cash")
    ax2 = fig.add_axes([0.1, 0.1, 0.9, 0.35])

    ax2.scatter(*zip(*all_points1), marker='o', color='k', s=60, facecolors='w', linewidth='2')
    ax2.scatter(*zip(*all_points2), marker='o', color='k', s=60, facecolors='k', linewidth='2')
    plt.legend(['Adaptive Federate (AF)', 'AF with auctioneer'])
    for i in range(len(hardcoded_designs) - 1):
        plt.axvline(i + 1.5, color='k', linestyle='-', linewidth=0.3)

    for edge in all_federate_edges:
        # plt.plot(*zip(*edge), 'k:', linewidth = 0.7)
        plt.arrow(edge[0][0], edge[0][1], 0.8 * (edge[1][0] - edge[0][0]), 0.8 * (edge[1][1] - edge[0][1]),
                  head_width=0.1, head_length=0.1, linewidth=1, fc='k', ec='k', zorder=-1, linestyle = ':')

    plt.ylabel("federate cash")
    plt.xticks(range(1, len(hardcoded_designs) + 1), xticklist, rotation=0)
    plt.savefig("TotalCash_Adaptive_vs_Auctioneer.pdf", bbox_inches='tight')
    # plt.show()



def drawStorageCoefficient(db):
    global xticklist, hardcoded_designs, divider
    # print(xticklist)
    query = {'experiment': 'Storage Penalty', 'capacity': 2, 'links': 2, 'numTurns': 2400}
    for j, des in enumerate(hardcoded_designs):
        # print(des)
        # print(xticklist[j])
        query['elementlist'] = des
        numPlayers = 2
        if '3.' in des:
            numPlayers = 3
        coefreslist = []
        pricereslist = []
        legends = []
        for test in ['storage stochastic', 'storage deterministic']:
            coefresulttuples = []
            priceresultsdict = {}
            for fops in fopsGen(des, test):
                # print(fops)
                query['fops'] = json.dumps(fops)
                query['experiment'] = 'Storage Penalty'
                # print(query)
                docs = list(db.results.find(query))
                # print(query, len(docs))
                docs = docs[0]
                # print("length of docs:", len(docs))
                results = json.loads(docs['results'])
                totalcash = sum([e[1] for e in results])/divider
                k = float(re.search(r'x.+,([-\.\d]+),.+', fops[0]).group(1))
                # print(k)
                if k<0:
                    coefresulttuples.append((abs(k), totalcash))
                else:
                    priceresultsdict[k] = totalcash
            coefreslist.append(coefresulttuples)
            pricereslist.append(priceresultsdict)
            legends.append(test)

        # print(coefresulttuples)
        # print(priceresultsdict)
        plt.figure()
        # coefresulttuples = sorted(coefresulttuples)
        plt.plot(*list(zip(*sorted(coefreslist[0]))))
        plt.plot(*list(zip(*sorted(coefreslist[1]))))
        stochasticMAX = max(pricereslist[0].items(), key = lambda x: x[1])
        deterministicMAX = max(pricereslist[1].items(), key = lambda x: x[1])
        plt.axhline(deterministicMAX[1], linestyle = '--', c = 'r')
        legends.append("deter-cost SP:%d"%deterministicMAX[0])
        plt.axhline(stochasticMAX[1], linestyle = '-.', c = 'b')
        legends.append("stoch-cost SP:%d"%stochasticMAX[0])
        plt.legend(legends)
        plt.title("%s"%(xticklist[j]))
        plt.ylabel('total cash')
        plt.xlabel('storage coefficient')
        plt.savefig("storagepenalty_coefficient_%s.pdf"%xticklist[j], bbox_inches='tight')

    plt.show()


def drawGraphbyDesign(number, design):
    elements = design.split(' ')
    federates = set([int(e[0]) for e in elements])
    federates_location_dict = defaultdict(list)
    federates_type_dict = defaultdict(list)
    federate_coordinates_dict = defaultdict(list)
    my_dpi = 150
    plt.figure(figsize=(800/my_dpi, 800/my_dpi), dpi=my_dpi)
    for r in [4, 2.25, 1.]:
        x = np.linspace(-1.0*r, 1.0*r, 50)
        y = np.linspace(-1.0*r, 1.0*r, 50)
        X, Y = np.meshgrid(x, y)
        F = X ** 2 + Y ** 2 - r
        plt.contour(X, Y, F, [0], colors='k', linewidths = 0.3, origin = 'lower', zorder = -1)

    font = FontProperties()
    font.set_style('italic')
    font.set_weight('bold')
    font.set_size('x-small')
    for x,y,lab in [(0,0,'SUR'), (0, 1, "LEO"),(0, 1.5, 'MEO'),(0, 2, 'GEO')]:
        # plt.annotate(lab, xy = (x,y), xytext = (x-0.2, y-0.1))
        plt.text(x,y, ha="center", va="center", s = lab, bbox = dict(fc="w", ec="w", lw=2),fontproperties=font)

    for i, (x, y) in enumerate([convertLocation2xy(e) for e in ['OOO'+str(i) for i in range(1,7)]]):
        plt.text(x, y, ha="center", va="center", s=str(i+1), bbox=dict(fc="none", ec="none", lw=2), fontproperties=font)

    font.set_size('medium')
    plt.text(0, 2.3 , ha="left", va="center", s=r'$|\rightarrow \theta$', bbox=dict(fc="w", ec="w", lw=2), fontproperties=font)

    types_dict = {'GroundSta': "G", 'Sat': 'S'}
    colordict = {'F1': 'yellow', 'F2': 'lightcyan', 'F3': 'lightgrey'}
    allpossiblelocations = []
    for location in ['SUR', 'LEO', 'MEO', 'GEO']:
        for i in range(1,7):
            allpossiblelocations.append(location + str(i))

    allpossiblecoordinates = [convertLocation2xy(e) for e in allpossiblelocations]
    plt.scatter(*zip(*allpossiblecoordinates), marker = "H", s = 800, color = 'k', facecolors = 'w')
    for f in federates:
        types = [re.search(r'\d\.(.+)@(\w+\d)', e).group(1) for e in elements if '%d.' % f in e]
        federates_type_dict['F%d'%f] = [types_dict[t] for t in types]
        federates_location_dict['F%d'%f] = [re.search(r'(.+)@(\w+\d)', e).group(2) for e in elements if '%d.'%f in e]
        federate_coordinates_dict['F%d'%f] = [convertLocation2xy(loc) for loc in federates_location_dict['F%d'%f]]
        plt.scatter(*zip(*federate_coordinates_dict['F%d'%f]), marker = "H", s = 800, edgecolors = 'k', facecolors = colordict['F%d'%f], linewidth='3')
        for x, y in federate_coordinates_dict['F%d'%f]:
            plt.annotate('F%d'%f, xy = (x, y), xytext = (x-0.1, y-0.075))


    plt.xticks([])
    plt.yticks([])
    rlim = 2.5
    plt.xlim(-rlim, rlim)
    plt.ylim(-rlim+0.2, rlim)
    plt.axis('off')
    des_roman_dict = {1: 'I', 2: 'II', 3:'III', 4:'IV', 5:'V'}
    plt.savefig("Design_%s.pdf"%des_roman_dict[number], bbox_inches='tight')



# db = None
# dbHost = socket.gethostbyname(socket.gethostname())
# dbHost = "127.0.0.1"
# # dbHost = "155.246.119.10"
# dbName = None
# dbPort = 27017
#
# db = pymongo.MongoClient(dbHost, dbPort).ofs
# seed1 = 20
# seed2 = 30
# numTurns = 2400
# divider = 1000000
# # #
# drawStoragePenalty(db)
# #
# # drawFederateAdaptive(db)
# #
# # drawTotalAdaptive({'experiment': 'Adaptive Cost', 'capacity': 2, 'links': 2, 'numTurns': 2400})
# #
# # drawAdaptiveAuctioneer(db)
# #
# # drawSampleNetwork()
# #
# # drawStorageCoefficient(db)
#
# # for i, des in enumerate(hardcoded_designs):
# # #     drawGraphbyDesign(i+1, des)