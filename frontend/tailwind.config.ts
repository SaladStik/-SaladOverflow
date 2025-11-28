import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // Forest Monstera palette - deep, lush greens
        cream: {
          50: '#FEFEFE',
          100: '#F7F7F2',
          200: '#F0F0E8',
          300: '#E4E6C3',
          DEFAULT: '#F7F7F2',
        },
        sage: {
          50: '#E8F0E8',
          100: '#D4E4D4',
          200: '#B8D4B8',
          300: '#8FB88F',
          400: '#6B9D6B',
          500: '#4A7C4A',
          600: '#3A6B3A',
          700: '#2D5A2D',
          800: '#234823',
          900: '#1A381A',
          DEFAULT: '#4A7C4A',
        },
        charcoal: {
          50: '#B5B7B5',
          100: '#6A6D6A',
          200: '#2C3E2C',
          300: '#1F2E1F',
          400: '#172317',
          500: '#0F1A0F',
          DEFAULT: '#1F2E1F',
        },
      },
      animation: {
        'gradient': 'gradient 8s linear infinite',
      },
      keyframes: {
        gradient: {
          '0%, 100%': {
            'background-size': '200% 200%',
            'background-position': 'left center'
          },
          '50%': {
            'background-size': '200% 200%',
            'background-position': 'right center'
          },
        },
      },
    },
  },
  plugins: [],
}
export default config
