import { TextDecoder } from "node:util";

import { SafeFailure } from "./errors.mjs";

export const CONTEXT_HELPER_OUTPUT_SCHEMA = "clean-handoff/helper-output/v2";
export const CONTEXT_LIMITS = Object.freeze({
  structuredInputBytes: 512 * 1024,
  handoffInputBytes: 256 * 1024,
  collectionItems: 100,
  textCharacters: 1000,
});

const DISALLOWED_TEXT = /[\u0000-\u0008\u000b\u000c\u000e-\u001f\u007f-\u009f\u202a-\u202e\u2066-\u2069]/u;
const UTF8_BOM = Buffer.from([0xef, 0xbb, 0xbf]);

export function strictUtf8(value, options = {}) {
  const label = options.label ?? "Input";
  const maximum = options.maxBytes ?? CONTEXT_LIMITS.structuredInputBytes;
  if (!Buffer.isBuffer(value)) {
    throw new SafeFailure("invalid-input", `${label} must be supplied as bytes.`);
  }
  if (!Number.isSafeInteger(maximum) || maximum < 0 || value.length > maximum) {
    throw new SafeFailure("input-too-large", `${label} exceeds the permitted size.`);
  }
  if (value.subarray(0, UTF8_BOM.length).equals(UTF8_BOM)) {
    throw new SafeFailure("invalid-utf8", `${label} must not contain a byte-order mark.`);
  }
  let text;
  try {
    text = new TextDecoder("utf-8", { fatal: true }).decode(value);
  } catch {
    throw new SafeFailure("invalid-utf8", `${label} is not valid UTF-8.`);
  }
  if (DISALLOWED_TEXT.test(text)) {
    throw new SafeFailure("invalid-text", `${label} contains disallowed control or directional characters.`);
  }
  return text;
}

export function parseStrictJson(bytes, options = {}) {
  const text = strictUtf8(bytes, options);
  try {
    return JSON.parse(text);
  } catch {
    throw new SafeFailure("invalid-json", `${options.label ?? "Input"} is not valid JSON.`);
  }
}

export function assertExactKeys(value, expectedKeys, label = "Value") {
  if (value === null || typeof value !== "object" || Array.isArray(value)) {
    throw new SafeFailure("invalid-object", `${label} must be an object.`);
  }
  const actual = Object.keys(value).sort();
  const expected = [...expectedKeys].sort();
  if (actual.length !== expected.length || actual.some((key, index) => key !== expected[index])) {
    throw new SafeFailure("invalid-object-keys", `${label} has an unexpected field set.`);
  }
  return value;
}

export function boundedText(value, label = "Value", maximum = CONTEXT_LIMITS.textCharacters) {
  if (typeof value !== "string" || value.length === 0 || value.length > maximum || DISALLOWED_TEXT.test(value)) {
    throw new SafeFailure("invalid-text", `${label} is missing, unsafe, or too long.`);
  }
  return value;
}

export function boundedTextList(values, label = "Values", options = {}) {
  const maximumItems = options.maximumItems ?? CONTEXT_LIMITS.collectionItems;
  const maximumCharacters = options.maximumCharacters ?? CONTEXT_LIMITS.textCharacters;
  if (!Array.isArray(values) || values.length > maximumItems) {
    throw new SafeFailure("invalid-list", `${label} must be a bounded array.`);
  }
  return values.map((value, index) => boundedText(value, `${label} ${index + 1}`, maximumCharacters));
}

export function redactText(value, maximum = CONTEXT_LIMITS.textCharacters) {
  let result = String(value)
    .replace(/[\u0000-\u0008\u000b\u000c\u000e-\u001f\u007f-\u009f\u202a-\u202e\u2066-\u2069]/gu, " ")
    .replace(/\s+/gu, " ")
    .trim();
  result = result
    .replace(/-----BEGIN [^-]*PRIVATE KEY-----[\s\S]*?-----END [^-]*PRIVATE KEY-----/giu, "[REDACTED: private key]")
    .replace(/\b(Bearer|Basic)\s+[A-Za-z0-9._~+/=-]+/giu, "$1 [REDACTED]")
    .replace(/\b(?:gh[pousr]_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9_-]{20,}|AKIA[A-Z0-9]{16})\b/gu, "[REDACTED]")
    .replace(/\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b/gu, "[REDACTED]")
    .replace(/\b[A-Za-z0-9+/_=-]{64,}\b/gu, "[REDACTED]")
    .replace(/\b(token|secret|password|passwd|api[_-]?key|private[_-]?key|credential|cookie|auth(?:orization)?)\b(\s*(?:=|:)\s*)[^\s,;|]+/giu, "$1$2[REDACTED]")
    .replace(/([?&](?:token|secret|password|passwd|api[_-]?key|credential|auth)=)[^&#\s]+/giu, "$1[REDACTED]")
    .replace(/([a-z][a-z0-9+.-]*:\/\/)[^/@\s]+@/giu, "$1[REDACTED]@");
  if (result.length > maximum) {
    const retained = Math.max(0, maximum - 14);
    result = `${result.slice(0, retained)}...(truncated)`;
  }
  return result;
}
