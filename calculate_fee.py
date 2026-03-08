import os
import plistlib
import readline
import json
from FeeCalc import FeeCalc

_DEFAULT_PARAGRAPH = 6


def load_fee_config(fd_path):
    """Load fee configuration from either plist/xml or JSON."""
    if fd_path.lower().endswith(".json"):
        with open(fd_path, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        with open(fd_path, "rb") as f:
            return plistlib.load(f)


# fdPath = "HonorartabellenHOAI2013.xml"
fdPath = "HOAI2013.plist"

pl = load_fee_config(fdPath)

#  phases  = pl["phases"]


#  for phase in phases:
#      print('{:30}'.format(phase) + "\t" + '{:4.2f}'.format(phases[phase]))

#  paragraphs = pl["paragraph"]
paragraphs = pl["paragraphs"]

for index, paragraph in enumerate(paragraphs):
    print(str(index + 1) + "\t" + paragraph["paragraph"])

selected_paragraph = input("\nLeistungsbereich wählen: ")
if selected_paragraph == '':
    selected_paragraph = 8
else:
    selected_paragraph = int(selected_paragraph) - 1
                          
zone = input("\nHonorarzone (1-5): ")
if zone =='':
    zone = 3
else:
    zone = int(zone)

fee_range_raw = input("\nHonorarsatz (0.0 -1.0): ")
if fee_range_raw == '':
    fee_range = 0.0
else:
    # Normalize: remove %, replace ',' with '.'
    s = fee_range_raw.strip().replace('%', '').replace(',', '.')
    try:
        fee_range = float(s)
    except ValueError:
        print("Ungültiger Honorarsatz, setze auf 0.0")
        fee_range = 0.0

applicable_cost = float(input("\nanrechenbare Herstellungskosten: "))

fee_calculation = FeeCalc(zone,fee_range,applicable_cost,selected_paragraph)

fee = fee_calculation.fee
print("\n" + fee_calculation.paragraph["paragraph"] + 
      ", Honorarzone " + fee_calculation.zone_roman() +
      ", Satz " + str(fee_calculation.fee_range) + "\n" )

print("Gesamthonorar " + '{:10,.2f}'.format(fee))
print("_"*60)

fee_calculation.printFeeForPhases()

# phases =  fee_calculation.phases
# for phase in phases:
#    print("Phase: {:35} \t % {}".format(phase,phases[phase]))

# print(fee_calculation.get_feecalc_json())
