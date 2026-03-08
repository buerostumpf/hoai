import os
import plistlib

class FeeCalculation():
    """FeeCalculation calculates Engineering fees based on the German HOAI"""
    
    loadedParagraphs = []
    currentFeeTable = []
    currentNumOfZones = 3

    
    
    def parseParagraphs(filePath = ''):
        """parseParagraphs searches the filepath for pList-files (xml-files)"""

        if len(filepath) == 0:
            filepath = os.getcwd()
        
        for fd in os.listdir(filepath):
            if fd.endswith("xml"):
                loadedParagraphs.append(fd)

    def getParagraph(hoaiPara):
        for para in loadedParagraphs:
            if para.find(hoaiPara):
                with open(para) as fileObject:
                    contentsOfPara = fileObject.read()

        return para

    

    
    def __init__(paragraph,band,feeRange,applicableCost):
        super(FeeCalculation, self).__init__()
        
    
        
if __name__ == '__main__':
    fCalc = FeeCalculation()
       

