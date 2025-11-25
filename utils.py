import numpy as np
from random import randint
import os


class ActivityCounter:
    def __init__(self, threshold, window_size_sec):
        self.threshold = threshold
        self.window_size_sec = window_size_sec
        self.buffer_x = []
        self.buffer_y = []
        self.buffer_z = []
        self.activity_counts = []

    def add_data(self, x, y, z):
        # Append the incoming data point to buffers
        self.buffer_x.append(x)
        self.buffer_y.append(y)
        self.buffer_z.append(z)

        # Process if we have enough data for at least one window
        if len(self.buffer_x) >= self.window_size_sec:
            # Extract window data
            window_x = self.buffer_x[:self.window_size_sec]
            window_y = self.buffer_y[:self.window_size_sec]
            window_z = self.buffer_z[:self.window_size_sec]

            # Remove the processed window data from the buffers
            self.buffer_x = self.buffer_x[self.window_size_sec:]
            self.buffer_y = self.buffer_y[self.window_size_sec:]
            self.buffer_z = self.buffer_z[self.window_size_sec:]

            # Calculate magnitude of the window
            magnitude = np.sqrt(np.square(window_x) + np.square(window_y) + np.square(window_z))

            # Count the number of times the magnitude exceeds the threshold
            count = np.sum(magnitude > self.threshold)
            self.activity_counts.append(int(count))

    def get_activity_counts(self):
        return self.activity_counts
