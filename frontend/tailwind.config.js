/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#eef4ff', 100: '#dae6ff', 500: '#3b6fe0',
          600: '#2c57c4', 700: '#22459e',
        },
      },
    },
  },
  plugins: [],
}
