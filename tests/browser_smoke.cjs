/* Node-only static page smoke test: no external packages. */
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const path = require("node:path");

const root = path.resolve(__dirname, "..");
const html = fs.readFileSync(path.join(root, "web/index.html"), "utf8");
const script = fs.readFileSync(path.join(root, "web/app.js"), "utf8");
assert.match(html, /<script src="\.\/app\.js" defer><\/script>/);
assert.match(html, /<link rel="stylesheet" href="\.\/style\.css">/);
assert.ok(fs.existsSync(path.join(root, "web/style.css")));
assert.doesNotMatch(script, /\bfetch\s*\(/);

const registry = {};
for (const id of ["calculator", "sodium", "glucose", "error", "katz", "hillier", "classification", "delta", "status"]) {
  registry[id] = {
    value: "",
    textContent: "",
    hidden: true,
    handlers: {},
    addEventListener(event, handler) { this.handlers[event] = handler; }
  };
}
registry.sodium.value = "135";
registry.glucose.value = "400";

vm.runInNewContext(script, {
  document: { getElementById(id) { return registry[id]; } }
}, { filename: "web/app.js" });

const submit = registry.calculator.handlers.submit;
const reset = registry.calculator.handlers.reset;
assert.equal(typeof submit, "function");
assert.equal(typeof reset, "function");
submit({ preventDefault() {} });
assert.equal(registry.katz.textContent, "139.80");
assert.equal(registry.hillier.textContent, "142.20");
assert.equal(registry.status.textContent, "Calculated");

registry.glucose.value = "0";
submit({ preventDefault() {} });
assert.equal(registry.error.hidden, false);
assert.equal(registry.status.textContent, "Check inputs");
assert.equal(registry.katz.textContent, "—");

reset();
assert.equal(registry.error.hidden, true);
assert.equal(registry.katz.textContent, "—");
console.log("Browser calculator static and calculation smoke tests passed.");
