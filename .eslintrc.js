module.exports = {
  root: true,
  env: {
    node: true
  },
  'extends': [
    'plugin:vue/vue3-recommended',
    'eslint:recommended'
  ],
  parserOptions: {
    parser: 'babel-eslint'
  },
  rules: {
    'vue/singline-html-element': 'off',
    'vue/singleline-html-element-content-newline': 'off',
    'vue/max-attributes-per-line': 'off',
    'vue/no-unused-components': 'warn',
    'no-unused-vars': 'warn',
    'no-console': process.env.NODE_ENV === 'production' ? 'warn' : 'off',
    'no-debugger': process.env.NODE_ENV === 'production' ? 'warn' : 'off'
  }
}
