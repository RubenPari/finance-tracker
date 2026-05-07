<script setup lang="ts">
import type { BalancePoint } from '@/types'
import { Line } from 'vue-chartjs'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Tooltip,
  Legend,
} from 'chart.js'
import { computed } from 'vue'
import { getChartDefaults, getCommonOptions } from '@/utils/chartTheme'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Legend)

const props = defineProps<{ data: BalancePoint[] }>()

const chartData = computed(() => {
  const defaults = getChartDefaults()
  return {
    labels: props.data.map((d) => d.date.slice(0, 10)),
    datasets: [
      {
        label: 'Saldo',
        data: props.data.map((d) => d.balance),
        borderColor: defaults.chart1,
        backgroundColor: `${defaults.chart1}20`,
        fill: true,
        tension: 0.3,
        pointRadius: 0,
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
        display: false,
      },
    },
    scales: {
      ...common.scales,
      y: {
        ...common.scales.y,
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
    <Line :data="chartData" :options="options" />
  </div>
</template>