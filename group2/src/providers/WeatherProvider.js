/**
 * Abstract WeatherProvider Base Class
 * Standardizes weather data fetching interface across current, forecast, and historical records.
 */
class WeatherProvider {
  constructor(name) {
    if (new.target === WeatherProvider) {
      throw new TypeError("Cannot instantiate abstract class WeatherProvider directly.");
    }
    this.name = name;
  }

  async getCurrentWeather(lat, lon) {
    throw new Error("Method 'getCurrentWeather()' must be implemented.");
  }

  async getForecast(lat, lon, days = 7) {
    throw new Error("Method 'getForecast()' must be implemented.");
  }

  async getHistory(lat, lon, startDate, endDate) {
    throw new Error("Method 'getHistory()' must be implemented.");
  }
}

module.exports = WeatherProvider;
