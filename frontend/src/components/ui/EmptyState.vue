<script setup lang="ts">
defineProps<{ message: string }>()
</script>

<template>
  <div class="card py-12 text-center text-gray-400">
    {{ message }}
  </div>
</template>
