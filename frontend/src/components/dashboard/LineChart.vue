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

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Legend)

const props = defineProps<{ data: BalancePoint[] }>()

const chartData = computed(() => ({
  labels: props.data.map((d) => d.date.slice(0, 10)),
  datasets: [
    {
      label: 'Saldo',
      data: props.data.map((d) => d.balance),
      borderColor: '#3B82F6',
      backgroundColor: '#3B82F620',
      fill: true,
      tension: 0.3,
      pointRadius: 0,
    },
  ],
}))

const options = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: { legend: { display: false } },
  scales: {
    y: { ticks: { callback: (v: unknown) => `${v}€` } },
  },
}
</script>

<template>
  <div class="h-64">
    <Line :data="chartData" :options="options" />
  </div>
</template>
