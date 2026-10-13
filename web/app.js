"use strict";

const form = document.getElementById("calculator");
const sodiumInput = document.getElementById("sodium");
const glucoseInput = document.getElementById("glucose");
const errorElement = document.getElementById("error");
const katzOutput = document.getElementById("katz");
const hillierOutput = document.getElementById("hillier");
const classification = document.getElementById("classification");
const delta = document.getElementById("delta");
const status = document.getElementById("status");

function correctedSodium(sodium, glucose, coefficient) {
  return sodium + coefficient * (glucose - 100) / 100;
}

function format(value) {
  return value.toFixed(2);
}

function clearResults() {
  katzOutput.textContent = "—";
  hillierOutput.textContent = "—";
  classification.textContent = "Enter measurements and calculate to see an estimate.";
  delta.textContent = "";
  status.textContent = "Ready";
}

function parseMeasurement(input, label, min, max) {
  const raw = input.value.trim();
  const value = Number(raw);
  if (!raw || !Number.isFinite(value) || value < min || value > max) {
    throw new RangeError(label + " must be between " + min + " and " + max + ".");
  }
  return value;
}

form.addEventListener("submit", function (event) {
  event.preventDefault();
  errorElement.hidden = true;
  errorElement.textContent = "";
  clearResults();

  try {
    const sodium = parseMeasurement(sodiumInput, "Sodium (mEq/L)", 100, 200);
    const glucose = parseMeasurement(glucoseInput, "Glucose (mg/dL)", 100, 2000);
    const katz = correctedSodium(sodium, glucose, 1.6);
    const hillier = correctedSodium(sodium, glucose, 2.4);

    katzOutput.textContent = format(katz);
    hillierOutput.textContent = format(hillier);
    const label = katz < 135 ? "Below 135 mEq/L" :
                  katz > 145 ? "Above 145 mEq/L" : "135–145 mEq/L";
    classification.textContent = "Katz estimate: " + label +
      " (conventional adult reference interval).";
    delta.textContent = "Difference between estimates: " +
      format(Math.abs(hillier - katz)) + " mEq/L.";
    status.textContent = "Calculated";
  } catch (error) {
    errorElement.textContent = error.message;
    errorElement.hidden = false;
    status.textContent = "Check inputs";
  }
});

form.addEventListener("reset", function () {
  errorElement.hidden = true;
  errorElement.textContent = "";
  clearResults();
});

// Exposed for deterministic browser test harnesses; no network access needed.
if (typeof module !== "undefined" && module.exports) {
  module.exports = { correctedSodium, parseMeasurement };
}
