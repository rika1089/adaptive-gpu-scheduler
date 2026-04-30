import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './app/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        'bg-base':       '#0a0c0f',
        'bg-1':          '#0f1117',
        'bg-2':          '#141720',
        'bg-3':          '#1a1f2e',
        'bg-4':          '#212840',
        'accent-blue':   '#3b82f6',
        'accent-green':  '#10b981',
        'accent-amber':  '#f59e0b',
        'accent-purple': '#8b5cf6',
        'accent-cyan':   '#06b6d4',
        'accent-red':    '#ef4444',
      },
      fontFamily: {
        sans: ['Syne', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      animation: {
        'fade-in':  'fadeIn 0.3s ease forwards',
        'slide-up': 'slideUp 0.35s ease forwards',
        'pulse2':   'pulse2 2s ease-in-out infinite',
      },
      keyframes: {
        fadeIn:  { from: { opacity: '0' }, to: { opacity: '1' } },
        slideUp: { from: { opacity: '0', transform: 'translateY(12px)' }, to: { opacity: '1', transform: 'translateY(0)' } },
        pulse2:  { '0%,100%': { opacity: '1' }, '50%': { opacity: '0.35' } },
      },
    },
  },
  plugins: [],
}
export default config
