<script setup lang="ts">
import { BarChart3 } from 'lucide-vue-next'
import ModeToggle from '@/components/ModeToggle.vue'
</script>

<template>
  <div class="flex min-h-screen flex-col items-center justify-center bg-background p-4">
    <div class="absolute right-4 top-4">
      <ModeToggle />
    </div>
    <div class="mb-8 flex items-center gap-3">
      <div
        class="flex size-10 items-center justify-center rounded-xl bg-primary text-primary-foreground"
      >
        <BarChart3 class="size-5" />
      </div>
      <h1 class="text-2xl font-bold tracking-tight">Finance Tracker</h1>
    </div>
    <slot />
  </div>
</template>