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

## Results


## Discussion

The idea of the MIP model is based on an crucial premise that:

"The combo prices are strictly cheaper than ANY BYOB prices for ordering."

This premise allows the formulation of our problem as a variant of the famous [knapsack Problem](https://en.wikipedia.org/wiki/Knapsack_problem), i.e., a formulation that enjoys all the advantages and elegance of MIP optimization, afterall. 


