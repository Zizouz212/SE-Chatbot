import os
import pickle

base = os.path.join(os.path.dirname(os.path.abspath(__file__)))
data_file = "Points_Data.p"
path = os.path.join(base, data_file)

def save(filepath, obj):
    """Pickles the object"""
    with open(filepath, "w+") as f:
        pickle.dump(obj, f)

def load(filepath):
    """Loads the pickled object back to proper form"""
    with open(filepath, "r") as f:
        return pickle.load(f)

