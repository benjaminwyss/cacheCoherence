class CacheRecord:
    def __init__(self, cycle, processor, isWrite, address):
        self.cycle = cycle
        self.processor = processor
        self.isWrite = isWrite
        self.address = address
    
    def __str__(self):
        return "[{}, {}, {}, {}]".format(self.cycle, self.processor, ("Write" if self.isWrite else "Read"), self.address)

    def __lt__(self, other):
        if (self.cycle < other.cycle):
            return True
        elif (self.cycle > other.cycle):
            return False
        else:
            return (self.processor < other.processor)

class CacheCoherence:
    def __init__(self):
        self.cacheRecords = []

    def readCacheRecordsFromFiles(self):
        for i in range(0, 4):
            file = open(("p{}.tr".format(i)), "r")
            for line in file:
                line = line.split()
                cacheRecord = CacheRecord(int(line[0]), i, bool(int((line[1]))), line[2])
                self.cacheRecords.append(cacheRecord)
        
        self.cacheRecords.sort()
        for record in self.cacheRecords:
            print(record)



if __name__ == "__main__":
    myCacheCoherence = CacheCoherence()
    myCacheCoherence.readCacheRecordsFromFiles()