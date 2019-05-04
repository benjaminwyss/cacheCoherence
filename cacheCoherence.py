class CacheRecord:
    """
    The CacheRecord class is utilized to store information from each processor's trace file. It serves as a data structure to make the implementation of this project simpler
    """
    def __init__(self, cycle, processor, isWrite, address):
        """
        Constructor for the CacheRecord class
        @param cycle is the clock cycle that the cache record took place in
        @param processor is the processor number that the cache record belongs to
        @param isWrite is True if the processor wrote to memory and False if the processor read from memory
        @param address is the memory address that the processor accessed
        @post Constructs a CacheRecord object by setting member variables equal to the corresponding parameters, and then calculates the offset, index, and tag that correspond to the cache record's memory address
        """
        self.cycle = cycle
        self.processor = processor
        self.isWrite = isWrite
        self.address = address
        # 32 byte cache line = 2^5. This corresponds to 5 bits of offset.
        self.offset = int(address[27:32], 2)
        # Number of lines = 16KB cache / 32B cache line = 2^9. This corresponds to 9 bits of index
        self.index = int(address[18:27], 2)
        # 32 bit address - 5 bit offset - 9 bit index = 18 bits of tag
        self.tag = int(address[0:18], 2)

    def __str__(self):
        """
        Overloaded string operator
        @return this helper method simply returns the cacheRecord object as a string, which is used to print individual cacheRecords to aid with testing
        """
        return "[{}, {}, {}, {}, {}, {}, {}]".format(self.cycle, self.processor, ("Write" if self.isWrite else "Read"), self.address, self.offset, self.index, self.tag)

    def __lt__(self, other):
        """
        Overloaded less than (<) operator
        @param other is another CacheRecord object
        @return this helper method returns True if the first CacheRecord happened before the other CacheRecord chronologically. This can be used to sort the CacheRecords in chronological order
        """
        if (self.cycle < other.cycle):
            return True
        elif (self.cycle > other.cycle):
            return False
        else:
            return (self.processor < other.processor)

class CacheLine:
    """
    The CacheLine class is utilized to store information about the tags and MOESI states that are stored for each processor's cache lines. It serves as a data structure to make the implementation of this project simpler
    """
    def __init__(self):
        """
        Constructor for the CacheLine class
        @post Constructs a CacheLine object with each processor beginning in the 'I' state and each tag starting out as 'None' 
        """
        self.tags = [None] * 4
        self.processorStates = ['I'] * 4

    def __str__(self):
        """
        Overloaded string operator
        @return This helper method simply returns the CacheLine object as a string that can be printed, which is utilized to aid manual testing
        """
        return "[{}, {}]".format(self.tags, self.processorStates)

class ProcessorStats:
    """
    The ProcessorStats class is used to store information that needs to be printed at the end of the cache coherence simulations. It acts as a data structure that helps to organize information about each processor's cache transfers, invalidations, and dirty write backs
    """
    def __init__(self):
        """
        Constructor for the ProcessorStats class
        @post Constructs a ProcessorStats object with each stat that is tracked initialized to 0. The cacheCoherence class can then update these values as needed throughout runtime
        """
        self.cacheTransfers = [0, 0, 0, 0]
        self.invalidationFromM = 0
        self.invalidationFromO = 0
        self.invalidationFromE = 0
        self.invalidationFromS = 0
        self.invalidationFromI = 0
        self.dirtyWriteBacks = 0

class CacheCoherence:
    """
    The CacheCoherence class is in charge of simulating cache coherency from processor trace files by using all of the data structure classes that were implemented above.
    """
    def __init__(self):
        """
        Constructor for the CacheCoherence class
        @post Constructs a CacheCoherence object by initializing an empty cacheRecords array, a cacheLine array that stores newly constructed CacheLines, and an array of ProcessorStats for each processor
        """
        self.cacheRecords = []
        # Since index is 9 bits, there are 2^9, or 512 cache lines
        self.cacheLines = [CacheLine() for i in range(0, 512)]
        # Keep track of stats for each processor
        self.processorStatTracker = [ProcessorStats() for i in range(0, 4)]

    def simulateCacheRecords(self):
        """
        simulateCacheRecords
        @pre readCacheRecordsFromFiles has been executed
        @post simulates each cacheRecord in the cacheRecords array by first checking for and handling conflict misses, then updating the cacheRecord's corresponding cache line's tag and state. The appropriate bus signal methods are called as needed. Lastly, once all of the cacheRecords have been simulated, this method loops through all cacheLines and writes back all remaining dirty lines.
        """
        for cacheRecord in self.cacheRecords:
            cacheLine = self.cacheLines[cacheRecord.index]
            state = cacheLine.processorStates[cacheRecord.processor]

            #Handle Conflict Misses
            if (cacheLine.tags[cacheRecord.processor] != None and cacheLine.tags[cacheRecord.processor] != cacheRecord.tag):
                if cacheLine.processorStates[cacheRecord.processor] == 'M' or cacheLine.processorStates[cacheRecord.processor] == 'O':
                    self.processorStatTracker[cacheRecord.processor].dirtyWriteBacks += 1
                cacheLine.processorStates[cacheRecord.processor] = 'I'

            #Update Tag Array
            cacheLine.tags[cacheRecord.processor] = cacheRecord.tag

            #prWr
            if (cacheRecord.isWrite):
                if state == 'M':
                    # Remain in M state, no bus signal
                    pass
                elif state == 'O':
                    cacheLine.processorStates[cacheRecord.processor] = 'M'
                    self.busUpgr(cacheRecord.processor, cacheLine, cacheRecord.tag)
                elif state == 'E':
                    cacheLine.processorStates[cacheRecord.processor] = 'M'
                elif state == 'S':
                    cacheLine.processorStates[cacheRecord.processor] = 'M'
                    self.busUpgr(cacheRecord.processor, cacheLine, cacheRecord.tag)
                elif state == 'I':
                    cacheLine.processorStates[cacheRecord.processor] = 'M'
                    self.busRdX(cacheRecord.processor, cacheLine, cacheRecord.tag)
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
                    if 'M' in cacheLine.processorStates or 'O' in cacheLine.processorStates or 'E' in cacheLine.processorStates or 'S' in cacheLine.processorStates:
                        self.busRd(cacheRecord.processor, cacheLine, cacheRecord.tag)
                        cacheLine.processorStates[cacheRecord.processor] = 'S'
                    else:
                        cacheLine.processorStates[cacheRecord.processor] = 'E'
                        #In a real processor, this would cause a BusRd signal, but since the data is fetched from memory nothing needs to be simulated here.

        #Write back all dirty lines at end of simulation
        for cacheLine in self.cacheLines:
            for processor in range(0, 4):
                if (cacheLine.processorStates[processor] == 'M' or cacheLine.processorStates[processor] == 'O'):
                    self.processorStatTracker[processor].dirtyWriteBacks += 1
        


    def busRd(self, originator, cacheLine, tag):
        """
        busRd
        @pre a processor in the 'I' state initiates a prRd instruction
        @param originator is the processor that initiated the prRd
        @param cacheLine is the cache line that the prRd occured on
        @param tag is the tag which the prRd read into the cache
        @post Simulates a busRd signal by searching for a processor to receive a data transfer from. This method first searches for a processor in the 'M' state with a matching tag, then a processor in the 'O' state with a matching tag, next a processor in the 'E' state with a matching tag, and lastly a processor in the 'S' state with a matching tag
        """
        for processor in range(0, 4):
            if cacheLine.processorStates[processor] == 'M' and cacheLine.tags[processor] == tag:
                self.processorStatTracker[processor].cacheTransfers[originator] += 1
                cacheLine.processorStates[processor] = 'O'
                return
        for processor in range(0, 4):
            if cacheLine.processorStates[processor] == 'O' and cacheLine.tags[processor] == tag:
                self.processorStatTracker[processor].cacheTransfers[originator] += 1
                return
        for processor in range(0, 4):
            if cacheLine.processorStates[processor] == 'E' and cacheLine.tags[processor] == tag:
                self.processorStatTracker[processor].cacheTransfers[originator] += 1
                cacheLine.processorStates[processor] = 'S'
                return
        for processor in range(0, 4):
            if cacheLine.processorStates[processor] == 'S' and cacheLine.tags[processor] == tag:
                self.processorStatTracker[processor].cacheTransfers[originator] += 1
                return

    def busRdX(self, originator, cacheLine, tag):
        """
        busRdX
        @pre a processor in the 'I' state initiates a prWr instruction
        @param originator is the processor that initiated the prWr
        @param cacheLine is the cache line that the prWr occured on
        @param tag is the tag which the prWr wrote to the cache
        @post Simulates a busRdX signal by looping through each other processor, invalidating cache lines that share the parameterized tag, and handling dirty writebacks from invalidated processors that were in the 'M' or 'O' state. This is accomplished by setting invalidated processors' tags to 'None' and states to 'I'
        """
        for processor in range(0, 4):
            if processor != originator and cacheLine.tags[processor] == tag:
                if cacheLine.processorStates[processor] == 'M':
                    cacheLine.processorStates[processor] = 'I'
                    cacheLine.tags[processor] = None
                    self.processorStatTracker[processor].invalidationFromM += 1
                    self.processorStatTracker[processor].dirtyWriteBacks += 1
                    self.processorStatTracker[processor].cacheTransfers[originator] += 1
                elif cacheLine.processorStates[processor] == 'O':
                    cacheLine.processorStates[processor] = 'I'
                    cacheLine.tags[processor] = None
                    self.processorStatTracker[processor].invalidationFromO += 1
                    self.processorStatTracker[processor].dirtyWriteBacks += 1
                    self.processorStatTracker[processor].cacheTransfers[originator] += 1
                elif cacheLine.processorStates[processor] == 'E':
                    cacheLine.processorStates[processor] = 'I'
                    cacheLine.tags[processor] = None
                    self.processorStatTracker[processor].invalidationFromE += 1
                    self.processorStatTracker[processor].cacheTransfers[originator] += 1
                elif cacheLine.processorStates[processor] == 'S':
                    cacheLine.processorStates[processor] = 'I'
                    cacheLine.tags[processor] = None
                    self.processorStatTracker[processor].invalidationFromS += 1
                elif cacheLine.processorStates[processor] == 'I':
                    #Stay in state I
                    pass

    def busUpgr(self, originator, cacheLine, tag):
        """
        busUpgr
        @pre a processor in the 'O' or 'S' state initiates a prWr instruction
        @param originator is the processor that initiated the prWr
        @param cacheLine is the cache line that the prWr occured on
        @param tag is the tag which the prWr wrote to the cache
        @post Simulates a busUpgr signal by looping through each other processor and invalidating cache lines that share the paramterized tag. This is accomplished by setting the processor's tag to 'None' and its state to 'I'
        """
        for processor in range(0, 4):
            if processor != originator and cacheLine.tags[processor] == tag:
                if cacheLine.processorStates[processor] == 'M':
                    print("This case shouldn't happen")
                elif cacheLine.processorStates[processor] == 'O':
                    cacheLine.processorStates[processor] = 'I'
                    cacheLine.tags[processor] = None
                    self.processorStatTracker[processor].invalidationFromO += 1
                elif cacheLine.processorStates[processor] == 'E':
                    print("This also shouldn't happen")
                elif cacheLine.processorStates[processor] == 'S':
                    cacheLine.processorStates[processor] = 'I'
                    cacheLine.tags[processor] = None
                    self.processorStatTracker[processor].invalidationFromS += 1
                elif cacheLine.processorStates[processor] == 'I':
                    #Stay in state I
                    pass

    def readCacheRecordsFromFiles(self):
        """
        readCacheRecordsFromFiles
        @pre CacheCoherence object has been constructed
        @post Reads in all 4 trace files and adds each row as an entry in the cacheRecord array. Once all cacheRecords have been read in, the cacheRecords array is sorted so that the cacheRecords can later be traced in chronological order
        """
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
        """
        testPrints
        @pre readCacheRecordsFromFiles has been executed
        @post this helper method prints every cacheRecord and every cacheLine in their corresponding array, so that they can be manually observed for accuracy
        """
        for record in self.cacheRecords:
            print(record)
        for cacheLine in self.cacheLines:
            print(cacheLine)

    def printStats(self):
        """
        printStats
        @pre simulateCacheRecords has been executed
        @post Prints all statistics stored in each ProcessorStats object of the processorStatTracker array, as well as the number final states of each processor's cache lines These prints are formatted to look the same as project specification's output
        """
        print("P0 cache transfers: <p0-p1> = {}, <p0-p2> = {}, <p0-p3> = {}".format(self.processorStatTracker[0].cacheTransfers[1], self.processorStatTracker[0].cacheTransfers[2], self.processorStatTracker[0].cacheTransfers[3]))
        print("P1 cache transfers: <p1-p0> = {}, <p1-p2> = {}, <p1-p3> = {}".format(self.processorStatTracker[1].cacheTransfers[0], self.processorStatTracker[1].cacheTransfers[2], self.processorStatTracker[1].cacheTransfers[3]))
        print("P2 cache transfers: <p2-p0> = {}, <p2-p1> = {}, <p2-p3> = {}".format(self.processorStatTracker[2].cacheTransfers[0], self.processorStatTracker[2].cacheTransfers[1], self.processorStatTracker[2].cacheTransfers[3]))
        print("P3 cache transfers: <p3-p0> = {}, <p3-p1> = {}, <p3-p2> = {}".format(self.processorStatTracker[3].cacheTransfers[0], self.processorStatTracker[3].cacheTransfers[1], self.processorStatTracker[3].cacheTransfers[2]))
        print()

        for processor in range(0, 4):
            print("P{} Invalidation from: m = {}, o = {}, e = {}, s = {}, i = {}".format(processor, self.processorStatTracker[processor].invalidationFromM, self.processorStatTracker[processor].invalidationFromO, self.processorStatTracker[processor].invalidationFromE, self.processorStatTracker[processor].invalidationFromS, self.processorStatTracker[processor].invalidationFromI))
        print()

        print("Dirty Writebacks: P0 = {}, P1 = {}, P2 = {}, P3 = {}".format(self.processorStatTracker[0].dirtyWriteBacks, self.processorStatTracker[1].dirtyWriteBacks, self.processorStatTracker[2].dirtyWriteBacks, self.processorStatTracker[3].dirtyWriteBacks))

        print()

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
    """
    main
    @post Creates a CacheCoherence object, then calls readCacheRecordsFromFiles, simulateCacheRecords, and then printStats, so that the simulated records' output is printed to the console.
    """
    myCacheCoherence = CacheCoherence()
    myCacheCoherence.readCacheRecordsFromFiles()
    myCacheCoherence.simulateCacheRecords()
    myCacheCoherence.printStats()
