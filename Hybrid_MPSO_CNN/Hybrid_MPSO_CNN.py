"""
Description:
    Implementation of "Hybrid MPSO-CNN: Multi-level Particle Swarm optimized hyperparameters of Convolutional Neural Network"
    doi: https://doi.org/10.1016/j.swevo.2021.100863
    Using this algorithm for tuning hyper-parameters of deep unfolding network
"""

import random
import math
from keras.models import Sequential
from keras.layers import Conv2D, MaxPooling2D, Dense, Flatten

class Particle_L1:
    def __init__(self, search_space):
        self.nC = random.randint(search_space['nC'][0], search_space['nC'][1])
        self.nP = random.randint(search_space['nP'][0], self.nC)
        self.nF = random.randint(search_space['nF'][0], self.nC)

        self.pos_i = [self.nC, self.nP, self.nF]        # Particle position 
        self.vel_i = [0, 0, 0]                          # Particle velocity
        
        self.pbest_i = self.pos_i                       # Personal best position
        self.pbest_i_F = -float("inf")                  # Personal best fitness
        self.gbest = self.pbest_i                       # Global best position
        self.gbest_F = float('inf')                     # Global best fitness
        self.F_i = -float("inf")                        # Current fitness

        self.swarm_size_lvl2 = 5*self.nC                # Swarm size at Swarm Level-2
        self.swarm_lvl2 = [Particle_L2(search_space) for _ in range(self.swarm_size_lvl2)]

    def update_velocity(self, w, c1, c2):
        r1 = random.uniform(0,1)
        r2 = random.uniform(0,1)
        for i in range(len(self.vel_i)):
            self.vel_i[i] = w*self.vel_i[i] + c1*r1*(self.pbest_i[i] - self.pos_i[i]) + c2*r2*(self.gbest[i] - self.pos_i[i])

    def update_position(self):
        for i in range(len(self.pos_i)):
            self.pos_i[i] += self.vel_i[i]
            self.pos_i[i] = int (self.pos_i[i])
            # self.pos_i[i] = max(bounds[i][0], min(self.pos_i[i], bounds[i][1]))
        
    def __repr__(self):
        return f"nC: {self.nC}, nP: {self.nP}, nF: {self.nF}"

class Particle_L2:
    def __init__(self, search_space):
        self.c_nf = random.randint(*search_space['c_nf'])
        self.c_fs = random.randrange(search_space['c_fs'][0], search_space['c_fs'][1]+1, 2)
        self.c_pp = random.randint(*search_space['c_pp'])
        self.c_ss = random.randint(search_space['c_ss'][0], self.c_fs)
        self.p_fs = random.randrange(search_space['p_fs'][0], search_space['p_fs'][1]+1, 2)
        self.p_ss = random.randint(*search_space['p_ss'])
        self.p_pp = random.randint(search_space['p_pp'][0], self.p_fs)
        self.op   = random.randint(*search_space['op'])

        self.pos_ij = [self.c_nf, self.c_fs, self.c_pp,
                       self.c_ss, self.p_fs, self.p_ss, 
                       self.p_pp, self.op]              # Particle position
        self.vel_ij = [0] * len(self.pos_ij)            # Particle velocity 
        
        self.pbest_ij = self.pos_ij                     # Personal best position
        self.pbest_ij_F = -float("inf")                 # Personal best fitness
        self.gbest = self.pbest_ij                      # Global best position
        self.gbest_F = float('inf')                     # Global best fitness
        self.F_ij = -float("inf")                       # Current fitness

    def evaluate(self, cnn, x_train, y_train):
        return cnn.fitness(x_train, y_train)[1]

    def update_velocity(self, w, c1, c2):
        r1 = random.uniform(0,1)
        r2 = random.uniform(0,1)
        for i in range(len(self.vel_ij)):
            self.vel_ij[i] = w*self.vel_ij[i] + c1*r1*(self.pbest_ij[i] - self.pos_ij[i]) + c2*r2*(self.gbest[i] - self.pos_ij[i])
                             
    def update_position(self):
        for i in range(len(self.pos_ij)):
            self.pos_ij[i] += self.vel_ij[i]
            self.pos_ij[i] = int (self.pos_ij[i])
            # self.pos_ij[i] = max(bounds[i][0], min(self.pos_ij[i], bounds[i][1]))

    def __repr__(self):
        return f"c_nf: {self.c_nf}, c_fs: {self.c_fs}, c_pp: {self.c_pp}, c_ss: {self.c_ss}, p_fs: {self.p_fs}, p_ss: {self.p_ss}, p_pp: {self.p_pp}, op: {self.op}"

class Hybrid_MPSO_CNN:
    def __init__(self, x_train, y_train, x_test, y_test, input_shape, output_shape):
        self.c1 = 2                                     # Social coefficient
        self.c2 = 2                                     # Cognitive coefficient
        self.max_iter_lvl1 = random.randint(5,8)        # Maximum iterations at Swarm Level-1
        self.max_iter_lvl2 = 5                          # Maximum iterations at Swarm Level-2
        self.search_space = {
                             'nC':   (1, 5),            # Number of convolutional layers
                             'nP':   (1, 5),            # Number of pooling layers
                             'nF':   (1, 5),            # Number of fully connected layers
                             'c_nf': (1, 64),           # Number of filters
                             'c_fs': (1, 13),           # Filter Size (odd) 
                             'c_pp': (0, 1),            # Padding pixels (0: "valid", 1: "same")
                             'c_ss': (1, 5),            # Stride Size (< 𝑐_fs)
                             'p_fs': (1, 13),           # Filter Size (odd)
                             'p_ss': (1, 5),            # Stride Size
                             'p_pp': (0, 1),            # Padding pixels (< 𝑝_fs) (0: "valid", 1: "same")
                             'op':   (1, 1024)          # Number of neurons
                            }                           # Range of hyperparameters (Based on Table 1)
        self.swarm_size_lvl1 = 5                        # Swarm size at Swarm Level-1 (nP ≤ nC, nF ≤ nC)
        self.swarm_lvl1 = [Particle_L1(self.search_space) for _ in range(self.swarm_size_lvl1)]
        self.x_train = x_train                          # Training data input
        self.y_train = y_train                          # Training data output
        self.x_test  = x_test                           # Testing data input
        self.y_test  = y_test                           # Testing data output
        self.input_shape = input_shape                  # Input data shape
        self.output_shape = output_shape                # Output data shape

    def calculate_omega(self, t, t_max, alpha=0.2):
        if t < alpha * t_max:
            return 0.9
        return 1 / (1 + math.e ** ((10 * t - t_max) / t_max))

    def level1_optimize(self):
        for t in range(self.max_iter_lvl1):
            w = self.calculate_omega(t, self.max_iter_lvl1)
            for i, particle_l1 in enumerate(self.swarm_lvl1):
                particle_l2_gbest, particle_l1.F_i = self.level2_optimize(particle_l1, w)
                if particle_l1.F_i > particle_l1.pbest_i_F:
                    particle_l1.pbest_i_F = particle_l1.F_i
                    particle_l1.pbest_i = particle_l1.pos_i
                    if particle_l1.F_i > particle_l1.gbest_F:
                        particle_l1.gbest_F = particle_l1.F_i
                        particle_l1.gbest = particle_l1.pos_i

        return particle_l1.gbest, particle_l2_gbest, particle_l1.F_i
        
    def level2_optimize(self, particle_l1, w):
        for t in range(self.max_iter_lvl2):
            for i, particle_l2 in enumerate(particle_l1.swarm_lvl2):
                particle_l2.update_velocity(w, self.c1, self.c2)
                particle_l2.update_position()
                cnn = CNN(particle_l1.pos_i, particle_l2.pos_ij)
                print(particle_l1.pos_i, particle_l2.pos_ij)
                cnn.buid_model(self.input_shape, self.output_shape)
                cnn.train_model(self.x_train, self.y_train, epochs=5, batch_size=256)
                particle_l2.F_ij = particle_l2.evaluate(cnn, self.x_train, self.y_train)
                if particle_l2.F_ij > particle_l2.pbest_ij_F:
                    particle_l2.pbest_ij_F = particle_l2.F_ij
                    particle_l2.pbest_ij = particle_l2.pos_ij
                    if particle_l2.F_ij > particle_l2.gbest_F:
                        particle_l2.gbest_F = particle_l2.F_ij
                        particle_l2.gbest = particle_l2.pos_ij
        
        return particle_l2.gbest, particle_l2.F_ij
    
    def run(self):
        lvl1_hp, lvl2_hp, fitness = self.level1_optimize()
        return lvl1_hp, lvl2_hp, fitness
    
    def __repr__(self):
        return f"Max_iter_lvl1: {self.max_iter_lvl1}, Max_iter_lvl2: {self.max_iter_lvl2}"

class CNN:
    def __init__(self, l1_hyperparameters, l2_hyperparameters):
        self.nC = l1_hyperparameters[0]                 # number of convolution layers
        self.nP = l1_hyperparameters[1]                 # number of pooling layers
        self.nF = l1_hyperparameters[2]                 # number of fully connected layers
        self.c_nf = l2_hyperparameters[0]               # number of filters in the convolutional layer
        self.c_fs = l2_hyperparameters[1]               # size of filter/kernel in the convolutional layer
        self.c_pp = l2_hyperparameters[2]               # padding (valid or same) requirement in the convolutional layer
        self.c_ss = l2_hyperparameters[3]               # size of stride in the convolutional layer
        self.p_fs = l2_hyperparameters[4]               # size of a filter in the max pooling layer
        self.p_ss = l2_hyperparameters[5]               # size of stride in the max-pooling layer
        self.p_pp = l2_hyperparameters[6]               # padding pixels in pooling layer
        self.op   = l2_hyperparameters[7]               # number of output neurons in the fully connected layer

        self.model = Sequential()

    def buid_model(self, input_shape, output_shape):
        for i in range(self.nC):
            self.model.add(Conv2D(filters = self.c_nf, 
                                  kernel_size = (self.c_fs, self.c_fs), 
                                  strides = (self.c_ss, self.c_ss), 
                                  padding = 'valid' if self.c_pp == 0 else 'same', 
                                  activation = 'relu'))
            
            if i < self.nP:
                self.model.add(MaxPooling2D(pool_size = (self.p_fs, self.p_fs), 
                                            strides = (self.p_ss, self.p_ss), 
                                            padding = 'valid' if self.p_pp == 0 else 'same'))
                                                   
        self.model.add(Flatten())
        
        for i in range(self.nF):
            self.model.add(Dense(units = self.op if i < self.nF-1 else output_shape, 
                                 activation = 'relu' if i < self.nF-1 else 'softmax'))
        
        return self.model

    def train_model(self, x_train, y_train, epochs=20, batch_size=64):
        self.model.compile(optimizer='adam', 
                           loss='mse', 
                           metrics=['accuracy'])

        self.model.fit(x_train, y_train, epochs=epochs, batch_size=batch_size, validation_split=0.2)

    def fitness(self, x_test, y_test):
        return self.model.evaluate(x_test, y_test)

    def __str__(self):
        model_summary = (f"nC: {self.nC}\n"
                         f"nP: {self.nP}\n"
                         f"nF: {self.nF}\n"
                         f"c_nf: {self.c_nf}\n"
                         f"c_fs: {self.c_fs}\n"
                         f"c_pp: {self.c_pp}\n"
                         f"c_ss: {self.c_ss}\n"
                         f"p_fs: {self.p_fs}\n"
                         f"p_ss: {self.p_ss}\n"
                         f"p_pp: {self.p_pp}\n"
                         f"op: {self.op}\n")
        return model_summary, str(self.model.summary())
