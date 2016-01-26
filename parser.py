import sys, getopt
from collections import OrderedDict
import matplotlib.pyplot as plt

#Index of first temperature value
TEMP_OFFSET = 20

NUM_CHANNELS = 135

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

    plot = plt.plot(list(means.keys()), list(means.values()))
    plt.title("Temperature vs. Frequency Across Measured Spectra")
    plt.xlabel("Frequency (MHz)")
    plt.ylabel("Temperature (K)")
    plt.tight_layout()
    plt.show()

def main(argv):

    filename = ""

    try:
        opts, args = getopt.getopt(argv,"hi:",["input="])
    except getopt.GetoptError:
        print("parser.py -i <input file>")
        sys.exit(2)

    for opt, arg in opts:
        if opt == '-h':
            print("parser.py -i <input file>")
            sys.exit(0)
        elif opt in ("-i", "--input"):
            print("opt")
            filename = arg

    print("Parsing file %s\n" % filename)

    parse(filename)

if __name__=="__main__":
    main(sys.argv[1:])
