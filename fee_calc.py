import json
import plistlib

"""
Core fee calculation logic for HOAI 2013.

This module is intended to be reusable from different frontends
(CLI, web, desktop, etc.). It operates on an in-memory data
structure that contains the HOAI fee tables.
"""


class FeeCalcError(Exception):
    """Base exception for all fee calculation errors."""

    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


ERROR_INVALID_PARAGRAPH = "invalid_paragraph_index"
ERROR_INVALID_ZONE = "invalid_zone"
ERROR_INVALID_FEE_RANGE = "invalid_fee_range"
ERROR_APPLICABLE_COST_OUT_OF_RANGE = "applicable_cost_out_of_range"


def load_tables_from_json(path):
    """Load HOAI tables from a JSON file."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_tables_from_plist(path):
    """Load HOAI tables from a plist/XML file."""
    with open(path, "rb") as f:
        return plistlib.load(f)


def load_tables(path):
    """
    Load HOAI tables from the given path, choosing JSON or plist
    based on the file extension.
    """
    lower = path.lower()
    if lower.endswith(".json"):
        return load_tables_from_json(path)
    return load_tables_from_plist(path)


class FeeCalc:
    def __init__(self, tables, zone, fee_range, applicable_cost, paragraph_index=7):
        """
        Create a fee calculation for a given paragraph.

        :param tables: Parsed HOAI tables (dict with key 'paragraphs').
        :param zone: Honorarzone (1-5, depending on table).
        :param fee_range: Honorarsatz between 0.0 and 1.0.
        :param applicable_cost: Anrechenbare Herstellungskosten.
        :param paragraph_index: Zero-based index into the paragraphs list.
        """
        self._tables = tables
        self._paragraph_index = paragraph_index
        self._fee = 0.0

        self._paragraph = self._resolve_paragraph(paragraph_index)
        self._feetable = self._paragraph["feetable"]

        # validate and assign core inputs
        self._zone = None
        self._fee_range = None
        self._applicable_cost = None

        self._validate_zone(zone)
        self._zone = zone

        self._validate_fee_range(fee_range)
        self._fee_range = fee_range

        self._validate_applicable_cost(applicable_cost)
        self._applicable_cost = applicable_cost

        self.__fee_calc()

    @classmethod
    def from_settings(cls, tables, settings):
        """
        Recreate a FeeCalc instance from a settings dict as produced
        by get_settings().
        """
        return cls(
            tables=tables,
            zone=settings["zone"],
            fee_range=settings["fee_range"],
            applicable_cost=settings["applicable_cost"],
            paragraph_index=settings["paragraph_index"],
        )

    def _resolve_paragraph(self, paragraph_index):
        paragraphs = self._tables["paragraphs"]
        # Support both dict-like (original XML) and list-like paragraph storage
        if isinstance(paragraphs, dict):
            keys = list(paragraphs.keys())
            if paragraph_index < 0 or paragraph_index >= len(keys):
                raise FeeCalcError(
                    ERROR_INVALID_PARAGRAPH,
                    f"Paragraph index {paragraph_index} is out of range 0..{len(keys) - 1}",
                )
            key = keys[paragraph_index]
            return paragraphs[key]
        else:
            if paragraph_index < 0 or paragraph_index >= len(paragraphs):
                raise FeeCalcError(
                    ERROR_INVALID_PARAGRAPH,
                    f"Paragraph index {paragraph_index} is out of range 0..{len(paragraphs) - 1}",
                )
            return paragraphs[paragraph_index]

    def _validate_zone(self, zone):
        first_row = self._paragraph["feetable"][0]
        # index 0 is applicable_cost; we access zone and zone+1
        min_zone = 1
        max_zone = len(first_row) - 2
        if not (min_zone <= zone <= max_zone):
            raise FeeCalcError(
                ERROR_INVALID_ZONE,
                f"Zone {zone} is out of allowed range {min_zone}..{max_zone} "
                f"for paragraph index {self._paragraph_index}",
            )

    def _validate_fee_range(self, fee_range):
        if not (0.0 <= fee_range <= 1.0):
            raise FeeCalcError(
                ERROR_INVALID_FEE_RANGE,
                f"Fee range {fee_range} must be between 0.0 and 1.0",
            )

    def _validate_applicable_cost(self, applicable_cost):
        feetable = self._paragraph["feetable"]
        low = feetable[0][0]
        high = feetable[-1][0]
        if applicable_cost < low or applicable_cost > high:
            raise FeeCalcError(
                ERROR_APPLICABLE_COST_OUT_OF_RANGE,
                f"Applicable cost {applicable_cost} is outside allowed range "
                f"{low}..{high} for paragraph index {self._paragraph_index}",
            )

    def __fee_calc(self):
        # grundlegende parameter aus der honorartabelle ziehen
        i = 0
        high_line = self._feetable[i]

        while self._applicable_cost > high_line[0]:
            i += 1
            high_line = self._feetable[i]

        low_line = self._feetable[i - 1]

        applicable_low = low_line[0]
        applicable_high = high_line[0]

        lower_marge_lower_fee = low_line[self._zone]
        lower_marge_higher_fee = low_line[self._zone + 1]

        higher_marge_lower_fee = high_line[self._zone]
        higher_marge_higher_fee = high_line[self._zone + 1]

        # dies ist die eigentliche honorarberechnung
        factor_v = (self._applicable_cost - applicable_low) / (
            applicable_high - applicable_low
        )

        lower_fee = lower_marge_lower_fee + (
            higher_marge_lower_fee - lower_marge_lower_fee
        ) * factor_v
        higher_fee = lower_marge_higher_fee + (
            higher_marge_higher_fee - lower_marge_higher_fee
        ) * factor_v
        self.fee = lower_fee + (higher_fee - lower_fee) * self._fee_range

    def print_fee_for_phases(self):
        phases = self._paragraph["phases"]
        if isinstance(phases, dict):
            items = phases.items()
        else:
            # assume list of {"phase": name, "percentage": value}
            items = ((p["phase"], p["percentage"]) for p in phases)
        for name, value in items:
            perc = value
            print(
                "{:35}".format(name)
                + "\t"
                + "{:2.2f}".format(perc)
                + "{:10.2f}".format(self.fee * perc)
            )

    # properties
    @property
    def fee(self):
        return float(self._fee)

    @fee.setter
    def fee(self, value):
        self._fee = value

    @property
    def phases(self):
        return self._paragraph["phases"]

    def set_percentage_for_phase(self, phase_name, phase_percentage):
        # phase is a dictionary with name, percentage as 0.20
        self._paragraph["phases"][phase_name] = phase_percentage

    @property
    def applicable_cost(self):
        return self._applicable_cost

    @applicable_cost.setter
    def applicable_cost(self, cost):
        self._validate_applicable_cost(cost)
        self._applicable_cost = cost
        self.__fee_calc()

    @property
    def paragraph(self):
        return self._paragraph

    @property
    def fee_range(self):
        return self._fee_range

    @fee_range.setter
    def fee_range(self, value):
        self._validate_fee_range(value)
        self._fee_range = value
        self.__fee_calc()

    @property
    def zone(self):
        return self._zone

    @zone.setter
    def zone(self, zone):
        self._validate_zone(zone)
        self._zone = zone
        self.__fee_calc()

    def zone_roman(self):
        roman_numbers = ["I", "II", "III", "IV", "V"]
        return roman_numbers[self._zone - 1]

    def get_settings(self):
        calc_settings = {
            "paragraph_index": self._paragraph_index,
            "zone": self._zone,
            "fee_range": self._fee_range,
            "applicable_cost": self._applicable_cost,
            "phases": self._paragraph["phases"],
        }
        return calc_settings

    def get_settings_json(self):
        return json.dumps(self.get_settings(), indent=4)

