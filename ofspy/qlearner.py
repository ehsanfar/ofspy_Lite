import numpy as np
from itertools import product
import random
from collections import deque, defaultdict

class Qlearner():
    def __init__(self, federate, numericactions, memoryset, sectors = list(range(1,7))):
        self.states = list(product(sorted(list(memoryset)), sectors))
        self.stateDict = {e: i for i,e in enumerate(self.states)}
        # print(numericactions, self.states)
        self.q = np.zeros((len(self.states), len(numericactions)))

        self.gamma = 1
        self.alpha = 0.9
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
        self.elementAction = {}



    def update_q(self, element, rewards):
        self.time = element.federateOwner.time
        name = element.name
        while self.recentstateactions[name] and self.recentstateactions[name][0][2] < self.time - 6:
            self.recentstateactions[name].popleft()
        # current_state = self.stateDict[(int(element.capacity - element.content), element.section)]
        # self.timeStateDict[self.time] = current_state
        # print("recent state actions:", self.recentstateactions[element.name])
        # print("rewards:", rewards)
        for state, action, t in self.recentstateactions[name]:
            qsa = self.q[state, action]
            # print(time, element.timeStateDict[time + 1], self.stateDict[element.timeStateDict[time + 1]])
            new_q = qsa + self.alpha * (rewards/6. + self.gamma * max(self.q[self.stateDict[element.timeStateDict[t + 1]], :]) - qsa)
            # print("qsa, nextstate, max:", name, qsa, element.timeStateDict[t], element.timeStateDict[t + 1], max(self.q[self.stateDict[element.timeStateDict[t + 1]], :]), new_q)

            self.q[state, action] = new_q
            # print("new q:", state, new_q, [int(e) for e in list(self.q[state])])
            # renormalize row to be between 0 and 1
            # rn = self.q[state] / np.sum(self.q[state])
            # self.q[state] = [round(r, 2) for r in rn]

        # print("SUM OF Q:", self.q.sum())
            # print(self.q[state])


        # print("Q matrix:", self.q)

    def getAction(self, element):
        current_state = self.stateDict[(int(element.capacity - element.content), element.section)]
        self.time = element.federateOwner.time
        # valid_moves = self.r[current_state] >= 0
        if self.random_state.rand() < self.epsilon or np.sum(self.q[current_state]) <= 0:
            action = random.choice(self.actions)
        else:
            # if np.sum(self.q[current_state]) > 0:
            action = self.actions[np.argmax(self.q[current_state])]
            # print("maximual action:", action)

        # print([element.name, current_state, self.actions.index(action), self.time])
        self.recentstateactions[element.name].append(tuple([current_state, self.actions.index(action), self.time]))
        # print("Action:", action)
        self.actionlist.append(action)
        return 6*[action]














