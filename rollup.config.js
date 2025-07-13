import { nodeResolve } from '@rollup/plugin-node-resolve';
import commonjs from '@rollup/plugin-commonjs';
import { terser } from '@rollup/plugin-terser';
import copy from 'rollup-plugin-copy';

export default {
  input: 'static/js/main.js',
  output: {
    file: 'static/js/bundle.min.js',
    format: 'iife',
    name: 'SapyynApp',
    sourcemap: true
  },
  plugins: [
    nodeResolve({
      browser: true,
      preferBuiltins: false
    }),
    commonjs(),
    copy({
      targets: [
        { 
          src: 'node_modules/bootstrap/dist/css/bootstrap.min.css', 
          dest: 'static/css/',
          rename: 'bootstrap.min.css'
        },
        { 
          src: 'node_modules/bootstrap/dist/js/bootstrap.bundle.min.js', 
          dest: 'static/js/',
          rename: 'bootstrap.bundle.min.js'
        },
        { 
          src: 'node_modules/bootstrap-icons/font/bootstrap-icons.css', 
          dest: 'static/css/',
          rename: 'bootstrap-icons.css'
        },
        { 
          src: 'node_modules/bootstrap-icons/font/fonts/*', 
          dest: 'static/css/fonts/'
        }
      ]
    }),
    terser({
      compress: {
        drop_console: true
      }
    })
  ],
  external: []
}
