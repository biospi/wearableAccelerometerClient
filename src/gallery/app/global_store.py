# global_store.py

class GlobalStore:
    _instance = None
    battlvl = 0  # Initialize your integer value here

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(GlobalStore, cls).__new__(cls)
        return cls._instance
