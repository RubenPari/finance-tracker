<script setup lang="ts">
/**
 * ModeToggle - Dark/light/system theme selector dropdown.
 *
 * Renders a button that toggles between sun/moon icons based on the
 * current theme, and opens a dropdown menu with three options:
 * light, dark, and auto (system preference).
 *
 * Consumes the `useTheme` composable which manages the theme mode
 * via a reactive `mode` ref that syncs with the document root class.
 */
import { Moon, Sun, Monitor } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { useTheme } from '@/composables/useTheme'

// Reactive theme mode from the theme composable; setting it to
// 'light', 'dark', or 'auto' updates the document class automatically
const { mode } = useTheme()
</script>

<template>
  <DropdownMenu>
    <DropdownMenuTrigger as-child>
      <Button variant="ghost" size="icon" class="shrink-0">
        <Sun class="size-4 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
        <Moon class="absolute size-4 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
        <span class="sr-only">Cambia tema</span>
      </Button>
    </DropdownMenuTrigger>
    <DropdownMenuContent align="end">
      <DropdownMenuItem @click="mode = 'light'">
        <Sun class="mr-2 size-4" />
        Chiaro
      </DropdownMenuItem>
      <DropdownMenuItem @click="mode = 'dark'">
        <Moon class="mr-2 size-4" />
        Scuro
      </DropdownMenuItem>
      <DropdownMenuItem @click="mode = 'auto'">
        <Monitor class="mr-2 size-4" />
        Sistema
      </DropdownMenuItem>
    </DropdownMenuContent>
  </DropdownMenu>
</template>