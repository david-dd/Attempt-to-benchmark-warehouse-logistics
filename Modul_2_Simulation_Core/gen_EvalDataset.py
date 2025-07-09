import numpy as np
import random
from datetime import datetime
from collections import deque
import tkinter as tk
from tkinter import messagebox
import time
from itertools import permutations
import heapq
import copy

from _config import envConfiguration    
from _env import *
from _utilities import *
from _picker import PickerCoordinator
from _solver.S_Shape_Routing import *
from _solver.Return_Routing import *
#from _solver.Largest_Gap_Routing import *
from _solver.Mid_Point_Routing import *
from _solver.Optimal_Routing import *


import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"




def startMulti():

    myConfig = envConfiguration()

    DS_Name = "DS01"
    min_orders=4
    max_orders=6
    
    #DS_Name = "DS02"
    #min_orders=6
    #max_orders=8

    #DS_Name = "DS03"
    #min_orders=8
    #max_orders=10


    Warehouse_Architectures=[
        "Heik_Traditional_1",
        #"Heik_Traditional_2",
        #"Heik_Traditional_3",
        #"Heik_Fisebone",
        #"Heik_Flying-V",
        #"Heik_Inverted-V",
    ]

    for Warehouse_Architecture in Warehouse_Architectures:



        env = WarehouseEnv(min_orders=min_orders, max_orders=max_orders, json_file="_layouts/"+Warehouse_Architecture+".json")
        
        out_folder = "Dataset/" + Warehouse_Architecture + "/" + DS_Name + "/"
        clear_output_folder(out_folder)

        for episode in range(1, myConfig.ammount_of_eval_episodes+1):

            # Neues Szenario generieren    
            initial_order, state, done = env.reset()

            with open(out_folder + DS_Name +'_E'+ f"{episode:04}" + '.pkl', 'wb') as f:
                pickle.dump(initial_order, f)
                print("Erstellt für epi=", episode)

            

if __name__ == "__main__":
    startMulti()