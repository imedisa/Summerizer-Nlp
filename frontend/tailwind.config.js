/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        'iranyekan': ['IRANYekan', 'sans-serif'],
        'sans': ['IRANYekan', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
