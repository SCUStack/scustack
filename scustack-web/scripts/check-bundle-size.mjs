import { readdir, stat } from 'node:fs/promises'
import { fileURLToPath } from 'node:url'
import { join } from 'node:path'

const outputDir = fileURLToPath(new URL('../.output/public/_nuxt/', import.meta.url))
const maxChunkBytes = Number(process.env.SCUSTACK_MAX_CHUNK_BYTES || 1000 * 1024)

async function listFiles(dir) {
  const entries = await readdir(dir, { withFileTypes: true })
  const files = await Promise.all(entries.map(async entry => {
    const path = join(dir, entry.name)
    if (entry.isDirectory()) return listFiles(path)
    return path
  }))
  return files.flat()
}

const files = await listFiles(outputDir)
const jsChunks = []

for (const file of files) {
  if (!file.endsWith('.js')) continue
  const info = await stat(file)
  jsChunks.push({ file, bytes: info.size })
}

const oversized = jsChunks.filter(chunk => chunk.bytes > maxChunkBytes)
const summary = jsChunks
  .sort((a, b) => b.bytes - a.bytes)
  .slice(0, 10)
  .map(chunk => `${Math.round(chunk.bytes / 1024)} KiB ${chunk.file.replace(outputDir, '')}`)

console.log(['Largest JS chunks:', ...summary].join('\n'))

if (oversized.length > 0) {
  console.error(`Bundle guard failed: ${oversized.length} JS chunk(s) exceed ${Math.round(maxChunkBytes / 1024)} KiB.`)
  process.exit(1)
}
