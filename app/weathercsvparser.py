import csv

def get_data(filedata):
    with open (filedata, newline='') as csvfile:
        spamreader = csv.reader(csvfile, dialect='unix', delimiter=';', quotechar="|")
        j = []
        for row in spamreader:
#            print(row)
            k = []
            i = 0
            for num in row:
                k.append(float(num))
                i += 1
            j = j + [k]
    return j

def print_tab(data):
    for s in data:
        print(s)
