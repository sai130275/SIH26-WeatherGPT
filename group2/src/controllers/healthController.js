const { sendSuccess } = require('../utils/responseFormatter');

const getHealthStatus = (req, res) => {
  return sendSuccess(res, {
    status: 'ONLINE',
    service: 'WeatherGPT Node.js Orchestrator',
    timestamp: new Date().toISOString(),
    uptime: process.uptime()
  });
};

module.exports = {
  getHealthStatus
};
