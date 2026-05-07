<!--
  Root application component.

  Serves as the top-level container for all routed views.
  The `<RouterView />` dynamically renders the component
  matched by the current URL path.
-->
<script setup lang="ts">
import { RouterView } from 'vue-router'
</script>

<template>
  <RouterView />
</template>
