const { weatherProvider } = require('../providers');
const { getCache, setCache } = require('../config/redis');
const { sendSuccess, sendError } = require('../utils/responseFormatter');

const getCurrentWeather = async (req, res, next) => {
  try {
    const lat = parseFloat(req.query.lat) || 17.9689;
    const lon = parseFloat(req.query.lon) || 79.5941;
    const cacheKey = `weather:${lat.toFixed(3)}:${lon.toFixed(3)}`;

    const cachedData = await getCache(cacheKey);
    if (cachedData) {
      return sendSuccess(res, cachedData, 'Current weather fetched from cache');
    }

    const weatherData = await weatherProvider.getCurrentWeather(lat, lon);
    await setCache(cacheKey, weatherData, 900); // 15 min TTL

    return sendSuccess(res, weatherData, 'Current weather fetched');
  } catch (err) {
    next(err);
  }
};

const getForecast = async (req, res, next) => {
  try {
    const lat = parseFloat(req.query.lat) || 17.9689;
    const lon = parseFloat(req.query.lon) || 79.5941;
    const days = parseInt(req.query.days) || 7;
    const cacheKey = `forecast:${lat.toFixed(3)}:${lon.toFixed(3)}:${days}`;

    const cachedData = await getCache(cacheKey);
    if (cachedData) {
      return sendSuccess(res, cachedData, 'Weather forecast fetched from cache');
    }

    const forecastData = await weatherProvider.getForecast(lat, lon, days);
    await setCache(cacheKey, forecastData, 1800); // 30 min TTL

    return sendSuccess(res, forecastData, 'Weather forecast fetched');
  } catch (err) {
    next(err);
  }
};

const getHistory = async (req, res, next) => {
  try {
    const lat = parseFloat(req.query.lat) || 17.9689;
    const lon = parseFloat(req.query.lon) || 79.5941;
    const startDate = req.query.start_date || '2026-09-01';
    const endDate = req.query.end_date || '2026-09-25';

    const historyData = await weatherProvider.getHistory(lat, lon, startDate, endDate);
    return sendSuccess(res, historyData, 'Historical weather data fetched');
  } catch (err) {
    next(err);
  }
};

module.exports = {
  getCurrentWeather,
  getForecast,
  getHistory
};
