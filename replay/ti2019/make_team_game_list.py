import sys
import numpy as np

games = np.genfromtxt(sys.stdin, delimiter=',', skip_header=1, dtype=int)
teams = np.unique(games[:,-2:])

for team in teams:
    print(team, end=' ')
    for i in np.where(games[:,-1] == team)[0]:
        print("{}_dire.txt".format(games[i,0]), end=' ')
    for i in np.where(games[:,-2] == team)[0]:
        print("{}_radiant.txt".format(games[i,0]), end=' ')
    print()
