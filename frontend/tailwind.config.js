/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        background: 'var(--color-background)',
        foreground: 'var(--color-foreground)',
        card: 'var(--color-card)',
        border: 'var(--color-border)',
      },
      animation: {
        'breathing': 'breathing 2s ease-in-out infinite',
        'shimmer': 'shimmer 2s ease-in-out infinite',
        'button-pulse': 'button-pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
      keyframes: {
        breathing: {
          '0%, 100%': { opacity: '0.35' },
          '50%': { opacity: '0.85' },
        },
        shimmer: {
          '0%': { transform: 'translateX(-100%)' },
          '100%': { transform: 'translateX(100%)' },
        },
        'button-pulse': {
          '0%, 100%': { transform: 'scale(1)', boxShadow: '0 0 0 0 rgba(168, 85, 247, 0.4)' },
          '50%': { transform: 'scale(1.02)', boxShadow: '0 0 0 8px rgba(168, 85, 247, 0)' },
        },
      },
    },
  },
  plugins: [],
}
