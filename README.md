hoai-python
===========

This project contains a fee calculation engine for the German *Honorarordnung für Architekten und Ingenieure* (HOAI) 2013. The core logic lives in `FeeCalc.py`, which reads structured fee tables (currently provided as plist/XML or JSON) and computes fees based on:

- **Paragraph / Leistungsbild**
- **Honorarzone**
- **Honorarsatz** (as a fraction between 0.0 and 1.0)
- **Anrechenbare Herstellungskosten**

The script `calculate_fee.py` is a simple CLI frontend that:

- loads the HOAI fee tables,
- lets you choose a paragraph and zone,
- asks for rate and applicable costs,
- prints the total fee and a breakdown per Leistungsphase.

The long-term goal is for `FeeCalc.py` to be a reusable library that can be imported from different frontends (web UI, desktop app, CLI, etc.), all sharing the same calculation rules and data tables.
