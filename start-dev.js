#!/usr/bin/env node
/**
 * Cross-platform Node.js launcher for PolicyRAG
 * Works on Windows, Mac, and Linux
 * Usage: node start-dev.js
 */

const { spawn } = require("child_process");
const path = require("path");
const http = require("http");

const rootDir = __dirname;
const backendDir = path.join(rootDir, "backend");
const frontendDir = path.join(rootDir, "frontend");

const isWindows = process.platform === "win32";

const BACKEND_PORT = Number(process.env.BACKEND_PORT || 8001);
const FRONTEND_PORT_START = Number(process.env.FRONTEND_PORT || 5173);

console.log(
  "======================================================================",
);
console.log("   Policy RAG Application - Development Launcher");
console.log(
  "======================================================================\n",
);

// Check if Ollama is running
function checkOllama() {
  return new Promise((resolve) => {
    const req = http.get("http://localhost:11434/api/tags", (res) => {
      console.log("[OK] Ollama is running");
      resolve(true);
    });
    req.on("error", () => {
      console.log("[WARNING] Ollama not detected - app will work in demo mode");
      resolve(false);
    });
    req.setTimeout(2000, () => {
      req.destroy();
      resolve(false);
    });
  });
}

// Start backend server
function isHttpUp(url, timeoutMs = 800) {
  return new Promise((resolve) => {
    const req = http.get(url, (res) => {
      res.resume();
      resolve(true);
    });
    req.on("error", () => resolve(false));
    req.setTimeout(timeoutMs, () => {
      req.destroy();
      resolve(false);
    });
  });
}

function isPortFree(port) {
  return new Promise((resolve) => {
    const net = require("net");
    const server = net.createServer();
    server.unref();
    server.on("error", () => resolve(false));
    server.listen({ port, host: "127.0.0.1" }, () => {
      server.close(() => resolve(true));
    });
  });
}

async function findFreePort(startPort, maxTries = 50) {
  for (let i = 0; i < maxTries; i++) {
    const port = startPort + i;
    // If we can bind locally, it's free
    // eslint-disable-next-line no-await-in-loop
    const free = await isPortFree(port);
    if (free) return port;
  }
  return startPort;
}

async function startBackend() {
  console.log(`\n[START] Starting Backend Server (Port ${BACKEND_PORT})...`);

  // If already up, don't spawn another server
  const alreadyUp = await isHttpUp(
    `http://localhost:${BACKEND_PORT}/docs`,
    500,
  );
  if (alreadyUp) {
    console.log(`[OK] Backend already running on port ${BACKEND_PORT}`);
    return null;
  }

  const backend = spawn(
    "python",
    [
      "-m",
      "uvicorn",
      "app.main:app",
      "--host",
      "0.0.0.0",
      "--port",
      String(BACKEND_PORT),
    ],
    {
      cwd: backendDir,
      shell: true,
      stdio: "inherit",
    },
  );

  backend.on("error", (err) => {
    console.error("[ERROR] Failed to start backend:", err.message);
  });

  return backend;
}

// Start frontend server
async function startFrontend(port) {
  console.log(`[START] Starting Frontend Dev Server (Port ${port})...\n`);

  const npmCmd = isWindows ? "npm.cmd" : "npm";
  const frontend = spawn(npmCmd, ["run", "dev", "--", "--port", String(port)], {
    cwd: frontendDir,
    shell: true,
    stdio: "inherit",
  });

  frontend.on("error", (err) => {
    console.error("[ERROR] Failed to start frontend:", err.message);
  });

  return frontend;
}

// Open browser
function openBrowser(frontendPort) {
  setTimeout(() => {
    console.log(`\n[BROWSER] Opening http://localhost:${frontendPort}...\n`);
    const cmd = isWindows
      ? "start"
      : process.platform === "darwin"
        ? "open"
        : "xdg-open";
    spawn(cmd, [`http://localhost:${frontendPort}`], {
      shell: true,
      stdio: "ignore",
    });
  }, 5000);
}

// Main function
async function main() {
  await checkOllama();

  const frontendPort = await findFreePort(FRONTEND_PORT_START, 20);
  const backend = await startBackend();
  await new Promise((resolve) => setTimeout(resolve, 1200));
  const frontend = await startFrontend(frontendPort);

  openBrowser(frontendPort);

  console.log(
    "======================================================================",
  );
  console.log("   Services Started!");
  console.log(
    "======================================================================",
  );
  console.log(`   Backend:  http://localhost:${BACKEND_PORT}`);
  console.log(`   Frontend: http://localhost:${frontendPort}`);
  console.log(`   API Docs: http://localhost:${BACKEND_PORT}/docs`);
  console.log(
    "======================================================================\n",
  );
  console.log("Press Ctrl+C to stop all servers\n");

  // Handle shutdown
  const cleanup = () => {
    console.log("\n\nShutting down servers...");
    if (backend) backend.kill();
    if (frontend) frontend.kill();
    process.exit(0);
  };

  process.on("SIGINT", cleanup);
  process.on("SIGTERM", cleanup);
}

main().catch((err) => {
  console.error("Failed to start:", err);
  process.exit(1);
});
