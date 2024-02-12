import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'
import {compression} from "vite-plugin-compression2";

// https://vitejs.dev/config/
export default defineConfig({
  build: {
    lib: {
      // Could also be a dictionary or array of multiple entry points
      entry: resolve(__dirname, 'vue/index.js'),
      name: 'EsdlMapEditor',
      // the proper extensions will be added
      fileName: 'esdl-mapeditor',
    },
    sourcemap: true
  },
  plugins: [vue(), compression()],
  resolve: {
    alias: {
      "@": resolve(__dirname, "./vue"),
    },
  },
  define: {
    'process.env': {}
  }
})
