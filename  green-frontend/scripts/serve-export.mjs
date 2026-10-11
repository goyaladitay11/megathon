import { createServer } from "node:http";
import { readFile, stat } from "node:fs/promises";
import path from "node:path";

const root = path.resolve("out");
const port = Number(process.env.PORT || 3000);
const host = process.env.HOST || "127.0.0.1";
const mime = {
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".json": "application/json",
  ".txt": "text/plain; charset=utf-8",
  ".png": "image/png",
  ".jpg": "image/jpeg",
  ".svg": "image/svg+xml",
  ".ico": "image/x-icon",
  ".woff": "font/woff",
  ".woff2": "font/woff2",
};

try {
  await stat(path.join(root, "index.html"));
} catch {
  console.error("No exported website found. Run npm run build first.");
  process.exit(1);
}

createServer(async (request, response) => {
  if (!["GET", "HEAD"].includes(request.method)) {
    response.writeHead(405, { Allow: "GET, HEAD" });
    response.end();
    return;
  }

  try {
    const pathname = decodeURIComponent(
      new URL(request.url, "http://localhost").pathname,
    );
    let file = path.resolve(root, `.${pathname}`);
    if (file !== root && !file.startsWith(root + path.sep)) {
      response.writeHead(403);
      response.end();
      return;
    }
    if ((await stat(file)).isDirectory()) file = path.join(file, "index.html");
    const body = await readFile(file);
    response.writeHead(200, {
      "Content-Type": mime[path.extname(file)] || "application/octet-stream",
      "Content-Length": body.length,
    });
    response.end(request.method === "HEAD" ? undefined : body);
  } catch (error) {
    const code =
      error.code === "ENOENT" || error.code === "ENOTDIR" ? 404 : 400;
    response.writeHead(code, { "Content-Type": "text/html; charset=utf-8" });
    const body =
      code === 404
        ? await readFile(path.join(root, "404.html")).catch(() => "Not found")
        : "Bad request";
    response.end(request.method === "HEAD" ? undefined : body);
  }
}).listen(port, host, () => {
  console.log(`Green Home Twin preview: http://${host}:${port}`);
});
