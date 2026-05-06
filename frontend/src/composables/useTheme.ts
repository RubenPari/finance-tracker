import { useColorMode } from '@vueuse/core'

export function useTheme() {
  const mode = useColorMode({
    attribute: 'class',
    modes: {
      dark: 'dark',
      light: 'light',
      auto: 'auto',
    },
    storageKey: 'finance-tracker-theme',
  })

  return { mode }
}