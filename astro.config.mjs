import { defineConfig } from 'astro/config';
import tailwindcss from '@tailwindcss/vite';
import icon from 'astro-icon';

export default defineConfig({
  site: 'https://netmediatop.com',
  integrations: [icon()],
  vite: {
    plugins: [tailwindcss()],
  },
});
