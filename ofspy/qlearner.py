import numpy as np
from itertools import product
import random
from collections import deque, defaultdict
import math

class Qlearner():
    def __init__(self, federate, numericactions, memoryset, sectors = [1]):
        self.states = list(product(sorted(list(memoryset)), sectors))
        self.stateDict = {e: i for i,e in enumerate(self.states)}
        # print(numericactions, self.states)
        self.q = np.zeros((len(self.states), len(numericactions)))

        self.gamma = 0.9
        self.alpha = 0.2
        # self.n_states = len(self.stateDict)
        # self.n_actions = len(numericactions)
        self.actions = numericactions
        self.epsilon = 0.05
        self.random_state = np.random.RandomState(0)
        self.time = 0

        self.federate = federate
        self.recentstateactions = defaultdict(deque)
        self.timeStateDict = {}
        self.actionlist = deque([])
        self.inertia = 6
        self.elementInertia = defaultdict(lambda: self.inertia)
        self.elementAction = defaultdict(list)
        self.delta = 3

        self.splitflag = True



    def update_q(self, element, rewards):
        self.time = element.federateOwner.time
        name = element.name
        while self.recentstateactions[name] and self.recentstateactions[name][0][2] < self.time - self.delta:
            self.recentstateactions[name].popleft()
        # current_state = self.stateDict[(int(element.capacity - element.content), element.section)]
        # self.timeStateDict[self.time] = current_state
        # print("recent state actions:", self.recentstateactions[element.name])
        # print("rewards:", rewards)
        N = float(len(self.recentstateactions))
        for state, action, t in self.recentstateactions[name]:
            qsa = self.q[state, action]
            # print(time, element.timeStateDict[time + 1], self.stateDict[element.timeStateDict[time + 1]])
            # new_q = qsa + self.alpha * (rewards/N + self.gamma * max(self.q[self.stateDict[element.timeStateDict[t + 1]], :]) - qsa)
            new_q = qsa + self.alpha * (rewards/N + self.gamma * max(self.q[self.stateDict[(element.timeStateDict[t + 1][0], 1)], :]) - qsa)
            # print("qsa, nextstate, max:", name, qsa, element.timeStateDict[t], element.timeStateDict[t + 1], max(self.q[self.stateDict[element.timeStateDict[t + 1]], :]), new_q)

            self.q[state, action] = new_q
            # print("new q:", state, new_q, [int(e) for e in list(self.q[state])])
            # renormalize row to be between 0 and 1
            # rn = self.q[state] / np.sum(self.q[state])
            # self.q[state] = [round(r, 2) for r in rn]

        # print("SUM OF Q:", self.q.sum())
            # print(self.q[state])


        # print("Q matrix:", self.q)
    def splitresolution(self):
        columns = [self.q[:, i] for i in range(self.q.shape[1])]
        meancolumns = [(columns[i]+columns[i-1])/2. for i in range(1, len(columns))]
        newcolums = (len(columns) + len(meancolumns))*[None]
        newcolums[::2] = columns
        newcolums[1::2] = meancolumns

        actionslist = list(self.actions)
        meanactionslist = [(actionslist[i]+actionslist[i-1])/2. for i in range(1, len(actionslist))]
        newactions = (len(actionslist) + len(meanactionslist))*[None]
        newactions[::2] = actionslist
        newactions[1::2] = meanactionslist

        # print(newcolums)
        self.q = np.concatenate(newcolums, 1)
        self.actions = np.array(newactions)

    def getAction(self, element):
        self.time = element.federateOwner.time
        # self.elementInertia[element.name] -= 1
        if self.elementAction[element.name] and self.time -  self.elementAction[element.name][1] < self.inertia:
            return 6*[self.elementAction[element.name][0]]
            # return self.recentstateactions[element.name][-1][1]

        # if self.time > 300 and self.splitflag:
        #     self.splitresolution()
        #     self.splitflag = False
        # self.elementInertia[element.name] = 10

        # current_state = self.stateDict[(int(element.capacity - element.content), element.section)]
        current_state = self.stateDict[(int(element.capacity - element.content), 1)]


        # valid_moves = self.r[current_state] >= 0
        if self.elementAction[element.name]:
            lastaction = self.elementAction[element.name][0]
            lastindex = self.actions.index(lastaction)
        else:
            lastindex = (1+len(self.actions))//2

        # newepsilon = self.epsilon*max(0.1, (1 - self.time/3000))
        if self.random_state.rand() < self.epsilon or np.sum(self.q[current_state]) <= 0:
            action = random.choice(self.actions[max(0, lastindex-2):min(lastindex+3, len(self.actions))])
            # action = random.choice(self.actions)
        else:
            # if np.sum(self.q[current_state]) > 0:
            # print("q row:", [int(e) for e in self.q[current_state]])
            maxq = max(self.q[current_state])
            indices = [i for i, e in enumerate(self.q[current_state]) if e == maxq]
            action = self.actions[random.choice(indices)]
            # print("maximual action:", action)

        # print([element.name, current_state, self.actions.index(action), self.time])
        self.recentstateactions[element.name].append(tuple([current_state, self.actions.index(action), self.time]))
        # print("Action:", element.name, action)
        self.actionlist.append(action)
        self.elementAction[element.name] = (action, self.time)
        return 6*[action]














