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
    outDir: 'static/dist',
    emptyOutDir: true,
    lib: {
      entry: path.resolve(__dirname, 'vue/index.js'),
      name: 'MapEditorVue',
      formats: ['umd'],
      fileName: () => 'index.umd.min.js',
      cssFileName: 'index',
    },
    rollupOptions: {
      output: {
        assetFileNames: (assetInfo) => {
          if (assetInfo.name && assetInfo.name.endsWith('.css')) {
            return 'index.css';
          }
          return 'assets/[name]-[hash][extname]';
        },
      },
    },
  },
});
