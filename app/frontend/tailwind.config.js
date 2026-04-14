/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          900: '#0f172a',
          800: '#1e293b',
          600: '#2563eb',
        }
      }
    },
  },
  plugins: [],
}