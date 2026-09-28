const OpenMeteoProvider = require('./OpenMeteoProvider');

// Weather Provider Singleton
const defaultWeatherProvider = new OpenMeteoProvider();

module.exports = {
  weatherProvider: defaultWeatherProvider
};
