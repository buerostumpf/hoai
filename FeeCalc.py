import plistlib
import json

'''
    These are classes to calculate engineering fees according to the German
    HOAI (Fee ordinance for architects and engineers)
    The input required is a special tpe of XML-File in the plist-format.

    ToDo
    191118. what is the fee.setter  used for? why does the program crash with
    high applicable costs?
    191117: convert internal variables to properties

'''


def _load_fee_tables(fd_path):
    """Load fee tables from either plist/xml or JSON."""
    if fd_path.lower().endswith(".json"):
        with open(fd_path, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        with open(fd_path, "rb") as f:
            return plistlib.load(f)


class FeeCalc():
    def __init__(self, zone, fee_range, applicable_cost, paragraph_number=7,
                 phases={}, fdPath="HonorartabellenHOAI2013.xml", ):
        self._index = paragraph_number
        self._fee = 0.0
        self._pl = _load_fee_tables(fdPath)

        paragraphs = self._pl["paragraphs"]
        # Support both dict-like (original XML) and list-like paragraph storage
        if isinstance(paragraphs, dict):
            for index, key in enumerate(paragraphs):
                if index == paragraph_number:
                    self._paragraph = paragraphs[key]
                    break
        else:
            self._paragraph = paragraphs[paragraph_number]

        self._feetable = self._paragraph["feetable"]
        #  Test einbauen. wert muss <= "zones" sein
        self._zone = zone
        #  Test einbauen. Wert ist zwischen 0.0 und 1.0
        self._fee_range = fee_range
        #  Test einbauen. Wert ist zwischen min Feetable
        # und max Feetable
        self._applicable_cost = applicable_cost
        if self.__is_in_range():
            self.__fee_calc()
        else:
            print("anrechenbare Herstellungskosten ausserhalb der \
            Schwellenwerte")

    @classmethod
    def from_json(cls, json_data):
        zone = json_data["zone"]
        fee_range = json_data["fee_range"]
        applicable_cost = json_data["applicable_cost"]
        return cls(zone, fee_range, applicable_cost)

    def __fee_calc(self):
        # grundlegende parameter aus dr honorartabelle ziehen
        i = 0
        high_line = self._feetable[i]

        while self._applicable_cost > high_line[0]:
            i = i + 1
            high_line = self._feetable[i]

        low_line = self._feetable[i-1]

        applicable_low = low_line[0]
        applicable_high = high_line[0]

        lower_marge_lower_fee = low_line[self._zone]
        lower_marge_higher_fee = low_line[self._zone+1]

        higher_marge_lower_fee = high_line[self._zone]
        higher_marge_higher_fee = high_line[self._zone + 1]

        # dies ist die eigentliche honorarberechnung
        factor_v = (self._applicable_cost - applicable_low) / \
            (applicable_high - applicable_low)

        lower_fee = lower_marge_lower_fee + \
            (higher_marge_lower_fee - lower_marge_lower_fee) * factor_v
        higher_fee = lower_marge_higher_fee + \
            (higher_marge_higher_fee - lower_marge_higher_fee) * factor_v
        self.fee = lower_fee + (higher_fee - lower_fee) * self._fee_range

    def __is_in_range(self):
        # checken, ob die anrechenbaren Kosten
        # innerhalb der Sätze liegen
        low = self._feetable[0][0]
        high = self._feetable[-1][0]
        if low > self._applicable_cost or high < self._applicable_cost:
            return False
        else:
            return True

    def printFeeForPhases(self):
        phases = self._paragraph["phases"]
        if isinstance(phases, dict):
            items = phases.items()
        else:
            # assume list of {"phase": name, "percentage": value}
            items = ((p["phase"], p["percentage"]) for p in phases)
        for key, value in items:
            perc = value
            print('{:35}'.format(key) + "\t" + '{:2.2f}'.format(perc) +
                  '{:10.2f}'.format(self.fee * perc))

# setters and getters, encapsulation
    @property
    def fee(self):
        return float(self._fee)

    @fee.setter
    def fee(self, value):
        self._fee = value

    @property
    def phases(self):
        phases = self._paragraph["phases"]
        return phases

    def set_percentage_for_phase(self, phase_name, phase_percentage):
        # phase is a dictionary with name, percentage as 0.20
        self._paragraph["phases"][phase_name] = phase_percentage

    @property
    def applicable_cost(self):
        return self.__applicable_cost

    @applicable_cost.setter
    def applicable_cost(self, cost):
        # sets the applicable cost after instantiation
        self.__applicable_cost = cost
        self.__fee_calc()

    @property
    def paragraph(self):
        return self._paragraph

    @property
    def fee_range(self):
        return self._fee_range

    @fee_range.setter
    def fee_range(self, value):
        self._fee_range = value
        self.__fee_calc()

    @property
    def zone(self):
        return self._zone

    @zone.setter
    def zone(self, zone):
        self._zone = zone
        self.__fee_calc()

    def zone_roman(self):
        roman_numbers = ["I", "II", "III", "IV", "V"]
        return roman_numbers[self._zone - 1]

    def get_feecalc_json(self):
        calc_settings = {}
        calc_settings["paragraph_number"] = self._index
        calc_settings["zone"] = self._zone
        calc_settings["fee_range"] = self._fee_range
        calc_settings["applicable_cost"] = self._applicable_cost
        calc_settings["phases"] = self._paragraph["phases"]
        json_string = json.dumps(calc_settings, indent=4)
        return json_string
