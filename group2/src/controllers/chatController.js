const axios = require('axios');
const { weatherProvider } = require('../providers');
const { sendSuccess, sendError } = require('../utils/responseFormatter');
const { GROUP3_URL } = require('../config/env');

const handleChat = async (req, res, next) => {
  try {
    const { message, latitude, longitude, conversation_id } = req.body;

    if (!message) {
      return sendError(res, 'VALIDATION_ERROR', 'Message is required.', 400);
    }

    const lat = parseFloat(latitude) || 17.9689;
    const lon = parseFloat(longitude) || 79.5941;

    // STEP 1: Weather Data Retrieval
    // Pre-fetching telemetry at the gateway decouples the AI intelligence service
    // from external meteorological network calls and ensures canonical data grounding.
    const currentWeather = await weatherProvider.getCurrentWeather(lat, lon);

    const weatherData = {
      location: "Unknown",
      latitude: lat,
      longitude: lon,
      timestamp: new Date().toISOString(),
      temperature: currentWeather.temperature,
      humidity: currentWeather.humidity,
      rainfall: currentWeather.precipitation || 0,
      wind_speed: currentWeather.wind_speed || 0,
      visibility: currentWeather.visibility,
      pressure: currentWeather.pressure
    };

    // STEP 2: Call Group 3 /chat
    // Forward structured payload to Group 3. A 60-second timeout accommodates
    // initial cold-start wakeups on free cloud tiers and LLM inference generation.
    const payload = {
      message,
      location: { latitude: lat, longitude: lon },
      conversation_id: conversation_id || `conv-${Date.now()}`,
      weather_data: weatherData
    };

    const response = await axios.post(`${GROUP3_URL}/chat`, payload, {
      timeout: 60000
    });

    // STEP 3: Return Structured Response
    return sendSuccess(res, response.data);
  } catch (err) {
    console.error(`[ChatController Error] Failed to proxy to Group 3 /chat: ${err.message}`);
    next(err);
  }
};

module.exports = {
  handleChat
};
