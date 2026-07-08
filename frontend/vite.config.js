import { defineConfig } from 'vite';

export default defineConfig({
  // The correct base is /terrain-view/ for generating correct URLs in dev and prod
  // when Nginx does NOT strip the path (proxy_pass without trailing slash).
  // But wait! If Nginx proxies `/terrain-view/` to `http://xx-xx:7006/` WITH the trailing slash,
  // Vite dev server receives `/`.
  // To make Vite output relative paths for @vite/client we need a plugin to rewrite the HTML output in dev.
  base: './',
  server: {
    host: '0.0.0.0',
    port: 7000,
    allowedHosts: true,
  },
  plugins: [
    {
      name: 'replace-vite-client-path',
      transformIndexHtml(html) {
        return html.replace(/src="\/@vite\/client"/g, 'src="./@vite/client"');
      }
    }
  ]
});
