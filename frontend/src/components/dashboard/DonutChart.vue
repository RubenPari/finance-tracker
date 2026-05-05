<script setup lang="ts">
import type { CategoryStats } from '@/types'
import { Doughnut } from 'vue-chartjs'
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js'
import { computed } from 'vue'

ChartJS.register(ArcElement, Tooltip, Legend)

const props = defineProps<{ data: CategoryStats[] }>()

const chartData = computed(() => ({
  labels: props.data.map((d) => d.category_name),
  datasets: [
    {
      data: props.data.map((d) => d.total),
      backgroundColor: props.data.map((d) => d.color),
      borderWidth: 2,
      borderColor: '#fff',
    },
  ],
}))

const options = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: 'right' as const,
      labels: { padding: 16, usePointStyle: true, font: { size: 12 } },
    },
  },
}
</script>

<template>
  <div class="h-64">
    <Doughnut :data="chartData" :options="options" />
  </div>
</template>
