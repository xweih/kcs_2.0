# The King Crab Hack (KCH) 2.0
## An Updated Model

<img src="images/kcs_2.0.png" width="1000" >

## Background
Since the release of the orginal [KCH problem](https://github.com/xweih/kcs), the menus of the restaurant has changed to some degree. Consequently, it affected the utility of my previous model. So in this post, I outline the menu change, and the subsequent model updates. 


## Menu Change

Other than the price increase, the old menus, including Build Your Own Seafood Bag and Seafood Combos, remain the same. However, new order options have been added as follows. 

1. The option to order crabs (snow crab, king crab, and dungenese crab) by the half-pound. Previously, one can only order these items by the whole-pound.

| Build Your Own Seafood Bag  | Unit Price | 
| :------  | ---: | 
| king crab (1/2 lb)   |	30.99|
| snow crab (1/2 lb)    |	19.99|
| dungeness crab (1/2 lb)|19.99|

2. Additional single items: egg and broccoli

3. For the ordering option "Build Your Own Seafood Bag", each bag will receive up to 1 corn and 1 potato (2 items in total) for free, if any seafood item is ordered. 


## Model Updates (KCH 2.0)

1. The new model incorperate all menu changes described above.

2. New items are now available in customer orders: eggs, broccoli

3. The new model will generate alert when an improper order quantity is entered. For example, if a non-integer valued quantity is entered for item "crawfish", the program will stop.   


## The new "build your own seafood bag" price
```javascript
# The first corn and potato will be free, if there is a seafood order
# Reduced the demand quantity of corn and potato by 1, by using a new df

df_D_modify = D.copy()

if df_D_modify.loc['corn','pound'] >=1 and np.sum(label_seafood * demandLBS) >=1:
    df_D_modify.loc['corn','pound'] = df_D_modify.loc['corn','pound'] - 1
    
if df_D_modify.loc['potato','pound'] >=1 and np.sum(label_seafood * demandLBS) >=1:
    df_D_modify.loc['potato','pound'] = df_D_modify.loc['potato','pound'] - 1

# BYOB Price of the order can be computed immediately
# Variable "demandLBS_disc" is used instead of "demandLBS"

demandLBS_disc = df_D_modify['pound'].to_numpy()
totalByob = np.inner(priceByob, demandLBS_disc)
```

## The code

The above mathematical model is encoded in Python Jupyter notebook with [CVXPY](https://www.cvxpy.org/) as the solver. Adding the following routine is necessary. 

```javascript
import numpy as np
import pandas as pd
import math
```
Import CVXPY library, assuming CVXPY has been installed properly.

```javascript
import cvxpy as cp
```
 
First, I preprocess the data, i.e., the KCS's menu pricing information and my required order that are contained in a few csv files. 

```javascript
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
```

Next, we clean data a little bit. 

```javascript
# Data imputation
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
```

"Customer order" info needs modifying on two places (1)(2)

```javascript
# (1) Split number of "tails" into numbers of "tail_1" and "tail_2"

num_tails = D[D['seafood'] == 'tail']['pound'].values[0]
num_1_tail = num_tails % 2
num_2_tail = int(num_tails/2)

# (2) Crawfish, clams, and mussels have the same price and are interchangable
# Combine these items to form a new item, "ccm"

ccm_lbs = D[D['seafood'] == 'crawfish']['pound'].values[0] \
        + D[D['seafood'] == 'clams']['pound'].values[0] \
        + D[D['seafood'] == 'mussels']['pound'].values[0]

```

```javascript
# Add "df_add" to the D dataframe and delete "crawfish", "clams", "mussels", and "tail" from it.

dict_add = {'seafood':['ccm','tail_1','tail_2'], 
            'pound': [ccm_lbs, num_1_tail, num_2_tail]
           }

df_add = pd.DataFrame(dict_add)

D = pd.concat( [D, df_add], axis=0, ignore_index=True )

D.drop(D[D['seafood'] == 'crawfish'].index, inplace=True)
D.drop(D[D['seafood'] == 'clams'].index, inplace=True)
D.drop(D[D['seafood'] == 'mussels'].index, inplace=True)
D.drop(D[D['seafood'] == 'tail'].index, inplace=True)

# Cast all numeric info into numpy arrays for modeling (CVX requirement)

comboMakeUp = A.values
priceByob = C['price'].to_numpy()
priceCombo = P['price'].to_numpy()

D = D.set_index('seafood')
D.sort_index(inplace=True)
demandLBS = D['pound'].to_numpy()

# BYOB Price of the order can be computed immediately

totalByob = np.inner(priceByob, demandLBS)

```

Finally, we are able to construct a problem in CVXPY

```javascript
# Construct a CVXPY problem with the SCIP backend to solve the MIP

# Define decision variables, x[i]: build your own bag seafood, y[j]: numbers of combos

x = cp.Variable(num_seafood, integer=True)
y = cp.Variable(num_combo, integer=True)

# Define objective function

obj_expr = cp.sum(priceCombo @ y) + cp.sum(priceByob @ x)
objective = cp.Minimize(obj_expr)

# Define constraints

constraints = [ comboMakeUp @ y + x >= demandLBS,
              x >=0,
              y>= 0
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

print( )
print("=============== THE KING CRAB HACK ===============")
print( )
print("Here's everything you ordered: ")
print( )
print(order)
print( )
print("'Build Your Own Bag' would have cost: $", round(totalByob,2))
print("\n" "Here's what you should order to get a bang for the buck:" "\n")
for j in range(num_combo):
    if y.value[j] != 0: 
        print(combos[j], " = ", int(y.value[j]))
for i in range(num_seafood):
    if x.value[i] != 0: 
        print(seafoods[i], " = ", int(x.value[i]))  
print( )
print("!! Now, your total (objective value) is: $", round(prob.value,2))
print("!! YOU SAVED: $", round(totalByob - prob.value, 2), "(%s)" % format((totalByob - prob.value) / totalByob, ".0%") )
```

## Results


## Discussion

The idea of the MIP model is based on an crucial premise that:

"The combo prices are strictly cheaper than ANY BYOB prices for ordering."

This premise allows the formulation of our problem as a variant of the famous [knapsack Problem](https://en.wikipedia.org/wiki/Knapsack_problem), i.e., a formulation that enjoys all the advantages and elegance of MIP optimization, afterall. 

Now, consider a less "well-designed" menu, in which

