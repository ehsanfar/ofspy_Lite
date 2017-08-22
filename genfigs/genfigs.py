import pymongo
import socket
import json
import pandas as pd
import matplotlib.pyplot as plt
import re
from collections import defaultdict, deque


hardcoded_designs = (
        "1.GroundSta@SUR1 2.GroundSta@SUR4 1.Sat@MEO1 1.Sat@MEO4 2.Sat@MEO5 1.Sat@LEO1 2.Sat@LEO2",
        "1.GroundSta@SUR1 2.GroundSta@SUR4 2.Sat@GEO4 1.Sat@MEO1 1.Sat@MEO4 2.Sat@MEO5 1.Sat@LEO1 2.Sat@LEO2",
        "1.GroundSta@SUR1 2.GroundSta@SUR3 3.GroundSta@SUR5 1.Sat@MEO1 1.Sat@MEO2 2.Sat@MEO3 2.Sat@MEO5 3.Sat@MEO6",
        "1.GroundSta@SUR1 2.GroundSta@SUR3 3.GroundSta@SUR5 3.Sat@GEO5 1.Sat@MEO1 1.Sat@MEO2 2.Sat@MEO3 2.Sat@MEO5 3.Sat@MEO6",
        "1.GroundSta@SUR1 2.GroundSta@SUR3 3.GroundSta@SUR5 1.Sat@MEO1 2.Sat@MEO2 3.Sat@MEO5 1.Sat@LEO2 2.Sat@LEO4 3.Sat@LEO6",
    )


design_dict = {d: i for i,d in enumerate(hardcoded_designs)}

def filterInvalidDics(dictlist):
    return [dic for dic in dictlist if len(set(dic['costDictList'])) <= 2]

def findBalancedMembers(dictlist):
    return [dic for dic in dictlist if len(set(dic['costDictList'])) == 1]

def fops2costs(fops):
    costSGL, storagePenalty, auctioneer = re.search('x([-\d]+),([-\d]+),([-\d]+)', fops).groups()
    # print(costSGL, costISL, storagePenalty)
    return (int(costSGL), int(storagePenalty), int(auctioneer))

def fopsGen(des, test):
    print("test:",test)
    numPlayers = 2
    if '3.' in des:
        numPlayers = 3

    if 'storage' in test:
        if 'stochastic' in test or 'random' in test:
            costsgl = [-3]
        else:
            costsgl = [600]

        storage = [-1, 400, 800]
        for sgl in costsgl:
            for stor in storage:
                fopslist = json.dumps(numPlayers*['x%d,%d,%d'%(sgl, stor, -1)])
                yield fopslist
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

def createPoints(letters, x, y, xdelta, ydelta, k):
    letterdict = defaultdict(list)
    d = 0.35
    k = (1.+k)/2
    xdelta = k*xdelta
    ydelta = k*ydelta
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
    for basecost in [0, 600, 1200]:
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

        totalcash_tuple_dict = defaultdict(list)
        color_dict = defaultdict(str)
        markerdict = defaultdict(str)
        order_dict = {'AA-AAA': 1, 'AAN': 2, 'AN-ANN': 3, 'NN-NNN': 4}
        # plt.figure()

        letter_dict = defaultdict(list)
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
            design_point_dict[x].append((avgx, avgy))
            print(x, avgx, avgy)
            for l in tempdict:
                letter_dict[l].extend(tempdict[l])


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
        cost_color_dict = {600: 'b', 1200: 'm', 0: 'r'}
        cost_marker_dict = {600: 'H', 1200: '*', 0: '^'}
        letter_marker_dict = {'A': ('s', 'k', 'Federate Cost: Adaptive'),
                              'N': (cost_marker_dict[basecost], cost_color_dict[basecost], 'Federate Cost: %d' % basecost)}
        for letter, points in letter_dict.items():
            marker, color, legend = letter_marker_dict[letter]
            plt.scatter(*zip(*points), marker=marker, color=color, s=k*30, linewidths='2')
            legends.append(legend)

        plt.legend(legends)
        plt.scatter(*zip(*all_points), marker = 'o', s = k*400, facecolors = 'w', edgecolors='k', zorder = -2, linewidths='1')
        for i in range(len(hardcoded_designs) - 1):
            plt.axvline(i + 1.5, color='k', linestyle=':', linewidth=0.6)

        for d, points in design_point_dict.items():
            print(points)
            plt.plot(*zip(*points), 'k--', zorder = -3)

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
    print(docslist)
    storageset = sorted(list(set([d['storagePenalty'] for d in docslist])))
    # storageset = [-1, 0, 100, 300, 500]
    # storageset = [-2, -1]
    # plt.figure()
    storage_cashlist_dict = defaultdict(list)
    for s in storageset:
        print("storage: ", s)
        tempdocs = [d for d in docslist if int(d["storagePenalty"]) == s]
        costlsit = [d['costSGL'] for d in tempdocs]
        resultlist = [json.loads(d["results"]) for d in tempdocs]
        cashlist = [sum([e[1] for e in r]) / 1000000. for r in resultlist]
        storage_cashlist_dict[s] =  [e[1] for e in sorted(list(zip(costlsit, cashlist)))]

    storage_residual_dict = defaultdict(int)
    baseline = storage_cashlist_dict[400]
    print("base line 400:", baseline)
    # print(maxlist)
    for s in storageset:
        cashlist = storage_cashlist_dict[s]
        print(s, ' cash list:', cashlist)
        residual = [100*(b-a)/a for a,b in zip(baseline, cashlist)]
        # residual = [b for a,b in zip(baseline, cashlist)]
        storage_residual_dict[s] = sum(residual)

    return storage_residual_dict

def fopsGen(des, test):
    numPlayers = 2
    if '3.' in des:
        numPlayers = 3

    if 'storage' in test:
        if 'stochastic' in test or 'random' in test:
            costsgl = [-3]
        else:
            costsgl = [600]

        storage = [-1, 400, 800]
        for sgl in costsgl:
            for stor in storage:
                fopslist = json.dumps(numPlayers*['x%d,%d,%d'%(sgl, stor, -1)])
                yield fopslist
    elif 'federate adaptive' in test:
        costrange = [-3, 0, 1200, 600]
        for sgl in costrange:
            fops_adaptive = json.dumps(['x%d,%d,%d' % (-2, -1, -1)] + (numPlayers-1) * ['x%d,%d,%d' % (sgl, -1, -1)])
            fops = json.dumps(numPlayers * ['x%d,%d,%d' % (sgl, -1, -1)])
            yield (fops, fops_adaptive)



def runQuery(db, query, test):
    global design_dict
    residual_dict = defaultdict(list)
    N = len(design_dict)
    for des, i in sorted(design_dict.items(), key = lambda x: x[1]):
        query['elementlist'] = des
        templist = []
        for fops in fopsGen(des, test):
            query['fops'] = fops
            templist.append(list(db.results.find(query))[0])

        templist2 = []
        # fopslist = [d['fops'] for d in templist]
        for row in templist:
            print("row: ", row)
            fops = row['fops']
            costsgl, storage, auctioneer = fops2costs(fops)
            if costsgl not in [600, -3]:
                continue

            row['costSGL'] = costsgl
            row['costISL'] = costsgl
            row['storagePenalty'] = storage
            templist2.append(row)
        # print(len(templist))
        storage_residual_dict = drawStorage(templist2, design=design_dict[des], query = query)
        # print("Storage residual dict:", len(storage_residual_dict), storage_residual_dict)
        for s, v in storage_residual_dict.items():
            residual_dict[s].append(v)

    return residual_dict

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
    print(designs)
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
        print(query)
        tempdict = runQuery(db, query, test)
        for s in tempdict:
            if s in residual_dict:
                residual_dict[s] = [a+b for a,b in zip(residual_dict[s], tempdict[s])]
            else:
                residual_dict[s] = tempdict[s]

        draw_Dictionary(tempdict)
        # plt.title('storage:%d, links:%d' % (capacity, links))
        plt.ylabel('Improvement over baseline (%)')


        plt.savefig("%s_storagepenalty_%d_%d.pdf" % (typ, capacity, links), bbox_inches='tight')


def drawAdaptiveSGL(query, test):
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
            sgl = int(re.search(r"x([-\d]+),.+", fops).group(1))
            docs = list(db.results.find(query))[0]
            query['fops'] = fops_adaptive
            print(query)
            docs_a = list(db.results.find(query))[0]

            results = json.loads(docs['results'])
            results_adaptive = json.loads(docs_a['results'])

            federatecash_1 = results[0][1]
            federatecash_a1 = results_adaptive[0][1]
            federatecash_2 = sum([e[1] for e in results[1:]])/len(results[1:])
            federetecash_a2 = sum([e[1] for e in results_adaptive[1:]])/len(results_adaptive[1:])

            totalcash = sum([e[1] for e in results])
            totalcash_adaptive = sum([e[1] for e in results_adaptive])
            federate_dict_1[sgl] = (federatecash_1, federatecash_a1)
            federate_dict_2[sgl] = (federatecash_2, federetecash_a2)
            print(federatecash_1, federatecash_a1)
            print(federatecash_2, federetecash_a2)
            totalcash_dict[sgl] = (totalcash, totalcash_adaptive)


        federatecash_dict_list1.append(federate_dict_1)
        federatecash_dict_list2.append(federate_dict_2)

        totalcash_dict_list.append(totalcash_dict)


    xtickDict = {0: 'I', 1: 'II', 2:'III', 3:'IV', 4:'V', 5:'VI', 6:'VII', 7:'VIII', 8:'XI', 9:'X'}
    xticklist = ['Design %s'%xtickDict[i] for i in range(len(hardcoded_designs))]

    delta = 0.3
    marker_dict = {-3: 'v', 0: '^', 600: 's', 1200: '*' ,'adaptive': 'o'}
    color_dict = {-3: 'g', 0: 'r', 600: 'b', 1200: 'm' ,'adaptive': 'k'}
    function_dict = {-3: 'CF=uniform', 0: 'CF=   0', 600: 'CF= 600', 1200: 'CF>1000' ,'adaptive': 'CF=adaptive'}
    order_dict = {-3: 4.5, 0: 2, 600: 3, 1200: 4 ,'adaptive': 5}

    all_points = defaultdict(list)
    all_edges = []
    divider = 1000000.
    fig = plt.figure()
    ax1 = fig.add_axes([0.1, 0.1, 0.4, 0.7])

    for i, cash_dict in enumerate(federatecash_dict_list1):
        for k, v in cash_dict.items():
            point1 = (i+1-delta, v[0]/divider)
            point2 = (i+1+delta, v[1]/divider)
            all_points[k].append(point1)
            all_points['adaptive'].append(point2)
            all_edges.append((point1, point2))

    legends = []

    lines = []
    for s, points in sorted(all_points.items(), key = lambda x: order_dict[x[0]]):
        lines.append(ax1.scatter(*zip(*points), marker = marker_dict[s], color = color_dict[s], s = 60, facecolors = 'w', linewidth='2'))
        legends.append(function_dict[s])

    # plt.legend(legends, loc = 2)
    # fig.legend(lines, legends, frameon=False, ncol=3, loc='upper center', bbox_to_anchor=(0.4, 1.2), labelspacing=2)
    fig.legend(lines, legends, loc='upper center', ncol = 3)

    for edge in all_edges:
        # plt.plot(*zip(*edge), 'k:', linewidth = 0.7)
        ax1.arrow(edge[0][0], edge[0][1], 0.8*(edge[1][0]-edge[0][0]), 0.8*(edge[1][1]-edge[0][1]), head_width=0.1, head_length=0.1, linewidth = 0.4, fc ='k', ec = 'k', zorder = -1)

    plt.xticks(range(1, len(hardcoded_designs)+1), xticklist, rotation = 60)

    for i in range(len(hardcoded_designs)-1):
        ax1.axvline(i+1.5, color = 'k', linestyle = '-', linewidth = 0.3)


    plt.ylabel('federate cash (M$)')
    plt.xlim(0.5, len(hardcoded_designs)+0.5)

    ax2 = fig.add_axes([0.55, 0.1, 0.4, 0.7])

    all_points = defaultdict(list)
    all_points_adaptive = defaultdict(list)
    all_edges = []

    for i, cash_dict in enumerate(federatecash_dict_list2):
        for k, v in cash_dict.items():
            point1 = (i+1-delta, v[0]/divider)
            point2 = (i+1+delta, v[1]/divider)
            all_points[k].append(point1)
            # all_points['adaptive'].append(point2)
            all_points_adaptive[k].append(point2)
            all_edges.append((point1, point2))

    lines = []
    for s, points in sorted(all_points.items(), key = lambda x: order_dict[x[0]]):
        lines.append(ax2.scatter(*zip(*points), marker = marker_dict[s], color = color_dict[s], s = 60, facecolors = 'w', linewidth='2'))
        legends.append(function_dict[s])

    for s, points in sorted(all_points_adaptive.items(), key = lambda x: order_dict[x[0]]):
        lines.append(ax2.scatter(*zip(*points), marker = marker_dict[s], color = 'k', s = 60, facecolors = 'w', linewidth='2'))
        legends.append(function_dict[s])

    for edge in all_edges:
        # plt.plot(*zip(*edge), 'k:', linewidth = 0.7)
        ax2.arrow(edge[0][0], edge[0][1], 0.8*(edge[1][0]-edge[0][0]), 0.8*(edge[1][1]-edge[0][1]), head_width=0.1, head_length=0.1, linewidth = 0.4, fc ='k', ec = 'k', zorder = -1)

    plt.xticks(range(1, len(hardcoded_designs)+1), xticklist, rotation = 60)
    for i in range(len(hardcoded_designs)-1):
        ax2.axvline(i+1.5, color = 'k', linestyle = '-', linewidth = 0.3)

    plt.savefig("Federate_revenue_costfunction.pdf", bbox_inches='tight')
    plt.show()

    # print(federatecash_dict_list1)
    # print(totalcash_dict_list)


def drawAdaptiveSGL(query, test):
    drawTotalAdaptive


def drawStoragePenalty(db):
    query = {'experiment': 'Adaptive Cost'}
    test = 'storage deterministic'
    sumDics(db, query, test)

    test = 'storage stochastic'
    sumDics(db, query, test)

    plt.show()

def drawFederateAdaptive(db):
    query = {'experiment': 'Adaptive Cost', 'capacity': 2, 'links': 2}
    test = 'federate adaptive'
    drawAdaptiveSGL(query, test)

# def drawTotalAdaptive(db):
#     query = {'experiment': 'Adaptive Cost', 'capacity': 2, 'links': 2}
#     drawTotalAdaptive(query)


db = None
dbHost = socket.gethostbyname(socket.gethostname())
dbHost = "127.0.0.1"
# dbHost = "155.246.119.10"
dbName = None
dbPort = 27017

db = pymongo.MongoClient(dbHost, dbPort).ofs

# drawFederateAdaptive(db)

drawTotalAdaptive({'experiment': 'Adaptive Cost', 'capacity': 2, 'links': 2, 'numTurns': 2400})

