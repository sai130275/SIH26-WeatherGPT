const axios = require('axios');
const { GROUP3_URL } = require('../config/env');

const fetchAdvisory = async (weatherData, riskData) => {
  const payload = {
    weather: {
      location: weatherData.location || "Unknown",
      latitude: weatherData.latitude || 0,
      longitude: weatherData.longitude || 0,
      timestamp: weatherData.timestamp || new Date().toISOString(),
      temperature: weatherData.temperature,
      humidity: weatherData.humidity,
      rainfall: weatherData.precipitation || 0,
      wind_speed: weatherData.wind_speed || 0,
      visibility: weatherData.visibility,
      pressure: weatherData.pressure
    },
    risk: riskData
  };

  try {
    const response = await axios.post(`${GROUP3_URL}/advisory`, payload, {
      timeout: 5000
    });
    return response.data; // { impacts, advisories, overall_risk_level, ... }
  } catch (err) {
    console.error(`[AdvisoryClient Error] Group 3 /advisory unreachable: ${err.message}`);
    throw err;
  }
};

module.exports = {
  fetchAdvisory
};
