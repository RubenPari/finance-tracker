/**
 * Vitest unit test configuration.
 *
 * Merges the base Vite configuration with Vitest-specific settings:
 * - Uses jsdom as the test environment (for DOM APIs in Vue components).
 * - Excludes E2E tests (handled by Playwright).
 * - Sets the test root to the frontend directory.
 */
import { fileURLToPath } from 'node:url'
import { mergeConfig, defineConfig, configDefaults } from 'vitest/config'
import viteConfig from './vite.config'

export default mergeConfig(
  viteConfig,
  defineConfig({
    test: {
      // jsdom provides a browser-like DOM environment for Vue component tests
      environment: 'jsdom',
      // Exclude E2E tests (Playwright handles those separately)
      exclude: [...configDefaults.exclude, 'e2e/**'],
      root: fileURLToPath(new URL('./', import.meta.url)),
    },
  }),
)
