/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./templates/**/*.html",
    "./apps/**/*.html",
    "./static/**/*.js",
  ],
  theme: {
    extend: {
      colors: {
        primary: { DEFAULT: '#DA291C', dark: '#B8231A', light: '#FEE2E2' },
        'light-grey': '#C8C9C7',
        'dark-grey': '#5B6770',
        success: { DEFAULT: '#059669', light: '#D1FAE5' },
        warning: { DEFAULT: '#D97706', light: '#FEF3C7' },
        danger: { DEFAULT: '#DA291C', light: '#FEE2E2' },
      },
    },
  },
  plugins: [],
}
