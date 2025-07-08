import matplotlib.pyplot as plt
import numpy as np
import pickle
import random
import subprocess
import torch as T
from datetime import datetime
import os



def writeLineInFile(file, content, shouldPrint=True):
    ausgabe = ""
    
    for c in content:
        if shouldPrint:
            print(c)
        ausgabe += c + "\n"

    f = open(file+".txt", "a")
    f.write(ausgabe)
    f.close()
    
def plot_learning_curve_reward(x, scores, figure_file, title):
    running_avg = np.zeros(len(scores))
    for i in range(len(running_avg)):
        running_avg[i] = np.mean(scores[max(0, i-50):(i+1)])
    plt.plot(x, running_avg)
    plt.title(str(title))
    plt.savefig(figure_file)
    plt.close('all')


def clear_output_folder(folder_path):
    """
    Löscht alle Dateien im angegebenen Ordner.
    :param folder_path: Pfad des Ordners, der geleert werden soll.
    """
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)  # Ordner erstellen, falls er nicht existiert
    else:
        for file in os.listdir(folder_path):
            file_path = os.path.join(folder_path, file)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)  # Datei löschen
                    #print(f"Gelöscht: {file_path}")
            except Exception as e:
                print(f"Fehler beim Löschen von {file_path}: {e}")