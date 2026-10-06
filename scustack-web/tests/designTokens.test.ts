import { readFileSync } from 'node:fs'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { describe, expect, it } from 'vitest'

const testDirectory = dirname(fileURLToPath(import.meta.url))

describe('design tokens', () => {
  const css = readFileSync(resolve(testDirectory, '../assets/css/main.css'), 'utf8')
  const tailwind = readFileSync(resolve(testDirectory, '../tailwind.config.ts'), 'utf8')

  it('defines the documented visual scales in the CSS source of truth', () => {
    for (const token of [
      '--color-bg',
      '--color-surface',
      '--color-text',
      '--color-text-secondary',
      '--color-border',
      '--color-success',
      '--color-warning',
      '--color-error',
      '--font-sans',
      '--font-mono',
      '--space-1',
      '--space-12',
      '--radius-sm',
      '--radius-lg',
      '--shadow-sm',
      '--shadow-lg',
    ]) {
      expect(css).toContain(`${token}:`)
    }
  })

  it('references CSS variables from Tailwind instead of duplicating values', () => {
    expect(tailwind).toContain("50: 'var(--color-primary-50)'")
    expect(tailwind).toContain("500: 'var(--color-accent-500)'")
    expect(tailwind).toContain("sans: 'var(--font-sans)'")
    expect(tailwind).toContain("'token-4': 'var(--space-4)'")
    expect(tailwind).toContain("token: 'var(--radius-md)'")
    expect(tailwind).toContain("token: 'var(--shadow-md)'")
    expect(tailwind).not.toMatch(/primary:\s*\{[\s\S]*#[0-9A-F]{6}/i)
  })
})
