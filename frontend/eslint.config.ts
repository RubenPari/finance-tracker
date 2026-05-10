/**
 * ESLint configuration for the Finance Tracker frontend.
 *
 * Combines multiple linting plugins into a flat config:
 * - Vue 3 essential rules (SFC-specific linting)
 * - TypeScript recommended rules (via @vue/eslint-config-typescript)
 * - Playwright recommended rules (E2E test linting)
 * - Vitest recommended rules (unit test linting)
 * - Oxlint (fast Rust-based linter for additional checks)
 * - Prettier integration (disables ESLint rules that conflict with formatting)
 *
 * Applies different rule sets based on file type:
 * - Vue + TypeScript source files
 * - Playwright E2E test files
 * - Vitest unit test files
 */
import { globalIgnores } from 'eslint/config'
import { defineConfigWithVueTs, vueTsConfigs } from '@vue/eslint-config-typescript'
import pluginVue from 'eslint-plugin-vue'
import pluginPlaywright from 'eslint-plugin-playwright'
import pluginVitest from '@vitest/eslint-plugin'
import pluginOxlint from 'eslint-plugin-oxlint'
import skipFormatting from 'eslint-config-prettier/flat'

// To allow more languages other than `ts` in `.vue` files, uncomment the following lines:
// import { configureVueProject } from '@vue/eslint-config-typescript'
// configureVueProject({ scriptLangs: ['ts', 'tsx'] })
// More info at https://github.com/vuejs/eslint-config-typescript/#advanced-setup

export default defineConfigWithVueTs(
  // Lint all Vue and TypeScript source files
  {
    name: 'app/files-to-lint',
    files: ['**/*.{vue,ts,mts,tsx}'],
  },

  // Ignore build output and coverage directories
  globalIgnores(['**/dist/**', '**/dist-ssr/**', '**/coverage/**']),

  // Vue 3 essential rules (SFC template/script/style linting)
  ...pluginVue.configs['flat/essential'],
  // TypeScript recommended rules
  vueTsConfigs.recommended,

  // Playwright rules for E2E test files
  {
    ...pluginPlaywright.configs['flat/recommended'],
    files: ['e2e/**/*.{test,spec}.{js,ts,jsx,tsx}'],
  },

  // Vitest rules for unit test files
  {
    ...pluginVitest.configs.recommended,
    files: ['src/**/__tests__/*'],
  },

  // Oxlint integration (fast Rust-based additional checks)
  ...pluginOxlint.buildFromOxlintConfigFile('.oxlintrc.json'),

  // Disable ESLint rules that conflict with Prettier formatting
  skipFormatting,
)
