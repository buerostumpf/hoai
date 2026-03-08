import os
import plistlib
import FeeCalc

fdPath = "hoai2013_p34.xml"
pl = plistlib.readPlist(fdPath)

line = pl["feetable"]

#  pdb.set_trace()
mFeecalc = FeeCalc.FeeCalc("hoai2013_p34.xml",3,0,250000.0)
    
#  mFeecalc.applicableHigh = mFeecalc.feeTable[mIndex + 1][0]
print("aHk:" + '{:12.2f}'.format(mFeecalc.applicableCost))
print("Gesamthonorar: " + str(mFeecalc.Fee))
mFeecalc.printFeeForPhases()

