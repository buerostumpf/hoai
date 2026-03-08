import json
import readline

from fee_calc import (
    FeeCalc,
    FeeCalcError,
    load_tables,
)

_DEFAULT_PARAGRAPH = 6


# Use JSON as the canonical data source; fall back to plist if needed.
DATA_PATH = "hoai2013.json"

tables = load_tables(DATA_PATH)

#  phases  = pl["phases"]


#  for phase in phases:
#      print('{:30}'.format(phase) + "\t" + '{:4.2f}'.format(phases[phase]))

#  paragraphs = tables["paragraph"]
paragraphs = tables["paragraphs"]

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
if fee_range_raw == "":
    fee_range = 0.0
else:
    # Normalize: remove %, replace ',' with '.'
    s = fee_range_raw.strip().replace("%", "").replace(",", ".")
    try:
        fee_range = float(s)
    except ValueError:
        print("Ungültiger Honorarsatz, Eingabe konnte nicht als Zahl gelesen werden.")
        raise SystemExit(1)

try:
    applicable_cost = float(input("\nanrechenbare Herstellungskosten: "))
except ValueError:
    print("Ungültige Eingabe für anrechenbare Herstellungskosten.")
    raise SystemExit(1)

try:
    fee_calculation = FeeCalc(
        tables=tables,
        zone=zone,
        fee_range=fee_range,
        applicable_cost=applicable_cost,
        paragraph_index=selected_paragraph,
    )
except FeeCalcError as exc:
    print(f"Fehler bei der Eingabe ({exc.code}): {exc}")
    raise SystemExit(1)

fee = fee_calculation.fee
print("\n" + fee_calculation.paragraph["paragraph"] + 
      ", Honorarzone " + fee_calculation.zone_roman() +
      ", Satz " + str(fee_calculation.fee_range) + "\n" )

print("Gesamthonorar " + '{:10,.2f}'.format(fee))
print("_"*60)

fee_calculation.print_fee_for_phases()

# phases =  fee_calculation.phases
# for phase in phases:
#    print("Phase: {:35} \t % {}".format(phase,phases[phase]))

# print(fee_calculation.get_feecalc_json())
