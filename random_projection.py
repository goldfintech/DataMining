"""
Random projection, Assignment 1c
"""
import numpy as np
import matplotlib.pylab as plt
from mpl_toolkits.axes_grid1 import make_axes_locatable
import random, mnist_dataloader
from scipy.spatial.distance import euclidean
import multiprocessing
import time

"""
load data sets
"""
def load_data_sets():
# load data set
    training_data, validation_data, test_data = mnist_dataloader.load_data()
    training_data_instances = training_data[0]
    training_data_labels = training_data[1]
    test_data_instances = test_data[0]
    test_data_labels = test_data[1]
    
    return training_data_instances, training_data_labels, test_data_instances, test_data_labels

"""
Generate random projection matrix R
@param: k, the reduced number of dimensions
@param: d, the original number of dimensions
@return: R, the generated random projection matrix, k * d size 
"""

def generate_random_projection_matrix(k, d):
    R = np.zeros((k, d), dtype = np.float64)
    for r in np.nditer(R, op_flags=['readwrite']):
        r[...] = 2 * random.randint(0, 1) - 1
    # to be cautious, this is the point the exercise wants us to get
    R *= 1.0 / np.sqrt(k)
    
    return R

"""
random projection matrix P into R
@param R: random projection matrix
@param P: matrix to be reduced in dimension
@return: Q: projected matrix of P on R
"""
def random_projection(R, P):
    if R.shape[1] != P.shape[0]:
        return False
    
    print R.shape, P.shape
    
    return np.dot(R, P)

"""
plot distortion
@param training_data_instances: training data instances
"""
def plot_distortion(training_data_instances):
    # dimension of a training data instance
    d = training_data_instances.shape[1]
    # first m instances considered
    m = 20
    
    fig, axes = plt.subplots(1, 1)
    fig.suptitle("Distortion of random projection", fontsize = "x-large")
    
    for k in [50, 100, 500]:
        ## generate random projection matrix
        random_projection_matrix =  generate_random_projection_matrix(k, d)
        ## random projection
        m_instances = training_data_instances[0:m]
        projected_m_instances = np.dot(m_instances, np.transpose(random_projection_matrix))
        # print random_projected_matrix[0], random_projected_matrix.shape
        ## evaluate distortion - line chart
        m_instances_distortions = []
        for i in range(m):
            for j in range(i + 1, m):
                m_instances_distortions.append(euclidean(projected_m_instances[i], projected_m_instances[j]) / euclidean(m_instances[i], m_instances[j]))
        m_instances_distortions = np.array(m_instances_distortions)
        mean, std = np.mean(m_instances_distortions), np.std(m_instances_distortions)
        # line chart
        axes.plot(m_instances_distortions, label = "k=" + str(k))
        axes.plot([0, m_instances_distortions.size], [mean, mean], label = "k=" + str(k) + ", mean = " + str(round(mean, 4)))
        
        print "k = ", k, "distortion =", mean, "+-", std
    axes.set_xlabel("pairs of instances", fontsize = "large")
    axes.set_ylabel("distortion", fontsize = "large")
    axes.legend(loc = "center right", fontsize = "medium")
    plt.show()

"""
classify test_data
@param training_data_instances
@param training_data_labels
@param test_data_instances
@param test_instance_start_index
@param test_instance_end_index
@param classified_results: classified results, shared by different subprocesses
@return: None. Note, the updated classified results array.
"""
def find_nearest_instances_subprocess(training_data_instances, training_data_labels, test_data_instances, test_instance_start_index, test_instance_end_index,\
                                      classified_results):
    # print test_instance_start_index, test_instance_end_index
    for test_instance_index in range(test_instance_start_index, test_instance_end_index):
        test_instance = test_data_instances[test_instance_index]
        # find the nearest training instance with euclidean distance
        minimal_euclidean_distance = euclidean(test_instance, training_data_instances[0])
        minimal_euclidean_distance_index = 0
        for training_instance, training_instance_index in zip(training_data_instances, range(len(training_data_instances))):
            # compute the euclidean distance
            euclidean_distance = euclidean(test_instance, training_instance)
            if euclidean_distance < minimal_euclidean_distance:
                minimal_euclidean_distance = euclidean_distance
                minimal_euclidean_distance_index = training_instance_index
        classified_results[test_instance_index] =\
         training_data_labels[int(minimal_euclidean_distance_index)]

"""
find nearest neighbor algorithm without random projection
@param training_data_instances
@param training_data_labels
@param test_data_instances
@param test_data_labels
@return: classified_results, error_rate, and confusion_matrix
"""
def find_nearest_instances(training_data_instances, training_data_labels, test_data_instances, test_data_labels):
    start_time = time.time()
    # speed using multiple processes
    NUMBER_OF_PROCESSES = 4
    processes = []
    # shared by different processes, to be mentioned is that
    # global variable is only read within processes
    # the update of global variable within a process will not be submitted 
    classified_results = multiprocessing.Array('i', len(test_data_instances), lock = False)
    test_data_subdivisions = range(0, len(test_data_instances) + 1,\
                                    int(len(test_data_instances) / NUMBER_OF_PROCESSES))
    test_data_subdivisions[-1] = len(test_data_instances)
    for process_index in range(NUMBER_OF_PROCESSES):
        process = multiprocessing.Process(target = find_nearest_instances_subprocess,
                                          args = (training_data_instances,
                                                  training_data_labels,
                                                  test_data_instances,
                                                  test_data_subdivisions[process_index],
                                                  test_data_subdivisions[process_index + 1],
                                                  classified_results))
        process.start()
        processes.append(process)
        
    print "Waiting..."
    # wait until all processes are finished
    for process in processes:
        process.join()
    print "Complete."
    print "--- %s seconds ---" % (time.time() - start_time)
    
    error_count = 0
    confusion_matrix = np.zeros((10, 10), dtype=np.int)
    for test_instance_index, classified_label in zip(range(len(test_data_instances)),\
                                                      classified_results):        
        if test_data_labels[test_instance_index] != classified_label:
            error_count += 1
        confusion_matrix[test_data_labels[test_instance_index]][classified_label] += 1        
        
    error_rate = 100.0 * error_count / len(test_data_instances)
    
    return classified_results, error_rate, confusion_matrix

if __name__ == '__main__':
    multiprocessing.freeze_support()
    training_data_instances, training_data_labels, test_data_instances, test_data_labels = load_data_sets()
    
    ## plot distortion
    # plot_distortion(training_data_instances)
    ## nearest neighbor without random projection
    print "Without random projection"
    classified_results, error_rate, confusion_matrix = find_nearest_instances(training_data_instances, training_data_labels, test_data_instances, test_data_labels)
    print "Error rate:", error_rate
    print "Confusion matrix:", confusion_matrix
    
    ## random projection
    # dimension of a training data instance
    d = training_data_instances.shape[1]
    for k in [50, 100, 500]:
        ## generate random projection matrix
        random_projection_matrix =  generate_random_projection_matrix(k, d)
        ## random projection        
        projected_training_instances = np.zeros((len(training_data_instances), k), dtype = np.float64)
        for i in range(training_data_instances.shape[0]):
            for j in range(projected_training_instances.shape[1]):
                projected_training_instances[i][j] = np.dot(random_projection_matrix[j], training_data_instances[i])
        
        projected_test_instances = np.zeros((len(test_data_instances), k), dtype = np.float64)
        for i in range(test_data_instances.shape[0]):
            for j in range(projected_test_instances.shape[1]):
                projected_test_instances[i][j] = np.dot(random_projection_matrix[j], test_data_instances[i])
        
        classified_results, error_rate, confusion_matrix = find_nearest_instances(projected_training_instances, training_data_labels, projected_test_instances, test_data_labels)
        print "Error rate:", error_rate
        print "Confusion matrix:", confusion_matrix