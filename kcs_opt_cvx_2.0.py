# -*- coding: utf-8 -*-
"""
The King Crab Hack 2.0

Created on Fri Jun 14 09:33:47 2024

@author: Xiaowei Hu
"""

import numpy as np
import pandas as pd
import cvxpy as cp
import math

A = pd.read_csv('input/combos_v1.csv')
C = pd.read_csv('input/menu_byob_v1.csv')
P = pd.read_csv('input/menu_combo_v1.csv')
my_order = pd.read_csv('input/cust_order_v1.csv')

# First, check if all the customer orders are legal, i.e., in proper quantity
my_order = my_order.set_index('item')

# These items must be order by the whole pound or by each item
int_items = ['crawfish','mussels','clams','tail','lob_live','scallops','shrimp_wh','shrimp_hs','corn','potato','sausage','egg','broccoli']

# To ensure the order quantities are legal
# Print alert if: the order qty is NOT "nan" AND is NOT an integer
for item in int_items: 
    if np.isfinite(my_order.loc[item,'pound']) and my_order.loc[item, 'pound'] != int(my_order.loc[item, 'pound']):
        print("ATTENTION:",item, "must be ordered by the whole pound; it cannot be", my_order.loc[item,'pound'], 'lbs. Please re-enter.')
        raise SystemExit("Please re-enter the order quantity!")
        
A = A.fillna(0)
A = A.set_index('combo')
A.sort_index(inplace=True)
A = A.reindex(sorted(A.columns), axis=1)

C = C.set_index('item')
C.sort_index(inplace=True)

P = P.set_index('combo')
P.sort_index(inplace=True)

# Total numbers of seafood types and combos

num_items = len(C)
num_combos = len(P)

items = C['price'].keys().tolist()
items[items.index('ccm')] = 'crawfish-clams-mussels'
combos = P['price'].keys().tolist()

# "Customer order" info needs modifying on two places (1)(2)
my_order.reset_index(inplace=True)
D = my_order.fillna(0)

# (1) Split number of "tails" into numbers of "tail_1" and "tail_2"

num_tails = D[D['item'] == 'tail']['pound'].values[0]
num_1_tail = num_tails % 2
num_2_tail = int(num_tails/2)

# (1.1) Split number of "king" into numbers of "king" and "king_half"

num_king = D[D['item'] == 'king']['pound'].values[0]
num_king_one = int(num_king)
num_king_half = math.ceil(num_king - num_king_one)

# (1.2) Split number of "snow" into numbers of "snow" and "snow_half"

num_snow = D[D['item'] == 'snow']['pound'].values[0]
num_snow_one = int(num_snow)
num_snow_half = math.ceil(num_snow - num_snow_one)

# (1.3) Split number of "dung" into numbers of "dun" and "dun_half"

num_dun = D[D['item'] == 'dung']['pound'].values[0]
num_dun_one = int(num_dun)
num_dun_half = math.ceil(num_dun - num_dun_one)

# (2) Crawfish, clams, and mussels have the same price and are interchangable
# Combine these items to form a new item, "ccm"

ccm_lbs = D[D['item'] == 'crawfish']['pound'].values[0] \
        + D[D['item'] == 'clams']['pound'].values[0] \
        + D[D['item'] == 'mussels']['pound'].values[0] 

# Add "df_add" to the D dataframe and delete "crawfish", "clams", "mussels", and "tail" from it.

dict_add = {'item':['ccm','tail_1','tail_2','king_one','king_half','snow_one','snow_half','dung_one', 'dung_half'], 
            'pound': [ccm_lbs, num_1_tail, num_2_tail, num_king_one, num_king_half, num_snow_one, num_snow_half, num_dun_one, num_dun_half]
           }

df_add = pd.DataFrame(dict_add)

D = pd.concat( [D, df_add], axis=0, ignore_index=True )

D.drop(D[D['item'] == 'crawfish'].index, inplace=True)
D.drop(D[D['item'] == 'clams'].index, inplace=True)
D.drop(D[D['item'] == 'mussels'].index, inplace=True)
D.drop(D[D['item'] == 'tail'].index, inplace=True)
D.drop(D[D['item'] == 'king'].index, inplace=True)
D.drop(D[D['item'] == 'snow'].index, inplace=True)
D.drop(D[D['item'] == 'dung'].index, inplace=True)

# Cast all numeric info into "numpy arrays" for modeling (CVX requirement)
# label_seafood indicates whether an item is a seafood

comboMakeUp = A.values
priceByob = C['price'].to_numpy()
label_seafood = C['seafood'].to_numpy()
priceCombo = P['price'].to_numpy()

D = D.set_index('item')
D.sort_index(inplace=True)
demandLBS = D['pound'].to_numpy()

# maybe?
num_corns = D.loc['corn','pound']
num_pots = D.loc['potato','pound']

# The first corn and potato will be free, if there is a seafood order

df_D_modify = D.copy()

if df_D_modify.loc['corn','pound'] >=1 and np.sum(label_seafood * demandLBS) >=1:
    df_D_modify.loc['corn','pound'] = df_D_modify.loc['corn','pound'] - 1
    
if df_D_modify.loc['potato','pound'] >=1 and np.sum(label_seafood * demandLBS) >=1:
    df_D_modify.loc['potato','pound'] = df_D_modify.loc['potato','pound'] - 1    

# The demand quantity with corn and potato reduced by 1

demandLBS_disc = df_D_modify['pound'].to_numpy()

# BYOB Price of the order can be computed immediately
# Condition: if there is a seafood order, *up to one* corn and one potato is free!
# so variable "demandLBS_disc" is used instead of "demandLBS"

totalByob = np.inner(priceByob, demandLBS_disc)

# Construct a CVXPY problem with the SCIP backend to solve the MIP

# Define decision variables, x[i]: build your own bag seafood, y[j]: numbers of combos

x = cp.Variable(num_items, integer=True)
y = cp.Variable(num_combos, integer=True)
z = cp.Variable(boolean=True)        

# Define objective function

obj_expr = cp.sum(priceCombo @ y) + cp.sum(priceByob @ x) - z * (0.75+0.55)
objective = cp.Minimize(obj_expr)

# Define constraints
M = 1000000

constraints = [ comboMakeUp @ y + x >= demandLBS,
                #cp.sum(label_seafood @ x) <= M * z ,
                cp.sum(label_seafood @ x) >= 2 * z - 1 ,
                #x[2] <= M * z,
                #x[9] <= M * z,
                x[2] >= 2 * z - 1 ,
                x[9] >= 2 * z - 1 ,
                x >= 0,
                y >= 0
              ]

# Call the solver

prob = cp.Problem(objective, constraints)
prob.solve()

# Display the solution

print("Status: ", prob.status)
print("The optimal value is:", prob.value)
print("A solution x is")
print(x.value)
print("A solution y is")
print(y.value)
print("A solution z is")
print(z.value)

print( )
print("=============== THE KING CRAB HACK ===============")
print( )
print("Here's everything you ordered: ")
print( )
print(D[D['pound']>0])
print( )
print("'Build Your Own Bag' would have cost: $", round(totalByob,2))
print("\n" "Here's what you should order to get a bang for the buck:" "\n")
for j in range(num_combos):
    if y.value[j] != 0: 
        print(combos[j], " = ", int(y.value[j]))
for i in range(num_items):
    if x.value[i] != 0: 
        print(items[i], " = ", int(x.value[i]))  
if z.value == 1:
    print("Free items: 1 corn and 1 potato")
print( )
print("!! Now, your total (objective value) is: $", round(prob.value,2))
print("!! YOU SAVED: $", round(totalByob - prob.value, 2), "(%s)" % format((totalByob - prob.value) / totalByob, ".0%") )