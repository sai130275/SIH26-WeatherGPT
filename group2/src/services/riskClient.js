const axios = require('axios');
const { GROUP3_URL } = require('../config/env');

const calculateRisk = async (weatherData) => {
  const payload = {
    location: weatherData.location || "Unknown",
    latitude: weatherData.latitude || 0,
    longitude: weatherData.longitude || 0,
    timestamp: weatherData.timestamp || new Date().toISOString(),
    temperature: weatherData.temperature,
    humidity: weatherData.humidity,
    rainfall: weatherData.precipitation || 0, // mapping precipitation to rainfall
    wind_speed: weatherData.wind_speed || 0,
    visibility: weatherData.visibility,
    pressure: weatherData.pressure
  };

  try {
    const response = await axios.post(`${GROUP3_URL}/risk`, payload, {
      timeout: 5000
    });
    return response.data;
  } catch (err) {
    console.error(`[RiskClient Error] Group 3 /risk unreachable: ${err.message}`);
    throw err;
  }
};

module.exports = {
  calculateRisk
};
