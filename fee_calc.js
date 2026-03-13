/**
 * Core fee calculation logic for HOAI 2013.
 *
 * This module is intended to be reusable from different frontends
 * (CLI, web, desktop, etc.). It operates on an in-memory data
 * structure that contains the HOAI fee tables.
 *
 * Node: use loadTables(path) for .json files.
 * Browser: fetch the JSON, parse it, and pass the object to new FeeCalc(tables, ...).
 */

// --- Error and constants ---

export const ERROR_INVALID_PARAGRAPH = "invalid_paragraph_index";
export const ERROR_INVALID_ZONE = "invalid_zone";
export const ERROR_INVALID_FEE_RANGE = "invalid_fee_range";
export const ERROR_APPLICABLE_COST_OUT_OF_RANGE = "applicable_cost_out_of_range";

export class FeeCalcError extends Error {
  constructor(code, message) {
    super(message);
    this.name = "FeeCalcError";
    this.code = code;
    Object.setPrototypeOf(this, FeeCalcError.prototype);
  }
}

// --- Table loading (Node.js; for browser, fetch JSON and pass parsed object) ---

/**
 * Load HOAI tables from a JSON file (Node.js).
 * @param {string} path - Path to the JSON file
 * @returns {Promise<object>} Parsed HOAI tables
 */
export async function loadTablesFromJson(path) {
  const { createRequire } = await import("node:module");
  const require = createRequire(import.meta.url);
  const fs = require("node:fs");
  const data = fs.readFileSync(path, "utf-8");
  return JSON.parse(data);
}

/**
 * Load HOAI tables from the given path. Only .json is supported in this port.
 * For plist support, use a package like 'plist' and add loadTablesFromPlist.
 * @param {string} path - Path to the JSON or plist file
 * @returns {Promise<object>} Parsed HOAI tables
 */
export async function loadTables(path) {
  const lower = path.toLowerCase();
  if (lower.endsWith(".json")) {
    return await loadTablesFromJson(path);
  }
  throw new Error(`Unsupported format: only .json is supported (path: ${path})`);
}

// --- FeeCalc class ---

export class FeeCalc {
  /**
   * Create a fee calculation for a given paragraph.
   *
   * @param {object} tables - Parsed HOAI tables (object with key 'paragraphs').
   * @param {number} zone - Honorarzone (1-5, depending on table).
   * @param {number} feeRange - Honorarsatz between 0.0 and 1.0.
   * @param {number} applicableCost - Anrechenbare Herstellungskosten.
   * @param {number} [paragraphIndex=7] - Zero-based index into the paragraphs list.
   */
  constructor(tables, zone, feeRange, applicableCost, paragraphIndex = 7) {
    this._tables = tables;
    this._paragraphIndex = paragraphIndex;
    this._fee = 0;

    this._paragraph = this._resolveParagraph(paragraphIndex);
    this._feetable = this._paragraph.feetable;

    this._zone = null;
    this._feeRange = null;
    this._applicableCost = null;

    this._validateZone(zone);
    this._zone = zone;

    this._validateFeeRange(feeRange);
    this._feeRange = feeRange;

    this._validateApplicableCost(applicableCost);
    this._applicableCost = applicableCost;

    this._feeCalc();
  }

  /**
   * Recreate a FeeCalc instance from a settings object as produced by getSettings().
   */
  static fromSettings(tables, settings) {
    return new FeeCalc(
      tables,
      settings.zone,
      settings.fee_range,
      settings.applicable_cost,
      settings.paragraph_index
    );
  }

  _resolveParagraph(paragraphIndex) {
    const paragraphs = this._tables.paragraphs;
    if (typeof paragraphs === "object" && paragraphs !== null && !Array.isArray(paragraphs)) {
      const keys = Object.keys(paragraphs);
      if (paragraphIndex < 0 || paragraphIndex >= keys.length) {
        throw new FeeCalcError(
          ERROR_INVALID_PARAGRAPH,
          `Paragraph index ${paragraphIndex} is out of range 0..${keys.length - 1}`
        );
      }
      return paragraphs[keys[paragraphIndex]];
    }
    if (paragraphIndex < 0 || paragraphIndex >= paragraphs.length) {
      throw new FeeCalcError(
        ERROR_INVALID_PARAGRAPH,
        `Paragraph index ${paragraphIndex} is out of range 0..${paragraphs.length - 1}`
      );
    }
    return paragraphs[paragraphIndex];
  }

  _validateZone(zone) {
    const firstRow = this._paragraph.feetable[0];
    const minZone = 1;
    let maxZone = this._paragraph.zones;
    if (maxZone == null) {
      maxZone = firstRow.length - 2;
    }
    if (!(minZone <= zone && zone <= maxZone)) {
      throw new FeeCalcError(
        ERROR_INVALID_ZONE,
        `Zone ${zone} is out of allowed range ${minZone}..${maxZone} for paragraph index ${this._paragraphIndex}`
      );
    }
  }

  _validateFeeRange(feeRange) {
    if (!(0 <= feeRange && feeRange <= 1)) {
      throw new FeeCalcError(
        ERROR_INVALID_FEE_RANGE,
        `Fee range ${feeRange} must be between 0.0 and 1.0`
      );
    }
  }

  _validateApplicableCost(applicableCost) {
    const feetable = this._paragraph.feetable;
    const low = feetable[0][0];
    const high = feetable[feetable.length - 1][0];
    if (applicableCost < low || applicableCost > high) {
      throw new FeeCalcError(
        ERROR_APPLICABLE_COST_OUT_OF_RANGE,
        `Applicable cost ${applicableCost} is outside allowed range ${low}..${high} for paragraph index ${this._paragraphIndex}`
      );
    }
  }

  _feeCalc() {
    let i = 0;
    let highLine = this._feetable[i];

    while (this._applicableCost > highLine[0]) {
      i += 1;
      highLine = this._feetable[i];
    }

    const lowLine = this._feetable[i - 1];
    const applicableLow = lowLine[0];
    const applicableHigh = highLine[0];

    const lowerMargeLowerFee = lowLine[this._zone];
    const lowerMargeHigherFee = lowLine[this._zone + 1];
    const higherMargeLowerFee = highLine[this._zone];
    const higherMargeHigherFee = highLine[this._zone + 1];

    const factorV =
      (this._applicableCost - applicableLow) / (applicableHigh - applicableLow);

    const lowerFee =
      lowerMargeLowerFee + (higherMargeLowerFee - lowerMargeLowerFee) * factorV;
    const higherFee =
      lowerMargeHigherFee + (higherMargeHigherFee - lowerMargeHigherFee) * factorV;
    this._fee = lowerFee + (higherFee - lowerFee) * this._feeRange;
  }

  /**
   * Print fee for each phase to console (name, percentage, fee amount).
   */
  printFeeForPhases() {
    const phases = this._paragraph.phases;
    const items = Array.isArray(phases)
      ? phases.map((p) => [p.phase, p.percentage])
      : Object.entries(phases);
    for (const [name, value] of items) {
      const perc = value;
      const feeAmount = this.fee * perc;
      console.log(
        `${name.padEnd(35)}\t${perc.toFixed(2)}${feeAmount.toFixed(2).padStart(10)}`
      );
    }
  }

  setPercentageForPhase(phaseName, phasePercentage) {
    this._paragraph.phases[phaseName] = phasePercentage;
  }

  zoneRoman() {
    const romanNumbers = ["I", "II", "III", "IV", "V"];
    return romanNumbers[this._zone - 1];
  }

  getSettings() {
    return {
      paragraph_index: this._paragraphIndex,
      zone: this._zone,
      fee_range: this._feeRange,
      applicable_cost: this._applicableCost,
      phases: this._paragraph.phases,
    };
  }

  getSettingsJson() {
    return JSON.stringify(this.getSettings(), null, 4);
  }

  // --- Getters / setters ---

  get fee() {
    return Number(this._fee);
  }

  set fee(value) {
    this._fee = value;
  }

  get phases() {
    return this._paragraph.phases;
  }

  get applicable_cost() {
    return this._applicableCost;
  }

  set applicable_cost(cost) {
    this._validateApplicableCost(cost);
    this._applicableCost = cost;
    this._feeCalc();
  }

  get paragraph() {
    return this._paragraph;
  }

  get fee_range() {
    return this._feeRange;
  }

  set fee_range(value) {
    this._validateFeeRange(value);
    this._feeRange = value;
    this._feeCalc();
  }

  get zone() {
    return this._zone;
  }

  set zone(zone) {
    this._validateZone(zone);
    this._zone = zone;
    this._feeCalc();
  }
}
