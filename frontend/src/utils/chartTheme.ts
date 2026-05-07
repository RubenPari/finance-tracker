export function getChartDefaults() {
  const isDark = document.documentElement.classList.contains('dark')

  return {
    color: isDark ? 'hsl(0 0% 95%)' : 'hsl(222 47% 11%)',
    font: {
      family: "'Inter', system-ui, -apple-system, sans-serif",
      size: 12,
    },
    grid: {
      color: isDark ? 'hsl(222 33% 18%)' : 'hsl(220 13% 91%)',
    },
    income: isDark ? 'hsl(142 71% 55%)' : 'hsl(142 71% 45%)',
    expense: isDark ? 'hsl(0 72% 55%)' : 'hsl(0 72% 51%)',
    chart1: isDark ? 'hsl(222 47% 65%)' : 'hsl(222 47% 21%)',
    chart2: isDark ? 'hsl(142 71% 55%)' : 'hsl(142 71% 45%)',
    chart3: isDark ? 'hsl(38 92% 60%)' : 'hsl(38 92% 50%)',
    chart4: isDark ? 'hsl(256 56% 65%)' : 'hsl(256 56% 50%)',
    chart5: isDark ? 'hsl(190 71% 55%)' : 'hsl(190 71% 40%)',
  }
}

export function getCommonOptions() {
  const defaults = getChartDefaults()

  return {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
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
    scales: {
      x: {
        ticks: {
          color: defaults.color,
          font: { ...defaults.font, size: 11 },
        },
        grid: {
          color: defaults.grid.color,
        },
        border: {
          color: defaults.grid.color,
        },
      },
      y: {
        ticks: {
          color: defaults.color,
          font: { ...defaults.font, family: "'JetBrains Mono', monospace", size: 11 },
        },
        grid: {
          color: defaults.grid.color,
        },
        border: {
          color: defaults.grid.color,
        },
      },
    },
  }
}