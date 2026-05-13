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
        // Base palette
        paper: '#FAFAF8',
        ink: '#1A1A1A',
        stone: {
          50: '#FAFAF8',
          100: '#F5F5F3',
          200: '#E8E8E5',
          300: '#D1D1CC',
          400: '#A3A39E',
          500: '#75756F',
          600: '#5C5C56',
          700: '#434340',
          800: '#2B2B28',
          900: '#1A1A18',
          950: '#0F0F0E',
        },
        // Sport-themed modern colors
        sport: {
          blue: {
            50: '#EFF6FF',
            100: '#DBEAFE',
            200: '#BFDBFE',
            300: '#93C5FD',
            400: '#60A5FA',
            500: '#3B82F6',
            600: '#2563EB',
            700: '#1D4ED8',
            800: '#1E40AF',
            900: '#1E3A8A',
          },
          gold: {
            50: '#FEFCE8',
            100: '#FEF9C3',
            200: '#FEF08A',
            300: '#FDE047',
            400: '#FACC15',
            500: '#EAB308',
            600: '#CA8A04',
            700: '#A16207',
            800: '#854D0E',
            900: '#713F12',
          },
        },
        // Semantic colors (enhanced)
        critical: {
          light: '#DC2626',
          dark: '#EF4444',
          50: '#FEF2F2',
          500: '#EF4444',
          600: '#DC2626',
          700: '#B91C1C',
        },
        warning: {
          light: '#EA580C',
          dark: '#F97316',
          50: '#FFF7ED',
          500: '#F97316',
          600: '#EA580C',
          700: '#C2410C',
        },
        info: {
          light: '#2563EB',
          dark: '#3B82F6',
          50: '#EFF6FF',
          500: '#3B82F6',
          600: '#2563EB',
          700: '#1D4ED8',
        },
        good: {
          light: '#16A34A',
          dark: '#22C55E',
          50: '#F0FDF4',
          500: '#22C55E',
          600: '#16A34A',
          700: '#15803D',
        },
        accent: {
          light: '#9333EA',
          dark: '#A855F7',
          50: '#FAF5FF',
          500: '#A855F7',
          600: '#9333EA',
          700: '#7E22CE',
        },
      },
      fontFamily: {
        headline: ['DM Serif Display', 'serif'],
        body: ['IBM Plex Serif', 'serif'],
        sans: ['Inter', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      backgroundImage: {
        'gradient-sport': 'linear-gradient(135deg, #1E3A8A 0%, #DC2626 100%)',
        'gradient-sport-subtle': 'linear-gradient(135deg, #3B82F6 0%, #EF4444 100%)',
        'gradient-gold': 'linear-gradient(135deg, #EAB308 0%, #F97316 100%)',
        'gradient-blue': 'linear-gradient(135deg, #2563EB 0%, #7C3AED 100%)',
        'gradient-success': 'linear-gradient(135deg, #16A34A 0%, #22C55E 100%)',
      },
      boxShadow: {
        'glass': '0 8px 32px 0 rgba(31, 38, 135, 0.15)',
        'glass-lg': '0 16px 48px 0 rgba(31, 38, 135, 0.2)',
        'sport': '0 10px 40px -10px rgba(30, 58, 138, 0.4)',
        'sport-lg': '0 20px 60px -15px rgba(30, 58, 138, 0.5)',
      },
      backdropBlur: {
        xs: '2px',
      },
      animation: {
        'fade-in': 'fadeIn 0.3s ease-in-out',
        'slide-up': 'slideUp 0.3s ease-out',
        'scale-in': 'scaleIn 0.2s ease-out',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        scaleIn: {
          '0%': { transform: 'scale(0.95)', opacity: '0' },
          '100%': { transform: 'scale(1)', opacity: '1' },
        },
      },
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
  ],
}
