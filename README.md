# hoai-python

**hoai-python** is a Python library for calculating professional fees under the German **HOAI 2013 / HOAI 2021** (*Honorarordnung für Architekten und Ingenieure*).

The project provides a reusable calculation engine that reads structured HOAI fee tables and computes architect and engineer fees based on the official fee structure.

The library is designed to be used by different frontends such as:

- command-line tools
- web applications
- desktop applications
- BIM / cost-planning software


---

# Features

- HOAI 2013 / 2021 fee calculation
- configurable fee tables (JSON or plist/XML)
- calculation based on  
  - service profile (*Leistungsbild*)
  - fee zone (*Honorarzone*)
  - fee rate (*Honorarsatz*)
  - chargeable construction costs (*anrechenbare Kosten*) for services for buildings
  - area in hectares for landscape and urban planning projects
- breakdown by **service phases (Leistungsphasen)**
- CLI frontend included
- reusable calculation engine for integration into other tools


---

# Installation

Until the package is published on PyPI you can install it locally:

```bash
pip install .