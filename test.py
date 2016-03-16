#!/usr/bin/env python3

from openslots.core import Game, LinePay, ScatterPay, Symbol, Reel
seven = Symbol('7')
bell = Symbol('B')
orange = Symbol('O')
melon = Symbol('M')
plum = Symbol('P')
cherry = Symbol('Ch')
bar = Symbol('BAR')
wbar = Symbol('BAR', True, ['M', 'Ch', '7'])
paylines = [[1,1,1],[0,0,0],[2,2,2]]
rules = []
rules.append(LinePay(cherry, [2, 5], paylines))
rules.append(LinePay(orange, [0, 0, 10], paylines))
rules.append(LinePay(plum, [0, 0, 14], paylines))
rules.append(LinePay(bell, [0, 0, 18], paylines))
rules.append(LinePay(melon, [0, 0, 20], paylines))
rules.append(LinePay(bar, [0, 0, 100], paylines))
rules.append(LinePay(seven, [0, 0, 200], paylines))
reels = []
reel1 = [seven, bell, orange, melon, orange, plum, cherry, bar, orange, melon, orange, plum, cherry, bar, orange, melon, orange, plum, cherry, bar, orange, melon]
reel2 = [seven, orange, melon, plum, melon, bell, cherry, bar, melon, plum, melon, bell, cherry, bar, melon, plum, melon, bell, cherry, bar, melon, plum]
reel3 = [seven, plum, bell, wbar, bell, melon, bell, orange, bell, melon, bell, orange, bell, melon, bell, orange, bell, melon, bell, orange, bell, melon]
reels.append(Reel(reel1))
reels.append(Reel(reel2))
reels.append(Reel(reel3))
g = Game(reels, rules)

choice = ''
while choice.lower() != 'x':
    print('I) Insert credits')
    print('1) Bet one')
    print('2) Bet two')
    print('3) Bet three')
    print('X) Cash out')
    choice = input('Choice: ')
    
    if choice.lower() == 'i':
        num = int(input('How many? '))
        g.add_credits(num)
        print('Credits: ', g.meters.credits)
    elif choice == '1':
        g.spin(1, 1)
    elif choice == '2':
        g.spin(2, 1)
    elif choice == '3':
        g.spin(3, 1)
    elif choice.lower() == 'x':
        g.cash_out()
        g.rng.stop_cycle()
        print("Thanks for playing!")

