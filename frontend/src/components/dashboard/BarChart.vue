<script setup lang="ts">
import type { MonthlyTrend } from '@/types'
import { Bar } from 'vue-chartjs'
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, Tooltip, Legend } from 'chart.js'
import { computed } from 'vue'
import { getChartDefaults, getCommonOptions } from '@/utils/chartTheme'

ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip, Legend)

const props = defineProps<{ data: MonthlyTrend[] }>()

const chartData = computed(() => {
  const defaults = getChartDefaults()
  return {
    labels: props.data.map((d) => d.month_label),
    datasets: [
      {
        label: 'Spese',
        data: props.data.map((d) => d.expenses),
        backgroundColor: defaults.expense,
        borderRadius: 2,
      },
      {
        label: 'Entrate',
        data: props.data.map((d) => d.income),
        backgroundColor: defaults.income,
        borderRadius: 2,
      },
    ],
  }
})

const options = computed(() => {
  const common = getCommonOptions()
  return {
    ...common,
    plugins: {
      ...common.plugins,
      legend: {
        ...common.plugins.legend,
        position: 'top' as const,
      },
    },
    scales: {
      ...common.scales,
      y: {
        ...common.scales.y,
        beginAtZero: true,
        ticks: {
          ...common.scales.y.ticks,
          callback: (v: unknown) => `${v}€`,
        },
      },
    },
  }
})
</script>

<template>
  <div class="h-64">
    <Bar :data="chartData" :options="options" />
  </div>
</template>