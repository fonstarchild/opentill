#!/usr/bin/env node
/**
 * Build backend — bundles the FastAPI Python app into a single executable
 * using PyInstaller, places it in src-tauri/binaries/ with the correct
 * Tauri sidecar naming convention.
 *
 * Usage:
 *   node scripts/build-backend.js
 *
 * Environment variables:
 *   PYTHON     - Python executable to use (default: python3)
 *   SKIP_VERIFY - Set to "1" to skip health check after build
 */

import { execSync, spawnSync } from 'child_process'
import { existsSync, mkdirSync, renameSync } from 'fs'
import { join, resolve } from 'path'
import { platform, arch } from 'os'

const ROOT = resolve(import.meta.dirname, '..')
const BINARIES_DIR = join(ROOT, 'src-tauri', 'binaries')
const ENTRY_POINT = join(ROOT, 'backend', 'main_entry.py')
const DIST_DIR = join(ROOT, 'dist')
const PYTHON = process.env.PYTHON || 'python3'

// ── Platform target triple ───────────────────────────────────────────────────
function getTargetTriple() {
  const p = platform()
  const a = arch()

  const archMap = {
    x64: 'x86_64',
    arm64: 'aarch64',
    arm: 'armv7',
  }
  const archStr = archMap[a] || a

  if (p === 'darwin') return `${archStr}-apple-darwin`
  if (p === 'win32') return `${archStr}-pc-windows-msvc`
  return `${archStr}-unknown-linux-gnu`
}

const triple = getTargetTriple()
const isWindows = platform() === 'win32'
const binaryName = `opentill-backend-${triple}${isWindows ? '.exe' : ''}`
const destPath = join(BINARIES_DIR, binaryName)

console.log(`\n🏗  Building Opentill backend for ${triple}...\n`)

// ── Ensure output dirs ───────────────────────────────────────────────────────
mkdirSync(BINARIES_DIR, { recursive: true })

// ── Verify PyInstaller is available ─────────────────────────────────────────
const pyinstallerCheck = spawnSync(PYTHON, ['-m', 'PyInstaller', '--version'])
if (pyinstallerCheck.status !== 0) {
  console.error('❌ PyInstaller not found. Install it with: pip install pyinstaller')
  process.exit(1)
}

// ── Run PyInstaller ──────────────────────────────────────────────────────────
const pyinstallerArgs = [
  '-m', 'PyInstaller',
  '--onefile',
  '--noconsole',
  '--name', 'opentill-backend',
  '--distpath', DIST_DIR,
  '--specpath', join(ROOT, 'build'),
  '--workpath', join(ROOT, 'build', 'pyinstaller-work'),
  // Include backend package
  '--add-data', `${join(ROOT, 'backend')}${isWindows ? ';' : ':'}backend`,
  // Hidden imports for SQLModel/SQLAlchemy
  '--hidden-import', 'sqlmodel',
  '--hidden-import', 'sqlalchemy.dialects.sqlite',
  '--hidden-import', 'uvicorn.logging',
  '--hidden-import', 'uvicorn.loops.auto',
  '--hidden-import', 'uvicorn.protocols.http.auto',
  '--hidden-import', 'uvicorn.protocols.websockets.auto',
  '--hidden-import', 'uvicorn.lifespan.on',
  ENTRY_POINT,
]

console.log(`Running: ${PYTHON} ${pyinstallerArgs.join(' ')}\n`)

try {
  execSync(`${PYTHON} ${pyinstallerArgs.join(' ')}`, {
    stdio: 'inherit',
    cwd: ROOT,
  })
} catch (err) {
  console.error('❌ PyInstaller build failed')
  process.exit(1)
}

// ── Move binary to src-tauri/binaries/ ──────────────────────────────────────
const builtBinaryName = `opentill-backend${isWindows ? '.exe' : ''}`
const builtPath = join(DIST_DIR, builtBinaryName)

if (!existsSync(builtPath)) {
  console.error(`❌ Built binary not found at: ${builtPath}`)
  process.exit(1)
}

renameSync(builtPath, destPath)
console.log(`\n✅ Binary moved to: ${destPath}`)

// ── Health check ─────────────────────────────────────────────────────────────
if (process.env.SKIP_VERIFY === '1') {
  console.log('⏭  Skipping health check (SKIP_VERIFY=1)')
  process.exit(0)
}

console.log('\n🔍 Verifying backend starts correctly...')

import { spawn } from 'child_process'

const proc = spawn(destPath, [], {
  env: { ...process.env, OPENTILL_PORT: '47899' },
  stdio: 'pipe',
})

let verified = false
const timeout = setTimeout(() => {
  if (!verified) {
    proc.kill()
    console.error('❌ Backend did not start within 10 seconds')
    process.exit(1)
  }
}, 10_000)

// Poll health endpoint
async function checkHealth(retries = 15) {
  for (let i = 0; i < retries; i++) {
    await new Promise(r => setTimeout(r, 1000))
    try {
      const res = await fetch('http://localhost:47899/api/health')
      if (res.ok) {
        const data = await res.json()
        verified = true
        clearTimeout(timeout)
        proc.kill()
        console.log(`✅ Health check passed: ${JSON.stringify(data)}\n`)
        console.log('🎉 Backend build complete!')
        return
      }
    } catch (_) { /* retry */ }
  }
  clearTimeout(timeout)
  proc.kill()
  console.error('❌ Health check failed after retries')
  process.exit(1)
}

checkHealth()
