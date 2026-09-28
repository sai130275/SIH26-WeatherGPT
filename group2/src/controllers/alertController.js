const { getActiveAlertsForLocation } = require('../services/alertService');
const { sendSuccess, sendError } = require('../utils/responseFormatter');

const getAlerts = async (req, res, next) => {
  try {
    const lat = parseFloat(req.query.lat) || 17.9689;
    const lon = parseFloat(req.query.lon) || 79.5941;
    const radius = parseFloat(req.query.radius) || 50;

    const alerts = await getActiveAlertsForLocation(lat, lon, radius);
    return sendSuccess(res, { alerts }, 'Alerts fetched successfully');
  } catch (err) {
    next(err);
  }
};

const checkAlerts = async (req, res, next) => {
  try {
    const { latitude, longitude, radius } = req.body;
    const lat = parseFloat(latitude) || 17.9689;
    const lon = parseFloat(longitude) || 79.5941;

    const alerts = await getActiveAlertsForLocation(lat, lon, radius || 50);
    return sendSuccess(res, {
      latitude: lat,
      longitude: lon,
      activeAlertsCount: alerts.length,
      alerts
    }, 'Location alert check completed');
  } catch (err) {
    next(err);
  }
};

module.exports = {
  getAlerts,
  checkAlerts
};
