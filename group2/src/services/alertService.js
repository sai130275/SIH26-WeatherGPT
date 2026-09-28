const mongoose = require('mongoose');
const Alert = require('../models/Alert');

/**
 * Alert Service
 * Geofencing distance calculation & active weather alert retrieval.
 */

const calculateDistanceKm = (lat1, lon1, lat2, lon2) => {
  const R = 6371; // Earth radius in km
  const dLat = (lat2 - lat1) * (Math.PI / 180);
  const dLon = (lon2 - lon1) * (Math.PI / 180);
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(lat1 * (Math.PI / 180)) * Math.cos(lat2 * (Math.PI / 180)) *
    Math.sin(dLon / 2) * Math.sin(dLon / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c;
};

const getActiveAlertsForLocation = async (lat, lon, radius = 50) => {
  try {
    if (mongoose.connection.readyState !== 1) {
      throw new Error("MongoDB connection not active");
    }
    const activeAlerts = await Alert.find({
      expiresAt: { $gt: new Date() }
    }).maxTimeMS(500).lean();

    const matchedAlerts = activeAlerts.filter(alert => {
      const dist = calculateDistanceKm(lat, lon, alert.latitude, alert.longitude);
      return dist <= (alert.radiusKm || radius);
    });

    return matchedAlerts;
  } catch (err) {
    // Return empty array when DB is offline as we don't fabricate alerts
    console.warn('MongoDB connection error, returning empty active alerts:', err.message);
    return [];
  }
};

module.exports = {
  calculateDistanceKm,
  getActiveAlertsForLocation
};
