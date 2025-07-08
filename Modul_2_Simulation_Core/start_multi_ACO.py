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

#Meta-heuritics
from _solver.Meta_ACO_Routing import * 
from _solver.Meta_ACO_DBSCAN_Routing import *


import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"



def startMulti():

    myConfig = envConfiguration()

    save_path = "output_images"
    export_img = False
    export_json_and_die = True

    width= 2
    height=3
    num_pickers=4

    #DS1
    DS_Name = "DS01"
    min_orders=4
    max_orders=6
    max_steps = 400

    #DS2
    #DS_Name = "DS02"
    #min_orders=6
    #max_orders=8
    #max_steps = 600 

    #DS3
    #DS_Name = "DS03"
    #min_orders=8
    #max_orders=10
    #max_steps = 800

    Warehouse_Architectures=[
        #"Heik_Traditional_1",
        "Heik_Traditional_2",
        "Heik_Traditional_3",
        "Heik_Fisebone",
        "Heik_Flying-V",
        "Heik_Inverted-V",
    ]

    for Warehouse_Architecture in Warehouse_Architectures:


        Warehouse_Architecture = "Heik_Traditional_1" 
        Eval_Folder = "Dataset/" + Warehouse_Architecture + "/" + DS_Name + "/"
        ACO_filename = "ACO_" +Warehouse_Architecture+ "_" + DS_Name + ".pkl"


        env = WarehouseEnv(min_orders=min_orders, max_orders=max_orders, json_file="_layouts/"+Warehouse_Architecture+".json")
        
        coordinators = [
            # Meta
            ACORoutingCoordinator(env),
            #ACODbscanRoutingCoordinator(env)
        ]

        logfileName = "exp_" + Warehouse_Architecture + "_" + DS_Name 

        

        for coordinator in coordinators:
            detaillogfileName = "exp_" + Warehouse_Architecture + "_" + DS_Name + "_" + coordinator.__class__.__name__


            writeLineInFile(logfileName, ["Start - " + coordinator.__class__.__name__])

            episodes_steps = []
            calc_duration = []

            for episode in range(1, myConfig.ammount_of_eval_episodes + 1):


                if export_img:
                    clear_output_folder(save_path)  # Löscht alle vorherigen Bilder

                if DS_Name != "":
                    with open(Eval_Folder + DS_Name +'_E'+ f"{episode:04}" + '.pkl', 'rb') as f:
                        saved_order = pickle.load(f)


                # Env zurücksetzten  
                initial_order, state, done = env.reset()
            
                if DS_Name != "":
                    # Bestellung wiederherstellen 
                    env.load_order(saved_order)

                #initial_order, state, done = env.getInit()
                #availableActionSpace = env.get_valid_actions_one_hot()
                



                if export_img:            
                    env.visualize(save_path=save_path, step=000000)



                #####################################
                # Select coordinator
                #####################################
                #coordinator = SShapeCoordinator(env)        
                #coordinator = ReturnCoordinator(env)        
                #coordinator = MidPointCoordinator(env)
                #coordinator = OptimalRoutingCoordinator(env)
                load_pheromones(coordinator, ACO_filename)    
                





                
                #####################################
                # Plan the routes and measure elapsed time
                #####################################
                start = time.perf_counter_ns()        
                paths = coordinator.plan_picker_paths()
                end = time.perf_counter_ns()
                dauer_ns = end - start
                dauer_s = dauer_ns / 1e9  # Umrechnung in Sekunden
                calc_duration.append(dauer_s)
                
                #####################################
                # Apply the plan to the environment
                #####################################
                env.set_planed_paths(paths)

                save_pheromones(coordinator, ACO_filename)



                #####################################
                #Execution of the simulation 
                #####################################
                for step in range(max_steps): 
                    if export_img:
                        env.visualize(save_path=save_path, step=step)

                    env.execute_plan()            

                    # Check: Sind alle Pfade abgeschlossen?
                    if all(not path for path in coordinator.paths):
                        break
                
                writeLineInFile(detaillogfileName, ["Epi=" + str(episode) + " t="  + str(step) + " Planningtime=" + str(dauer_s) + " Watingtimes=" +str(env.get_wait_times())])
                episodes_steps.append(step)
                
                if export_img:
                    env.visualize(save_path=save_path, step=step+1)      

                #####################################
                #Export for the Web GUI
                #####################################
                if export_json_and_die :       
                    env.export_json("Result_" + str(DS_Name) + " _Epi" + f"{episode:04d}" + "_Solver_" + coordinator.__class__.__name__ + ".json")
                    die()
            #####################################
            # Calculation of the statistics
            #####################################
            mean_calc_duration = sum(calc_duration) / len(calc_duration)    
            mean_episodes_steps = sum(episodes_steps) / len(episodes_steps)

            writeLineInFile(logfileName, [
                "mean_calc_duration =" + str(mean_calc_duration),
                "mean_episodes_steps =" + str(mean_episodes_steps),
                "",
                "" 
                    ])

def die():
     raise Exception("Program has ended")

if __name__ == "__main__":
    startMulti()