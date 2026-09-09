import { defineConfig } from 'astro/config';
import cloudflare from '@astrojs/cloudflare';

export default defineConfig({
  output: 'static', // <-- Tambahkan baris ini
  adapter: cloudflare(),
});