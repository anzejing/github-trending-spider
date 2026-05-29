module.exports = {
  publicPath: '/ai/',
  devServer: {
    host: 'localhost',
    port: 8080,
    allowedHosts: 'all',
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  }
};
