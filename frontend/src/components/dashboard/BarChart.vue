<script setup lang="ts">
import type { MonthlyTrend } from '@/types'
import { Bar } from 'vue-chartjs'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Tooltip,
  Legend,
} from 'chart.js'
import { computed } from 'vue'

ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip, Legend)

const props = defineProps<{ data: MonthlyTrend[] }>()

const chartData = computed(() => ({
  labels: props.data.map((d) => d.month_label),
  datasets: [
    {
      label: 'Spese',
      data: props.data.map((d) => d.expenses),
      backgroundColor: '#EF4444',
      borderRadius: 4,
    },
    {
      label: 'Entrate',
      data: props.data.map((d) => d.income),
      backgroundColor: '#10B981',
      borderRadius: 4,
    },
  ],
}))

const options = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: { legend: { position: 'top' as const } },
  scales: {
    y: { beginAtZero: true, ticks: { callback: (v: unknown) => `${v}€` } },
  },
}
</script>

<template>
  <div class="h-64">
    <Bar :data="chartData" :options="options" />
  </div>
</template>
