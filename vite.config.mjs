import {defineConfig} from 'vite';
import vue from '@vitejs/plugin-vue';
import path from 'path';
import {fileURLToPath} from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './vue'),
      '@static': path.resolve(__dirname, './static'),
    },
    extensions: ['.mjs', '.js', '.ts', '.jsx', '.tsx', '.json', '.vue'],
  },
  server: {
    host: '127.0.0.1',
    port: 9111,
    strictPort: true,
  },
  build: {
    outDir: 'static/dist-vite',
    emptyOutDir: true,
    rollupOptions: {
      input: path.resolve(__dirname, 'vue/index.js'),
      output: {
        entryFileNames: 'index.js',
        chunkFileNames: 'assets/[name]-[hash].js',
        assetFileNames: 'assets/[name]-[hash][extname]',
      },
    },
  },
});
