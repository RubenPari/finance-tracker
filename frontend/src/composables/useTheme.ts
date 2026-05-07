/**
 * Theme switching composable for dark/light mode.
 *
 * Wraps `@vueuse/core`'s `useColorMode` to provide a reactive `mode`
 * reference that syncs with the `class` attribute on the document root
 * and persists the user's preference in localStorage.
 */
import { useColorMode } from '@vueuse/core'

/**
 * Use the application theme.
 *
 * @returns An object containing the reactive `mode` ref
 *   (values: `"dark"`, `"light"`, `"auto"`).
 */
export function useTheme() {
  const mode = useColorMode({
    // Apply theme as a class on the <html> element
    attribute: 'class',
    modes: {
      dark: 'dark',
      light: 'light',
      auto: 'auto',
    },
    // Persistent storage key for the user's theme preference
    storageKey: 'finance-tracker-theme',
  })

  return { mode }
}