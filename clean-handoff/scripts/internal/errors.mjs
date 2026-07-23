const ERROR_CODE_PATTERN = /^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$/u;
const SAFE_LITERAL_PATTERN = /^[\u0020-\u007e]+$/u;
const MAX_ERROR_MESSAGE_LENGTH = 300;
const SAFE_DETAIL_KEY_PATTERN = /^[a-z][a-z0-9_]*$/u;

function safeCode(value) {
  return typeof value === "string" && ERROR_CODE_PATTERN.test(value) && value.length <= 80
    ? value
    : "internal-failure";
}

function safeMessage(value) {
  return typeof value === "string"
    && value.length > 0
    && value.length <= MAX_ERROR_MESSAGE_LENGTH
    && SAFE_LITERAL_PATTERN.test(value)
    ? value
    : "The operation failed without exposing untrusted diagnostics.";
}

function safeEnvelopeLiteral(value, fallback) {
  return typeof value === "string"
    && value.length > 0
    && value.length <= 160
    && SAFE_LITERAL_PATTERN.test(value)
    ? value
    : fallback;
}

function safeDetailValue(value, depth = 0) {
  if (depth > 5) return undefined;
  if (value === null || typeof value === "boolean") return value;
  if (typeof value === "number") return Number.isSafeInteger(value) ? value : undefined;
  if (typeof value === "string") {
    return value.length <= 300 && SAFE_LITERAL_PATTERN.test(value) ? value : undefined;
  }
  if (Array.isArray(value)) {
    if (value.length > 32) return undefined;
    const items = value.map((item) => safeDetailValue(item, depth + 1));
    return items.some((item) => item === undefined) ? undefined : items;
  }
  if (value === null || typeof value !== "object" || Object.getPrototypeOf(value) !== Object.prototype) {
    return undefined;
  }
  const result = {};
  const keys = Object.keys(value);
  if (keys.length > 32 || keys.some((key) => !SAFE_DETAIL_KEY_PATTERN.test(key))) return undefined;
  for (const key of keys.sort()) {
    const child = safeDetailValue(value[key], depth + 1);
    if (child === undefined) return undefined;
    result[key] = child;
  }
  return result;
}

function safeTransaction(value) {
  const transaction = safeDetailValue(value);
  if (transaction === undefined || Array.isArray(transaction) || transaction === null) return null;
  return Buffer.byteLength(JSON.stringify(transaction), "utf8") <= 8 * 1024 ? Object.freeze(transaction) : null;
}

export class SafeFailure extends Error {
  constructor(code, message, options = {}) {
    super(safeMessage(message));
    this.name = "SafeFailure";
    this.code = safeCode(code);
    this.kind = safeCode(options.kind ?? "failure");
    this.transaction = safeTransaction(options.transaction);
  }
}

export function notice(code, message) {
  const safe = new SafeFailure(code, message, { kind: "notice" });
  return Object.freeze({ code: safe.code, message: safe.message });
}

export function asSafeFailure(error) {
  return error instanceof SafeFailure
    ? error
    : new SafeFailure("internal-failure", "The operation failed without exposing untrusted diagnostics.");
}

export function successEnvelope({ schema, command, result, projectRoot = "." }) {
  return {
    schema: safeEnvelopeLiteral(schema, "clean-handoff/unknown"),
    command: safeEnvelopeLiteral(command, "unknown"),
    ok: true,
    project_root: projectRoot === "." ? "." : ".",
    result,
  };
}

export function failureEnvelope(error, { schema, command, projectRoot = "." }) {
  const safe = asSafeFailure(error);
  const envelope = {
    schema: safeEnvelopeLiteral(schema, "clean-handoff/unknown"),
    command: safeEnvelopeLiteral(command, "unknown"),
    ok: false,
    project_root: projectRoot === "." ? "." : ".",
    error: { code: safe.code, message: safe.message },
  };
  if (safe.transaction !== null) envelope.transaction = safe.transaction;
  return envelope;
}
