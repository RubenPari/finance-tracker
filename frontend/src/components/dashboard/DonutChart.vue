<script setup lang="ts">
import type { CategoryStats } from '@/types'
import { Doughnut } from 'vue-chartjs'
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js'
import { computed } from 'vue'
import { getChartDefaults } from '@/utils/chartTheme'

ChartJS.register(ArcElement, Tooltip, Legend)

const props = defineProps<{ data: CategoryStats[] }>()

const chartData = computed(() => {
  const defaults = getChartDefaults()
  return {
    labels: props.data.map((d) => d.category_name),
    datasets: [
      {
        data: props.data.map((d) => d.total),
        backgroundColor: props.data.map((d) => d.color),
        borderWidth: 2,
        borderColor: defaults.color,
      },
    ],
  }
})

const options = computed(() => {
  const defaults = getChartDefaults()
  return {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'right' as const,
        labels: {
          color: defaults.color,
          font: defaults.font,
          usePointStyle: true,
          padding: 12,
        },
      },
      tooltip: {
        titleFont: defaults.font,
        bodyFont: { ...defaults.font, family: "'JetBrains Mono', monospace" },
        padding: 10,
        cornerRadius: 6,
      },
    },
  }
})
</script>

<template>
  <div class="h-64">
    <Doughnut :data="chartData" :options="options" />
  </div>
</template>