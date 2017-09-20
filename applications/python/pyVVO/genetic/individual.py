"""
required packages: pyodbc

Created on Aug 9, 2017

@author: thay838
"""
import random
from powerflow import writeCommands
import util.gld
import util.helper
import math

# Define cap status, to be accessed by binary indices.
CAPSTATUS = ['OPEN', 'CLOSED']
REGPEG = ['max', 'min']
# Define the percentage of the tap range which sigma should be for drawing
# tap settings. Recall the 68-95-99.7 rule for normal distributions -
# 1 std dev, 2 std dev, 3 std dev probabilities
TAPSIGMAPCT = 0.1
 
class individual:
    
    def __init__(self, uid, starttime, stoptime, reg=None, regBias=False,
                 peg=None, cap=None, capFlag=2, regChrom=None, capChrom=None,
                 parents=None):
        """An individual contains information about Volt/VAR control devices
        
        Individuals can be initialized in two ways: 
        1) From scratch: Provide self, uid, reg, and cap inputs. Positions
            will be randomly generated
            
        2) From a chromosome: Provide self, reg, cap, uid, regChrom, and 
            capChrom. After crossing two individuals, a new chromosome will
            result. Use this chromosome to update reg and cap
        
        INPUTS:
            reg: Dictionary as described in the docstring for the gld module.
            
                Note possible tap positions be in interval [-(lower_taps - 1),
                raise_taps]. 
                    
            cap: Dictionary describing capacitors as described in the docstring
                for the gld module.
                
            capFlag: Flag for special handling of capacitors.
                0: All capacitors set to CAPSTATUS[0] (OPEN)
                1: All capacitors set to CAPSTATUS[1] (CLOSED)
                2: Capacitor state randomly determined
                3: Capacitor state unchanged - simply reflects what's in the
                    'cap' input.
                
            uid: Unique ID of individual. Should be an int.
            
            regChrom: Regulator chromosome resulting from crossing two
                individuals. List of ones and zeros representing tap positions. 
                
            capChrom: Capacitor chromosome resulting from crossing two
                individuals. List of ones and zeros representing switch status.
                
            parents: Tuple of UIDs of parents that created this individual.
                None if individual was randomly created at population init.
            
        TODO: add controllable DERs
                
        """
        # Assign reg and cap dicts
        self.reg = reg
        self.cap = cap
        
        # Assign the unique identifier.
        self.uid = uid
        # Assing times.
        self.starttime = starttime
        self.stoptime = stoptime
        # Full path to output model.
        self.model = None
        # Table information
        self.swingTable = None
        self.swingColumns = None
        self.swingInterval = None
        self.triplexTable = None
        self.triplexColumns = None
        self.triplexInterval = None
        
        # Track tap changes and capacitor switching
        self.tapChangeCount = 0
        self.capSwitchCount = 0
        
        # When the model is run, output will be saved.
        self.modelOutput = None

        # The evalFitness method assigns to fitness and costs
        self.fitness = None
        self.costs = None
        # Parent tracking is useful to see how well the GA is working
        self.parents = parents
        
        # When writing model, names of voltdump files will be saved
        self.voltdumpFiles = None
        
        # When writing model, output directory will be saved.
        self.outDir = None
        
        # If not given a regChrom or capChrom, generate them.
        if (regChrom is None) and (capChrom is None):
            # Generate regulator chromosome:
            self.genRegChrom(regBias=regBias, peg=peg)
            # Generate capacitor chromosome:
            self.genCapChrom(flag=capFlag)
            # TODO: DERs
        else:
            # Use the given chromosomes to update the dictionaries.
            self.regChrom = regChrom
            self.modifyRegGivenChrom()
            self.capChrom = capChrom
            self.modifyCapGivenChrom()
            
    def __str__(self):
        """Individual's string should include fitness and reg/cap info.
        
        This is a simple wrapper to call helper.getSummaryStr since the
        benchmark system should be displayed in the same way.
        """
        s = util.helper.getSummaryStr(costs=self.costs, reg=self.reg,
                                      cap=self.cap, regChrom=self.regChrom,
                                      capChrom=self.capChrom,
                                      parents=self.parents)
        
        return s
        
    def genRegChrom(self, regBias, peg):
        """Method to randomly generate an individual's regulator chromosome
        
        INPUTS:
            regBias: Flag, True or False. True indicates that tap positions
                for this individual will be biased (via a Gaussian 
                distribution and the TAPSIGMAPCT constant) toward the previous
                tap positions, while False indicates taps will be chosen purely
                randomly.
            peg: None, 'max', or 'min.' If 'None' is provided, input has no 
                affect. 'max' will put all regulator taps at maximum position,
                and 'min' will put all regulator taps at minimum position.
                
        OUTPUTS:
            sets self.regChrom and modifies self.reg
            
        NOTES:
            If the peg input is not None, regBias must be False.
            
        TODO: track tap changes. 
        """
        # Make sure inputs aren't incompatible.
        if peg:
            assert (not regBias), ("If 'peg' is not None, "
                                    "'regBias' must be False.")
            assert peg in REGPEG
        
        # Initialize chromosome for regulator and dict to store list indices.
        self.regChrom = ()
         
        # Intialize index counters.
        s = 0;
        e = 0;
        
        # Loop through the regs and create binary representation of taps.
        for r, v in self.reg.items():
            
            # Define the upper tap bound (tb).
            tb = v['raise_taps'] + v['lower_taps'] - 1
            
            # Compute the needed field width to represent the upper tap bound
            width = math.ceil(math.log(tb, 2))
            
            # If we're pegging, set the position high or low.
            if peg:
                if peg == 'max':
                    newState = tb
                elif peg == 'min':
                    newState = 0
            elif regBias:
                # If we're biasing from the previous position, get a sigma for
                # the Gaussian distribution.
                tapSigma = round(TAPSIGMAPCT * (tb + 1))
            
            # Loop through the phases
            for phase, phaseData in v['phases'].items():
                
                # If we're biasing new positions based on previous positions:
                if regBias:
                    # Randomly draw tap position from gaussian distribution.
                    
                    # Translate previous position to integer on interval [0,tb]
                    prevState = \
                        util.gld.inverseTranslateTaps(lowerTaps=v['lower_taps'],
                                                 pos=phaseData['prevState'])
                        
                    # Initialize the newState for while loop.
                    newState = -1
                    
                    # The standard distribution runs from (-inf, +inf) - draw 
                    # until position is valid. Recall valid positions are
                    # [0, tb]
                    while (newState < 0) or (newState > tb):
                        # Draw the tap position from the normal distribution.
                        # Here oure 'mu' is the previous value
                        newState = round(random.gauss(prevState, tapSigma))
                        
                elif not peg:
                    # If we made it here, we aren't implementing a previous 
                    # bias or 'pegging' the taps. Randomly draw.
                    newState = random.randint(0, tb)
                
                # Express tap setting as binary list with consistent width.
                binTuple = tuple([int(x) for x in "{0:0{width}b}".format(newState,
                                                                  width=width)])
                
                # Extend the regulator chromosome.
                self.regChrom += binTuple
                
                # Increment end index.
                e += len(binTuple)
                
                # Translate newState for GridLAB-D.
                self.reg[r]['phases'][phase]['newState'] = \
                    util.gld.translateTaps(lowerTaps=v['lower_taps'], pos=newState)
                    
                # Increment the tap change counter (previous pos - this pos)
                self.tapChangeCount += \
                    abs(self.reg[r]['phases'][phase]['prevState']
                        - self.reg[r]['phases'][phase]['newState'])
                
                # Assign indices for this phase
                self.reg[r]['phases'][phase]['chromInd'] = (s, e)
                
                # Increment start index.
                s += len(binTuple)
                
    def genCapChrom(self, flag):
        """Method to generate an individual's capacitor chromosome.
        
        INPUTS:
            flag:
                0: All capacitors set to CAPSTATUS[0] (OPEN)
                1: All capacitors set to CAPSTATUS[1] (CLOSED)
                2: Capacitor state randomly determined
                3: Capacitor state unchanged - simply reflects what's in the
                    'cap' input.
                
        OUTPUTS:
            modifies self.cap, sets self.capChrom
        """
        # If we're forcing all caps to the same status, determine the binary
        # representation. TODO: add input checking.
        if flag < 2:
            capBinary = flag
            capStatus = CAPSTATUS[flag]
        
        # Initialize chromosome for capacitors and dict to store list indices.
        self.capChrom = ()

        # Keep track of chromosome index
        ind = 0
        
        # Loop through the capacitors, randomly assign state for each phase
        for c, capData in self.cap.items():
            
            # Loop through the phases and randomly decide state
            for phase in capData['phases']:
                
                # Randomly determine capacitor status if flag is 2
                if flag == 2:
                    capBinary = round(random.random())
                    capStatus = CAPSTATUS[capBinary]
                elif flag == 3:
                    capStatus = self.cap[c]['phases'][phase]['prevState']
                    capBinary = CAPSTATUS.index(capStatus)
                
                # Assign to the capacitor
                self.capChrom += (capBinary,)
                self.cap[c]['phases'][phase]['newState'] = capStatus
                self.cap[c]['phases'][phase]['chromInd'] = ind
                
                # Increment the switch counter if applicable
                if (self.cap[c]['phases'][phase]['newState'] !=
                        self.cap[c]['phases'][phase]['prevState']):
                    
                    self.capSwitchCount += 1
                
                # Increment the chromosome counter
                ind += 1
                
    def modifyRegGivenChrom(self):
        """Modifiy self.reg based on self.regChrom
        """
        # Loop through self.reg and update 'newState'
        for r, regData in self.reg.items():
            for phase, phaseData in regData['phases'].items():
                
                # Extract the binary representation of tap position.
                tapBin = \
                    self.regChrom[phaseData['chromInd'][0]:\
                                  phaseData['chromInd'][1]]
                    
                # Convert the binary to an integer
                posInt = util.helper.bin2int(tapBin)
                
                # Convert integer to tap position and assign to new position
                self.reg[r]['phases'][phase]['newState'] = \
                    util.gld.translateTaps(lowerTaps=self.reg[r]['lower_taps'],
                                      pos=posInt)
                    
                # Increment the tap change counter (previous pos - this pos)
                self.tapChangeCount += \
                    abs(self.reg[r]['phases'][phase]['prevState']
                        - self.reg[r]['phases'][phase]['newState'])
    
    def modifyCapGivenChrom(self):
        """Modify self.cap based on self.capChrom
        """
        # Loop through the capDict and assign 'newState'
        for c, capData in self.cap.items():
            for phase in capData['phases']:
                # Read chromosome and assign newState
                self.cap[c]['phases'][phase]['newState'] = \
                    CAPSTATUS[self.capChrom[self.cap[c]['phases'][phase]\
                                            ['chromInd']]]
                
                # Bump the capacitor switch count if applicable
                if self.cap[c]['phases'][phase]['newState'] != \
                        self.cap[c]['phases'][phase]['prevState']:
                    
                    self.capSwitchCount += 1
                
    def writeModel(self, strModel, inPath, outDir, dumpGroup='tLoad'):
        """Create a GridLAB-D .glm file for the given individual by modifying
        setpoints for controllable devices (capacitors, regulators, eventually
        DERs)
        
        INPUTS:
            self: constructed individual
            strModel: string of .glm file found at inPath
            inPath: path to model to modify volt control settings
            outDir: directory to write new model to. Filename will be inferred
                from the inPath, and the individuals uid preceded by an
                underscore will be added
            dumpGroup: Name of group used for triplex_loads.
                
        OUTPUTS:
            Path to new model after it's created
        """
        # Assign output directory.
        self.outDir = outDir
        
        # Get the filename of the original model and create output path
        outPath = \
            writeCommands.writeCommands.addFileSuffix(inPath=inPath,
                                                      suffix=str(self.uid),
                                                      outDir = outDir)
        
        # Track the output path for running the model later.
        self.model = outPath
        
        # Instantiate a writeCommands object.
        writeObj = writeCommands.writeCommands(strModel=strModel,
                                               pathModelIn=inPath,
                                               pathModelOut=outPath)
        
        # Update the swing node to a meter and get it writing power to a table
        # TODO: swing table won't be the only table.
        o = writeObj.recordSwing(suffix=self.uid)
        self.swingTable = o['table']
        self.swingColumns = o['columns']
        self.swingInterval = o['interval']
        
        # Add voltdumps for each triplex load. Start by adding groups.
        writeObj.addGroupToObjects(objectRegex=writeCommands.TRIPLEX_LOAD_REGEX,
                                   groupName=dumpGroup)
        
        self.voltdumpFiles = writeObj.addVoltDumps(starttime=self.starttime,
                                                   stoptime=self.stoptime,
                                                   group=dumpGroup, 
                                                   fileDir=self.outDir,
                                                   baseFile='vDump.csv',
                                                   suffix=self.uid,
                                                   interval=60)
        
        
        # TODO: Uncomment when ready
        '''
        # Record triplex nodes
        o = writeObj.recordTriplex(suffix=self.uid)
        self.triplexTable = o['table']
        self.triplexColumns = o['columns']
        self.triplexInterval = o['interval']
        ''' 
        # Set regulator and capacitor control schemes to manual.
        for r in self.reg:
            self.reg[r]['Control'] = 'MANUAL'
            
        for c in self.cap:
            self.cap[c]['control'] = 'MANUAL'
        
        # Change capacitor and regulator statuses/positions.
        writeObj.commandRegulators(reg=self.reg)
        writeObj.commandCapacitors(cap=self.cap)
        
        # Write the modified model to file.
        writeObj.writeModel()
        
        # Return the path to the new file.
        return outPath
    
    def runModel(self):
        """Function to run GridLAB-D model.
        """
        self.modelOutput = util.gld.runModel(self.model)
                            
    def evalFitness(self, cursor, energyPrice, tapChangeCost, capSwitchCost,
                    voltCost, tCol='t'):
        """Function to evaluate fitness of individual. This is essentially a
            wrapper to call util.gld.computeCosts
        
        TODO: Add more evaluators of fitness like voltage violations, etc.
        
        INPUTS:
            cursor: pyodbc cursor from pyodbc connection 
            energyPrice: price of energy
            tapChangeCost: cost changing regulator taps
            capSwitchCost: cost of switching a capacitor
            tCol: name of time column(s)
            starttime: starting time to evaluate
            stoptime: ending time to evaluate
        """
        self.costs = util.gld.computeCosts(cursor=cursor,
                                            powerTable=self.swingTable,
                                            powerColumns=self.swingColumns,
                                            powerInterval=self.swingInterval,
                                            energyPrice=energyPrice,
                                            starttime=self.starttime,
                                            stoptime=self.stoptime,
                                            tCol=tCol,
                                            tapChangeCost=tapChangeCost,
                                            capSwitchCost=capSwitchCost,
                                            tapChangeCount=self.tapChangeCount,
                                            capSwitchCount=self.capSwitchCount,
                                            voltCost=voltCost,
                                            voltdumpDir=self.outDir,
                                            voltdumpFiles=self.voltdumpFiles
                                            )
        
        # Assign fitness to simplify things.
        self.fitness = self.costs['total']