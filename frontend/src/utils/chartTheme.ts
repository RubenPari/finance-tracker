/**
 * Chart.js theme configuration for the Finance Tracker dashboard.
 *
 * Provides colour palettes and default options that adapt to the
 * current dark/light theme. All colours use HSL values derived
 * from the application's CSS design tokens.
 */

/**
 * Get the current theme-dependent colour palette for charts.
 *
 * Detects dark mode by checking the `dark` class on the document root,
 * then returns light or dark variants for text, grid lines, and
 * predefined chart colours.
 *
 * @returns Object containing `color`, `font`, `grid`, `income`, `expense`,
 *   and `chart1`-`chart5` colour values.
 */
export function getChartDefaults() {
  const isDark = document.documentElement.classList.contains('dark')

  return {
    // Text colour: light in dark mode, dark in light mode
    color: isDark ? 'hsl(0 0% 95%)' : 'hsl(222 47% 11%)',
    font: {
      family: "'Inter', system-ui, -apple-system, sans-serif",
      size: 12,
    },
    // Grid line colour
    grid: {
      color: isDark ? 'hsl(222 33% 18%)' : 'hsl(220 13% 91%)',
    },
    // Semantic colours for income/expense series
    income: isDark ? 'hsl(142 71% 55%)' : 'hsl(142 71% 45%)',
    expense: isDark ? 'hsl(0 72% 55%)' : 'hsl(0 72% 51%)',
    // Categorical palette (5 colours for donut/bar charts)
    chart1: isDark ? 'hsl(222 47% 65%)' : 'hsl(222 47% 21%)',
    chart2: isDark ? 'hsl(142 71% 55%)' : 'hsl(142 71% 45%)',
    chart3: isDark ? 'hsl(38 92% 60%)' : 'hsl(38 92% 50%)',
    chart4: isDark ? 'hsl(256 56% 65%)' : 'hsl(256 56% 50%)',
    chart5: isDark ? 'hsl(190 71% 55%)' : 'hsl(190 71% 40%)',
  }
}

/**
 * Get shared Chart.js configuration options for all chart components.
 *
 * Configures responsive sizing, legend styling, tooltip appearance,
 * and axis formatting with theme-aware colours and monospace fonts
 * for numeric values.
 *
 * @returns Chart.js options object suitable for passing to any chart type.
 */
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
        // Monospace font for tooltip body (numeric values)
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
          // Monospace font for y-axis numeric labels
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