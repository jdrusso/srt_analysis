import sys, getopt
from collections import OrderedDict
import matplotlib.pyplot as plt
import numpy as np

#These values are adjust to ignore the first and last 10 data points, since they
#   go to 0 and are bad data.

#Index of first temperature value
TEMP_OFFSET = 20
#Number of bins of data to gather per line from file
NUM_CHANNELS = 135

# Filtering cutoffs. This means filter the first LOW_CUTOFF, and the last
# HIGH_CUTOFF data points from the dataset

# These are some sample values
LOW_CUTOFF = 45
HIGH_CUTOFF = 23

FILTER_POLYNOMIAL_DEGREE = 3

def parse(filename):

    file = open(filename)

    i = 0
    spacing = -1
    startFreq = -1

    spectra = OrderedDict()

    while True:
        line = file.readline()

        if not line: break
        if line[0] == '*': continue

        splitline = line.split()

        #Values come in timestamp | elevation | azimuth | unused offset | unused offset
        #    / Starting frequency (MHz) / spacing (MHz) / mode / number of channels / temperatures

        if startFreq == -1:
            startFreq = splitline[5]
            spacing = splitline[6]
            firstRun = True

        #Iterate through each bin, and add its value to the spectra
        for k in range(NUM_CHANNELS):
            frequency = float(startFreq) + float(k)*float(spacing)

            #Store results of measurements in dict.
            # Dict is of format {frequency: [list of all values]}
            if firstRun:
                spectra[str(frequency)] = list()

            spectra[str(frequency)].append(float(splitline[k+TEMP_OFFSET]))

        firstRun = False
        i+=1

    print("%d lines of data found." % i)

    means = OrderedDict()
    print("Frequency\t\tMean Temperature")
    for key in spectra.keys():
        means[key] = sum(spectra[key])/len(spectra[key])
        print("%8s\t\t%s" % (key, means[key]))

    return means

# Returns an OrderedDict of datapoints from the input file, where each point
#   below LOW_CUTOFF and each point above HIGH_CUTOFF is removed.
def threshold(means):

    newmeans = list()

    for i in range(len(means)):
        if  i > LOW_CUTOFF and i < len(means) - HIGH_CUTOFF:
            newmeans.append(means[i])

    return newmeans



# Generate polyfit equation for background noise based on points outside the
#   LOW_CUTOFF -> HIGH_CUTOFF range, and subtract that from the datapoints.
def datafilter(means, thresholded):

    # Make a list of only the values that are thresholded *out*. We will calculate
    #   background noise from these.

    x = [float(means[i][0]) for i in range(len(means))
        if i < LOW_CUTOFF or i > len(means) - HIGH_CUTOFF]

    y = [float(means[i][1]) for i in range(len(means))
        if i < LOW_CUTOFF or i > len(means) - HIGH_CUTOFF]


    # This generates an equation which should estimate the background noise
    #   for any given frequency.
    polyfilter = np.polyfit(x, y, FILTER_POLYNOMIAL_DEGREE)
    polyeqn = np.poly1d(polyfilter)

    print("Polynomial approximation of noise is ")
    print(polyeqn)

    for i in range(len(means)):

        corrected = means[i][1] - polyeqn(float(means[i][0]))

        # print("Correcting %5f by %5f" % (means[i][1], polyeqn(float(means[i][0]))))
        means[i] = (means[i][0], corrected)

    for i in range(len(thresholded)):
        corrected = thresholded[i][1] - polyeqn(float(thresholded[i][0]))
        thresholded[i] = (thresholded[i][0], corrected)

    return thresholded, means, polyfilter



# Apply some thresholding and filtering to the dataset.
def processdata(means):

    filtered = threshold(means)

    filtered, filteredmeans, eqn = datafilter(means, filtered)

    return filtered, filteredmeans, eqn




def main(argv):

    filename = ""

    # YOLO
    global LOW_CUTOFF
    global HIGH_CUTOFF

    try:
        opts, args = getopt.getopt(argv,"hi:l:t:",["input="])
    except getopt.GetoptError:
        print("parser.py -i <input file> -l <lower_threshold> -t <upper_threshold>")
        sys.exit(2)

    for opt, arg in opts:
        if opt == '-h':
            print("parser.py -i <input file> -l <lower_threshold> -t <upper_threshold>")
            sys.exit(0)
        elif opt in ("-i", "--input"):
            filename = arg
        elif opt in ("-l"):
            LOW_CUTOFF = int(arg)
        elif opt in ("-t"):
            HIGH_CUTOFF = int(arg)

    print("Parsing file %s\n" % filename)

    data_means = parse(filename)

    # Process data into a list of tuples
    unfiltered = [(key, data_means[key]) for key in data_means.keys()]

    # Make a deep copy
    means_tuple = [x for x in unfiltered]

    # Process/filter data
    processed, processedmeans, polyfilter = processdata(means_tuple)

    # Calculate average of polyfit line to shift it down
    points = [float(processedmeans[i][0]) for i in range(len(processedmeans))]
    thresholdedpoints = [points[i] for i in range(len(points))
        if (i < LOW_CUTOFF or i > len(points) - HIGH_CUTOFF)]
    avg = np.average(np.poly1d(polyfilter)(thresholdedpoints))
    # print(np.poly1d(polyfilter))
    # print(avg)

    f, axarr = plt.subplots(2, sharex=True)
    axarr[1].plot(*zip(*processed), 'b',
                    *zip(*processedmeans), 'r.')#,
                    # points, np.poly1d(polyfilter)(points) - avg, 'g--')

    axarr[0].set_title("Temperature vs. Frequency Across Measured Spectra (Unfiltered)")
    axarr[1].set_title("Temperature vs. Frequency Across Measured Spectra (Filtered)")
    axarr[1].set_xlabel("Frequency (MHz)")
    axarr[0].set_ylabel("Temperature (K)")
    axarr[1].set_ylabel("Temperature (K)")

    axarr[0].plot(*zip(*threshold(unfiltered)),
                    *zip(*unfiltered), 'r.',
                    points, np.poly1d(polyfilter)(points), 'g--')

    plt.tight_layout()
    plt.show()

if __name__=="__main__":
    main(sys.argv[1:])
