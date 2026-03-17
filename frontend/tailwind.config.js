/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        dark: {
          900: '#0a0a0f',
          800: '#12121a',
          700: '#1a1a26',
          600: '#24243a',
          500: '#2e2e48',
        },
        bull: '#22c55e',
        bear: '#ef4444',
        accent: '#6366f1',
      },
    },
  },
  plugins: [],
};
