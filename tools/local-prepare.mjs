import fs from "node:fs";
import path from "node:path";
import { execFileSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { parseDotenv, resolveVariables } from "./local-doctor.mjs";

const root = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const envPath = path.join(root, ".env");
if (!fs.existsSync(envPath)) {
  throw new Error("Create .env from .env.example before preparing the local environment");
}
const original = fs.readFileSync(envPath, "utf8");
const vars = resolveVariables(parseDotenv(original, process.env), process.env);
const configured = vars.get("CHAT_HMAC_FILE")?.trim();
const keyPath = configured ? path.resolve(root, configured) : path.join(root, ".secrets", "chat-hmac");
if (configured && !fs.existsSync(keyPath)) {
  throw new Error("Configured CHAT_HMAC_FILE is missing; restore the existing key or clear the setting for first setup");
}
execFileSync(process.env.PYTHON ?? "python", [path.join(root, "tools", "chat_secrets.py"), keyPath],
  { stdio: "inherit", windowsHide: true });
if (!configured) {
  const value = "CHAT_HMAC_FILE='./.secrets/chat-hmac'";
  const updated = /^CHAT_HMAC_FILE=.*$/m.test(original)
    ? original.replace(/^CHAT_HMAC_FILE=.*$/m, value) : original + "\n" + value + "\n";
  fs.writeFileSync(envPath, updated);
}
console.log("Private chat channel prepared; existing credentials preserved");
