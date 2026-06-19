# Configuración de TailwindCSS para BASILE Frontend

> **Estado**: Documentado, no instalado aún.
> **Cuándo aplicar**: Cuando se inicie el trabajo de UI/UX en cualquier change frontend.

---

## Por qué TailwindCSS

El frontend actual usa `className` en componentes pero **no tiene ningún sistema de estilos** (no CSS files, no styled-components, no MUI). Tailwind es la elección natural porque:

- Zero-runtime (purge automático en build)
- TypeScript-friendly (autocompletado de clases)
- Ya usamos Vite (plugin tailwindcss/vite es nativo)
- Escalable para equipo: no necesitás inventar nombres de clases
- Responsive, dark mode, y variantes built-in

---

## Instalación (pasos a ejecutar)

```bash
cd frontend
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

---

## Archivos de configuración

### 1. `tailwind.config.js`

```js
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Paleta BASILE — carnicería, carne, profesional
        primary: {
          50: '#fef2f2',
          100: '#fee2e2',
          200: '#fecaca',
          300: '#fca5a5',
          400: '#f87171',
          500: '#ef4444', // Rojo carnicería
          600: '#dc2626',
          700: '#b91c1c',
          800: '#991b1b',
          900: '#7f1d1d',
        },
        meat: {
          50: '#fdf8f6',
          100: '#f2e8e5',
          200: '#eaddd7',
          300: '#e0cec7',
          400: '#d2bab0',
          500: '#a0522d', // Marrón carne
          600: '#8b4513',
          700: '#cd853f',
        },
        surface: {
          50: '#fafafa',
          100: '#f5f5f5',
          200: '#e5e5e5',
          300: '#d4d4d4',
          400: '#a3a3a3',
          500: '#737373',
          600: '#525252',
          700: '#404040',
          800: '#262626',
          900: '#171717',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      boxShadow: {
        'card': '0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24)',
        'card-hover': '0 4px 6px rgba(0,0,0,0.15), 0 2px 4px rgba(0,0,0,0.12)',
      },
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/typography'),
  ],
}
```

### 2. `src/index.css` (nuevo archivo)

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  html {
    font-family: theme('fontFamily.sans');
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
  }

  body {
    @apply bg-surface-50 text-surface-900;
  }

  /* Tablas por defecto estilo BASILE */
  table {
    @apply w-full text-sm text-left;
  }

  th {
    @apply px-4 py-3 font-semibold text-surface-600 bg-surface-100 uppercase tracking-wider text-xs;
  }

  td {
    @apply px-4 py-3 border-b border-surface-200;
  }

  tr:hover td {
    @apply bg-surface-50;
  }

  /* Inputs por defecto */
  input, select, textarea {
    @apply block w-full rounded-md border-surface-300 shadow-sm 
           focus:border-primary-500 focus:ring-primary-500 
           sm:text-sm px-3 py-2;
  }

  /* Botones base */
  button {
    @apply inline-flex items-center justify-center px-4 py-2 
           border border-transparent text-sm font-medium rounded-md 
           shadow-sm focus:outline-none focus:ring-2 focus:ring-offset-2;
  }
}

@layer components {
  .btn-primary {
    @apply bg-primary-600 text-white hover:bg-primary-700 
           focus:ring-primary-500;
  }

  .btn-secondary {
    @apply bg-white text-surface-700 border-surface-300 hover:bg-surface-50 
           focus:ring-primary-500;
  }

  .btn-danger {
    @apply bg-red-600 text-white hover:bg-red-700 
           focus:ring-red-500;
  }

  .card {
    @apply bg-white rounded-lg shadow-card p-6;
  }

  .page-header {
    @apply mb-6 pb-4 border-b border-surface-200;
  }

  .page-title {
    @apply text-2xl font-bold text-surface-900;
  }

  .form-group {
    @apply mb-4;
  }

  .form-label {
    @apply block text-sm font-medium text-surface-700 mb-1;
  }

  .form-error {
    @apply mt-1 text-sm text-red-600;
  }

  .badge {
    @apply inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium;
  }

  .badge-green {
    @apply bg-green-100 text-green-800;
  }

  .badge-red {
    @apply bg-red-100 text-red-800;
  }

  .badge-yellow {
    @apply bg-yellow-100 text-yellow-800;
  }

  .badge-gray {
    @apply bg-surface-100 text-surface-800;
  }
}
```

### 3. `src/main.tsx` (modificar)

Agregar import del CSS:

```tsx
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'  // <-- AGREGAR
import App from './App'

// ... resto igual
```

### 4. `index.html` (agregar fuente Inter)

```html
<!doctype html>
<html lang="es">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <title>BASILE - Gestión de Carnicerías</title>
  </head>
  <!-- ... -->
</html>
```

---

## Dependencias adicionales a instalar

```bash
npm install -D @tailwindcss/forms @tailwindcss/typography
```

---

## Migración progresiva de componentes existentes

No hace falta reescribir todo de una. La estrategia es:

1. **Páginas nuevas** (ej. panel de superadmin): usar Tailwind directamente
2. **Páginas existentes**: reemplazar `className="producto-grid"` por clases de Tailwind cuando se toque ese archivo
3. **Componentes compartidos** (ProductoGrid, ProductoForm, etc.): migrar primero porque se reutilizan

### Ejemplo de migración: `ProductoGrid.tsx`

**Antes (actual):**
```tsx
<div className="producto-grid">
  <div className="filters">
    <input placeholder="Buscar..." />
  </div>
  <table>...</table>
</div>
```

**Después (con Tailwind):**
```tsx
<div className="space-y-4">
  <div className="flex gap-3">
    <input 
      placeholder="Buscar por PLU o nombre..."
      className="flex-1"
    />
    <select className="w-48">...</select>
  </div>
  <div className="card overflow-hidden">
    <table>...</table>
  </div>
</div>
```

---

## Convenciones para el equipo

1. **No inventar clases**: usar utilidades de Tailwind, no crear `.css` nuevos
2. **Componentes con @layer**: solo para patrones que se repiten 3+ veces (btn-primary, card, badge)
3. **Responsive mobile-first**: `sm:`, `md:`, `lg:` para breakpoints
4. **Colores BASILE**: usar la paleta custom (`primary-500`, `meat-500`, `surface-*`), no colores crudos de Tailwind
5. **Dark mode**: opcional, se puede agregar después con `darkMode: 'class'` en config

---

## Checklist de instalación

- [ ] `npm install -D tailwindcss postcss autoprefixer @tailwindcss/forms @tailwindcss/typography`
- [ ] `npx tailwindcss init -p`
- [ ] Copiar `tailwind.config.js` (arriba)
- [ ] Crear `src/index.css` (arriba)
- [ ] Modificar `src/main.tsx` para importar `index.css`
- [ ] Agregar fuente Inter en `index.html`
- [ ] Verificar build: `npm run build` debe pasar sin errores
- [ ] Verificar dev: `npm run dev` debe mostrar estilos aplicados

---

## Referencias

- [TailwindCSS docs](https://tailwindcss.com/docs)
- [Tailwind Forms plugin](https://github.com/tailwindlabs/tailwindcss-forms)
- [Inter font](https://fonts.google.com/specimen/Inter)
