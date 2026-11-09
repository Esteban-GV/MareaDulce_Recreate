/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        aguamarina: {
          300: '#A9E0D6',
          500: '#56C7B6',
          600: '#4BBBAA',
          700: '#47B5A5',
        },
        petroleo: {
          500: '#245B59',
          600: '#1C4745',
        },
        menta: {
          100: '#F4F8F6',
          500: '#E1F3ED',
        },
        crema: {
          100: '#FFF9F0',
          200: '#F3EBDD',
          300: '#E6DCCB',
        },
        coral: {
          500: '#ED978C',
        },
        vainilla: {
          500: '#F1D998',
        },
        gris: {
          500: '#777A75',
          700: '#5F625E',
        },
        carbon: {
          500: '#303A3A',
        },
        feedback: {
          exito: '#2E7D5B',
          advertencia: '#7A5200',
          error: '#B3402F',
          'error-bg': '#FBE4E0',
        }
      },
      fontFamily: {
        serif: ['Fraunces', 'Playfair Display', 'Georgia', 'serif'],
        sans: ['DM Sans', 'Inter', '-apple-system', 'sans-serif'],
      },
      borderRadius: {
        sm: '8px',
        md: '12px',
        lg: '20px',
        xl: '28px',
        pill: '9999px',
      },
      boxShadow: {
        sm: '0 1px 3px rgba(36, 91, 89, 0.08)',
        md: '0 4px 16px rgba(36, 91, 89, 0.10)',
        lg: '0 12px 32px rgba(36, 91, 89, 0.12)',
      }
    },
  },
  plugins: [],
}
