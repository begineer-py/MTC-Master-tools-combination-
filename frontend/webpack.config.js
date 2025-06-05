const path = require('path');

module.exports = {
  entry: {
    bundle: '../static/js/attack.js',
    result: '../static/js/result.js'
  },
  output: {
    path: path.resolve(__dirname, '../static/js/dist'),
    filename: '[name].js',
  },
  module: {
    rules: [
      {
        test: /\.(js|jsx)$/,
        exclude: /node_modules/,
        use: {
          loader: 'babel-loader',

          
          options: {
            presets: ['@babel/preset-env', '@babel/preset-react']
          }
        }
      },
      {
        test: /\.css$/,
        use: ['style-loader', 'css-loader']
      }
    ]
  },
  resolve: {
    extensions: ['.js', '.jsx'],
    modules: [
      path.resolve(__dirname, 'node_modules'),
      'node_modules'
    ]
  },
  devtool: 'source-map'
}; 