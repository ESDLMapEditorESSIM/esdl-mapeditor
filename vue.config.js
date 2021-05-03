const webpack = require("webpack");

module.exports = {
  configureWebpack: (config) => {
    if (process.env.NODE_ENV === 'development') {
      config.devtool = 'eval-source-map';
    }
    if (process.env.NODE_ENV === 'production') {
      // config.optimization = {
      //   splitChunks: {
      //       minSize: 10000,
      //       maxSize: 250000,
      //   }
      // }
    }
    config.plugins = [
      ...config.plugins,
      new webpack.ContextReplacementPlugin(/moment[\\\/]locale$/, /^\.\/(en|nl)$/),
    ];
  },
};
