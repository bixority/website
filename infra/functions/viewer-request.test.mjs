// Tests for viewer-request.js. Run: node --test infra/functions/
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";

const HOST = "www.bixority.com";
const source = readFileSync(new URL("viewer-request.js", import.meta.url), "utf8");
assert.ok(source.includes("${host}"), "the template placeholder is missing");
// Same substitution as templatefile() in cdn.tf.
const handler = new Function(source.replace("${host}", HOST) + "\nreturn handler;")();

function run(uri, host = HOST) {
  const headers = host === null ? {} : { host: { value: host } };
  return handler({ request: { method: "GET", uri, querystring: {}, headers, cookies: {} } });
}

function assertRedirect(result, location) {
  assert.equal(result.statusCode, 301);
  assert.equal(result.headers.location.value, location);
}

test("the home page is served from index.html", () => {
  assert.equal(run("/").uri, "/index.html");
});

test("a folder address is served from its index.html", () => {
  assert.equal(run("/services/").uri, "/services/index.html");
  assert.equal(run("/lv/open-source/").uri, "/lv/open-source/index.html");
});

test("a folder address without the slash is redirected", () => {
  assertRedirect(run("/services"), "/services/");
  assertRedirect(run("/lv"), "/lv/");
  assertRedirect(run("/v1.0/notes"), "/v1.0/notes/");
});

test("files are passed through unchanged", () => {
  for (const uri of ["/404.html", "/robots.txt", "/assets/site.5145083d23.css", "/assets/fonts/geist-latin.woff2"]) {
    assert.equal(run(uri).uri, uri);
  }
});

test("other host names are redirected to the canonical host", () => {
  assertRedirect(run("/services/", "d111111abcdef8.cloudfront.net"), "https://www.bixority.com/services/");
  assertRedirect(run("/", "bixority.com"), "https://www.bixority.com/");
  assertRedirect(run("/", null), "https://www.bixority.com/");
});

test("the host comparison ignores letter case", () => {
  assert.equal(run("/", "WWW.Bixority.com").uri, "/index.html");
});
