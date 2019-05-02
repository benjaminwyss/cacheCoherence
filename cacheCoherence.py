class CacheRecord:
    def __init__(self, cycle, processor, isWrite, address):
        self.cycle = cycle
        self.processor = processor
        self.isWrite = isWrite
        self.address = address
        # 32 byte cache line = 2^5. This corresponds to 5 bits of offset. This offset is divided by 4 since the processor loads/stores words instead of bytes
        self.offset = int(int(address[27:32], 2) / 4)
        # Number of lines = 16KB cache / 32B cache line = 2^9. This corresponds to 9 bits of index
        self.index = int(address[18:27], 2)
        # 32 bit address - 5 bit offset - 9 bit index = 18 bits of tag
        self.tag = int(address[0:18], 2)

    def __str__(self):
        return "[{}, {}, {}, {}, {}, {}, {}]".format(self.cycle, self.processor, ("Write" if self.isWrite else "Read"), self.address, self.offset, self.index, self.tag)

    def __lt__(self, other):
        if (self.cycle < other.cycle):
            return True
        elif (self.cycle > other.cycle):
            return False
        else:
            return (self.processor < other.processor)

class CacheLine:
    def __init__(self):
        self.tags = [None] * 8
        self.processorStates = ['I'] * 4

    def __str__(self):
        return "[{}, {}]".format(self.tags, self.processorStates)

class processorStats:
    def __init__(self):
        self.cacheTransfers = [0, 0, 0, 0]
        self.invalidationFromM = 0
        self.invalidationFromO = 0
        self.invalidationFromE = 0
        self.invalidationFromS = 0
        self.invalidationFromI = 0
        self.dirtyWriteBacks = 0

class CacheCoherence:
    def __init__(self):
        self.cacheRecords = []
        # Since index is 9 bits, there are 2^9, or 512 cache lines
        self.cacheLines = [CacheLine() for i in range(0, 512)]
        # Keep track of stats for each processor
        self.processorStatTracker = [processorStats() for i in range(0, 4)]

    def simulateCacheRecords(self):
        for cacheRecord in self.cacheRecords:
            cacheLine = self.cacheLines[cacheRecord.index]
            state = cacheLine.processorStates[cacheRecord.processor]

            #prWr
            if (cacheRecord.isWrite):
                if state == 'M':
                    # Remain in M state, no bus signal
                    pass
                elif state == 'O':
                    cacheLine.processorStates[cacheRecord.processor] = 'M'
                    self.busUpgr(cacheRecord.processor)
                elif state == 'E':
                    cacheLine.processorStates[cacheRecord.processor] = 'M'
                elif state == 'S':
                    cacheLine.processorStates[cacheRecord.processor] = 'M'
                    self.busUpgr(cacheRecord.processor)
                elif state == 'I':
                    cacheLine.processorStates[cacheRecord.processor] = 'M'
                    self.busRdX(cacheRecord.processor)
            #prRd
            else:
                if state == 'M':
                    # Remain in M state, no bus signal
                    pass
                elif state == 'O':
                    # Remain in O state, no bus signal
                    pass
                elif state == 'E':
                    # Remain in E state, no bus signal
                    pass
                elif state == 'S':
                    # remain in S state, no bus signal
                    pass
                elif state == 'I':
                    if 'M' in cacheLine.processorStates or 'O' in cacheLine.processorStates or 'E' in cacheLine.processorStates:
                        cacheLine.processorStates[cacheRecord.processor] = 'S'
                        self.busRd(cacheRecord.processor)
                    else:
                        cacheLine.processorStates[cacheRecord.processor] = 'E'
                        self.busRd(cacheRecord.processor)


    def busRd(self, originator):
        pass

    def busRdX(self, originator):
        pass

    def busUpgr(self, originator):
        pass

    def readCacheRecordsFromFiles(self):
        for i in range(0, 4):
            file = open(("p{}.tr".format(i)), "r")
            for line in file:
                line = line.split()
                #line[0] is the clock cycle, i is the processor number, line[1] is a write/read flag, and line[2] is the memory adress, which is converted to binary and filled to 32 bits
                cacheRecord = CacheRecord(int(line[0]), i, bool(int((line[1]))), bin(int(line[2], 0))[2:].zfill(32))
                self.cacheRecords.append(cacheRecord)

            # Based on the definition for sorting CacheRecords, this arranges the records in chronological order
            self.cacheRecords.sort()

    def testPrints(self):
        for record in self.cacheRecords:
            print(record)
        for cacheLine in self.cacheLines:
            print(cacheLine)

    def printStats(self):
        print("P0 cache transfers: <p0-p1> = {}, <p0-p2> = {}, <p0-p3> = {}".format(self.processorStatTracker[0].cacheTransfers[1], self.processorStatTracker[0].cacheTransfers[2], self.processorStatTracker[0].cacheTransfers[3]))
        print("P1 cache transfers: <p1-p0> = {}, <p1-p2> = {}, <p1-p3> = {}".format(self.processorStatTracker[1].cacheTransfers[0], self.processorStatTracker[1].cacheTransfers[2], self.processorStatTracker[1].cacheTransfers[3]))
        print("P2 cache transfers: <p2-p0> = {}, <p2-p1> = {}, <p2-p3> = {}".format(self.processorStatTracker[2].cacheTransfers[0], self.processorStatTracker[2].cacheTransfers[1], self.processorStatTracker[2].cacheTransfers[3]))
        print("P3 cache transfers: <p3-p0> = {}, <p3-p1> = {}, <p3-p2> = {}".format(self.processorStatTracker[3].cacheTransfers[0], self.processorStatTracker[3].cacheTransfers[1], self.processorStatTracker[3].cacheTransfers[2]))
        print()

        for processor in range(0, 4):
            print("P{} Invalidation from: m = {}, o = {}, e = {}, s = {}, i = {}".format(processor, self.processorStatTracker[processor].invalidationFromM, self.processorStatTracker[processor].invalidationFromO, self.processorStatTracker[processor].invalidationFromE, self.processorStatTracker[processor].invalidationFromS, self.processorStatTracker[processor].invalidationFromI))
        print()

        print("Dirty Writebacks: P0 = {}, P1 = {}, P2 = {}, P3 = {}".format(self.processorStatTracker[0].dirtyWriteBacks, self.processorStatTracker[1].dirtyWriteBacks, self.processorStatTracker[2].dirtyWriteBacks, self.processorStatTracker[3].dirtyWriteBacks))
        print("Currently dirty cache lines at indexes: ", end='')
        for i in range(0, 512):
            if 'M' in self.cacheLines[i].processorStates or 'O' in self.cacheLines[i].processorStates:
                print("{}, ".format(i), end='')

        print('\n')

        for processor in range(0, 4):
            m = 0
            o = 0
            e = 0
            s = 0
            i = 0
            for cacheLine in self.cacheLines:
                if cacheLine.processorStates[processor] == 'M':
                    m += 1
                elif cacheLine.processorStates[processor] == 'O':
                    o += 1
                elif cacheLine.processorStates[processor] == 'E':
                    e += 1
                elif cacheLine.processorStates[processor] == 'S':
                    s += 1
                elif cacheLine.processorStates[processor] == 'I':
                    i += 1
            print("Final States for P{}: m = {}, o = {}, e = {}, s = {}, i = {}".format(processor, m, o, e, s, i))



if __name__ == "__main__":
    myCacheCoherence = CacheCoherence()
    myCacheCoherence.readCacheRecordsFromFiles()
    myCacheCoherence.simulateCacheRecords()
    myCacheCoherence.printStats()
