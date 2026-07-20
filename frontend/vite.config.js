import { resolve } from 'path';
import { defineConfig } from 'vite';

export default defineConfig({
  build: {
    rollupOptions: {
      input: {
        main: resolve(__dirname, 'index.html'),
        predict: resolve(__dirname, 'predict.html'),
        evaluation: resolve(__dirname, 'evaluation.html'),
      },
    },
  },
});
