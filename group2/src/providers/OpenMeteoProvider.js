const axios = require('axios');
const WeatherProvider = require('./WeatherProvider');
const { OPEN_METEO_BASE_URL } = require('../config/env');

class OpenMeteoProvider extends WeatherProvider {
  constructor() {
    super('Open-Meteo');
    this.baseUrl = OPEN_METEO_BASE_URL;
    this.archiveUrl = 'https://archive-api.open-meteo.com/v1/archive';
  }

  async getCurrentWeather(lat, lon) {
    try {
      const response = await axios.get(`${this.baseUrl}/forecast`, {
        params: {
          latitude: lat,
          longitude: lon,
          current_weather: true,
          hourly: 'precipitation_probability,precipitation,relative_humidity_2m,wind_speed_10m,weather_code,cape',
          timezone: 'auto'
        },
        timeout: 8000
      });

      const current = response.data.current_weather || {};
      const hourly = response.data.hourly || {};

      // Find the hourly index matching the current time instead of always using 0 (midnight)
      let currentIndex = 0;
      if (hourly.time && hourly.time.length > 0 && current.time) {
        const currentTimeStr = current.time; // e.g. "2026-09-28T14:00"
        const matchIdx = hourly.time.findIndex(t => t === currentTimeStr);
        if (matchIdx >= 0) {
          currentIndex = matchIdx;
        } else {
          // Fallback: use current hour of day
          const now = new Date();
          currentIndex = Math.min(now.getHours(), hourly.time.length - 1);
        }
      }

      const precipProb = hourly.precipitation_probability ? hourly.precipitation_probability[currentIndex] || 0 : 0;
      const precipitation = hourly.precipitation ? hourly.precipitation[currentIndex] || 0 : 0;
      const humidity = hourly.relative_humidity_2m ? hourly.relative_humidity_2m[currentIndex] || 50 : 50;
      const cape = hourly.cape ? hourly.cape[currentIndex] || 0 : 0;
      const weatherCode = current.weathercode || 0;

      // Detect thunderstorm/lightning code (codes 95, 96, 99 in WMO code list)
      const lightning = [95, 96, 99].includes(weatherCode);

      return {
        temperature: current.temperature || 25,
        wind_speed: current.windspeed || 10,
        rain_probability: precipProb,
        precipitation: precipitation,
        humidity: humidity,
        lightning: lightning,
        cape: cape,
        weather_code: weatherCode,
        weather_condition: this.mapWmoCodeToCondition(weatherCode),
        time: current.time || new Date().toISOString(),
        provider: this.name
      };
    } catch (err) {
      console.error(`[OpenMeteoProvider Error] ${err.message}`);
      throw new Error(`Weather Provider (${this.name}) failed: ${err.message}`);
    }
  }

  async getForecast(lat, lon, days = 7) {
    try {
      const response = await axios.get(`${this.baseUrl}/forecast`, {
        params: {
          latitude: lat,
          longitude: lon,
          forecast_days: days,
          hourly: 'temperature_2m,relative_humidity_2m,precipitation_probability,precipitation,wind_speed_10m,weather_code,cape',
          daily: 'temperature_2m_max,temperature_2m_min,precipitation_probability_max,precipitation_sum,wind_speed_10m_max',
          timezone: 'auto'
        },
        timeout: 8000
      });

      const data = response.data;
      const hourlyList = [];
      const times = data.hourly.time || [];

      for (let i = 0; i < times.length; i++) {
        const code = data.hourly.weather_code[i] || 0;
        hourlyList.push({
          time: times[i],
          temperature: data.hourly.temperature_2m[i],
          humidity: data.hourly.relative_humidity_2m ? data.hourly.relative_humidity_2m[i] : 50,
          rain_probability: data.hourly.precipitation_probability ? data.hourly.precipitation_probability[i] : 0,
          precipitation: data.hourly.precipitation ? data.hourly.precipitation[i] : 0,
          wind_speed: data.hourly.wind_speed_10m ? data.hourly.wind_speed_10m[i] : 0,
          lightning: [95, 96, 99].includes(code),
          cape: data.hourly.cape ? data.hourly.cape[i] : 0,
          weather_code: code,
          weather_condition: this.mapWmoCodeToCondition(code)
        });
      }

      const dailyList = [];
      const dailyTimes = data.daily.time || [];
      for (let j = 0; j < dailyTimes.length; j++) {
        dailyList.push({
          date: dailyTimes[j],
          max_temp: data.daily.temperature_2m_max[j],
          min_temp: data.daily.temperature_2m_min[j],
          max_rain_prob: data.daily.precipitation_probability_max ? data.daily.precipitation_probability_max[j] : 0,
          total_precipitation: data.daily.precipitation_sum ? data.daily.precipitation_sum[j] : 0,
          max_wind_speed: data.daily.wind_speed_10m_max ? data.daily.wind_speed_10m_max[j] : 0
        });
      }

      return {
        latitude: lat,
        longitude: lon,
        hourly: hourlyList,
        daily: dailyList,
        provider: this.name,
        forecast_agreement: "Single primary high-precision Open-Meteo deterministic forecast source available."
      };
    } catch (err) {
      console.error(`[OpenMeteoProvider Forecast Error] ${err.message}`);
      throw new Error(`Weather Forecast Provider (${this.name}) failed: ${err.message}`);
    }
  }

  async getHistory(lat, lon, startDate, endDate) {
    try {
      const response = await axios.get(this.archiveUrl, {
        params: {
          latitude: lat,
          longitude: lon,
          start_date: startDate,
          end_date: endDate,
          hourly: 'temperature_2m,precipitation,wind_speed_10m'
        },
        timeout: 8000
      });

      return {
        latitude: lat,
        longitude: lon,
        startDate,
        endDate,
        history: response.data.hourly || {},
        provider: this.name
      };
    } catch (err) {
      console.error(`[OpenMeteoProvider History Error] ${err.message}`);
      // Return gracefully structured empty historical response if date range issue
      return {
        latitude: lat,
        longitude: lon,
        startDate,
        endDate,
        history: { time: [], temperature_2m: [], precipitation: [] },
        provider: this.name,
        error: err.message
      };
    }
  }

  mapWmoCodeToCondition(code) {
    const wmoMap = {
      0: 'Clear sky',
      1: 'Mainly clear',
      2: 'Partly cloudy',
      3: 'Overcast',
      45: 'Fog',
      48: 'Depositing rime fog',
      51: 'Light drizzle',
      53: 'Moderate drizzle',
      55: 'Dense drizzle',
      61: 'Slight rain',
      63: 'Moderate rain',
      65: 'Heavy rain',
      71: 'Slight snow',
      73: 'Moderate snow',
      75: 'Heavy snow',
      80: 'Slight rain showers',
      81: 'Moderate rain showers',
      82: 'Violent rain showers',
      95: 'Thunderstorm',
      96: 'Thunderstorm with slight hail',
      99: 'Thunderstorm with heavy hail'
    };
    return wmoMap[code] || 'Cloudy';
  }
}

module.exports = OpenMeteoProvider;
