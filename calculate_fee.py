import argparse
import json
import readline
import sys

from fee_calc import (
    FeeCalc,
    FeeCalcError,
    ERROR_INVALID_PARAGRAPH,
    ERROR_INVALID_ZONE,
    ERROR_INVALID_FEE_RANGE,
    ERROR_APPLICABLE_COST_OUT_OF_RANGE,
    load_tables,
)

_DEFAULT_PARAGRAPH_INDEX = 7  # 0-based; §34 Objektplanung Gebäude
DATA_PATH = "data/hoai2013.json"


def _parse_fee_range(s: str) -> float:
    """Parse fee range, allowing ',' and '%'."""
    s = s.strip().replace("%", "").replace(",", ".")
    return float(s)


def _run_interactive(tables) -> tuple:
    """Prompt for paragraph, zone, fee range, applicable cost. Return (paragraph_index, zone, fee_range, applicable_cost)."""
    paragraphs = tables["paragraphs"]
    n = len(paragraphs)

    for index, paragraph in enumerate(paragraphs):
        print(f"{index + 1}\t{paragraph['paragraph']}")

    raw = input("\nLeistungsbereich wählen: ").strip()
    if raw == "":
        selected_paragraph = _DEFAULT_PARAGRAPH_INDEX
    else:
        try:
            selected_paragraph = int(raw) - 1
        except ValueError:
            print("Ungültige Eingabe: Bitte eine Zahl eingeben.")
            sys.exit(1)
    if selected_paragraph < 0 or selected_paragraph >= n:
        print(f"Leistungsbereich muss zwischen 1 und {n} liegen.")
        sys.exit(1)

    raw = input("\nHonorarzone (1-5): ").strip()
    if raw == "":
        zone = 3
    else:
        try:
            zone = int(raw)
        except ValueError:
            print("Ungültige Eingabe: Bitte eine Zahl eingeben.")
            sys.exit(1)

    raw = input("\nHonorarsatz (0.0 - 1.0): ").strip()
    if raw == "":
        fee_range = 0.0
    else:
        try:
            fee_range = _parse_fee_range(raw)
        except ValueError:
            print("Ungültiger Honorarsatz, Eingabe konnte nicht als Zahl gelesen werden.")
            sys.exit(1)

    raw = input("\nAnrechenbare Herstellungskosten: ").strip()
    try:
        applicable_cost = float(raw.replace(",", "."))
    except ValueError:
        print("Ungültige Eingabe für anrechenbare Herstellungskosten.")
        sys.exit(1)

    return selected_paragraph, zone, fee_range, applicable_cost


def _format_error(exc: FeeCalcError) -> str:
    """Return a short, user-friendly message for FeeCalcError."""
    if exc.code == ERROR_INVALID_PARAGRAPH:
        return f"Ungültiger Leistungsbereich: {exc}"
    if exc.code == ERROR_INVALID_ZONE:
        return f"Ungültige Honorarzone: {exc}"
    if exc.code == ERROR_INVALID_FEE_RANGE:
        return f"Ungültiger Honorarsatz: {exc}"
    if exc.code == ERROR_APPLICABLE_COST_OUT_OF_RANGE:
        return f"Anrechenbare Kosten außerhalb des zulässigen Bereichs: {exc}"
    return str(exc)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="HOAI 2013 Honorarberechnung (Leistungsbild, Zone, Satz, Kosten)."
    )
    parser.add_argument(
        "--paragraph", "-p",
        type=int,
        metavar="N",
        help="Leistungsbereich (1-basiert, siehe Liste)",
    )
    parser.add_argument(
        "--zone", "-z",
        type=int,
        metavar="N",
        help="Honorarzone (1-5, je nach Leistungsbild)",
    )
    parser.add_argument(
        "--rate", "-r",
        type=str,
        metavar="R",
        help="Honorarsatz 0.0–1.0 (Komma/Prozent erlaubt)",
    )
    parser.add_argument(
        "--cost", "-c",
        type=float,
        metavar="C",
        help="Anrechenbare Herstellungskosten",
    )
    parser.add_argument(
        "--json", "-j",
        action="store_true",
        help="Ergebnis als JSON ausgeben",
    )
    parser.add_argument(
        "--data",
        default=DATA_PATH,
        metavar="PATH",
        help=f"Pfad zu HOAI-Tabellen (Standard: {DATA_PATH})",
    )
    args = parser.parse_args()

    tables = load_tables(args.data)
    paragraphs = tables["paragraphs"]

    if args.paragraph is not None and args.zone is not None and args.rate is not None and args.cost is not None:
        paragraph_index = args.paragraph - 1
        zone = args.zone
        try:
            fee_range = _parse_fee_range(args.rate)
        except ValueError:
            print("Ungültiger Honorarsatz (--rate). Erlaubt: Zahl zwischen 0.0 und 1.0, ggf. mit Komma oder %.")
            sys.exit(1)
        applicable_cost = args.cost
    else:
        paragraph_index, zone, fee_range, applicable_cost = _run_interactive(tables)

    try:
        calc = FeeCalc(
            tables=tables,
            zone=zone,
            fee_range=fee_range,
            applicable_cost=applicable_cost,
            paragraph_index=paragraph_index,
        )
    except FeeCalcError as exc:
        print(_format_error(exc))
        sys.exit(1)

    if args.json:
        phases_raw = (
            calc.phases
            if isinstance(calc.phases, dict)
            else {p["phase"]: p["percentage"] for p in calc.phases}
        )
        out = {
            "paragraph": calc.paragraph["paragraph"],
            "zone": calc.zone,
            "zone_roman": calc.zone_roman(),
            "fee_range": calc.fee_range,
            "applicable_cost": calc.applicable_cost,
            "fee": calc.fee,
            "phases": {name: round(calc.fee * pct, 2) for name, pct in phases_raw.items()},
        }
        print(json.dumps(out, indent=2, ensure_ascii=False))
    else:
        print(
            f"\n{calc.paragraph['paragraph']}, Honorarzone {calc.zone_roman()}, "
            f"Satz {calc.fee_range}\n"
        )
        print("Gesamthonorar " + "{:10,.2f}".format(calc.fee))
        print("_" * 60)
        calc.print_fee_for_phases()


if __name__ == "__main__":
    main()
