/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        felt: {
          dark: '#28503c',
          DEFAULT: '#3d7a5a',
          light: '#4a8a6a',
        },
        poker: {
          dark: '#1a1a2e',
          card: '#1a3a6e',
        },
      },
      animation: {
        'pulse-glow': 'pulse-glow 1.5s ease-in-out infinite',
        'deal-card': 'dealCard 0.3s ease-out',
        'fade-in': 'fadeIn 0.2s ease-out',
      },
    },
  },
  plugins: [],
}

