const { generateRiskGeoJson } = require('../services/mapService');
const { sendSuccess } = require('../utils/responseFormatter');

const getRiskMap = async (req, res, next) => {
  try {
    const lat = parseFloat(req.query.lat) || 17.9689;
    const lon = parseFloat(req.query.lon) || 79.5941;

    const geoJson = await generateRiskGeoJson(lat, lon);
    return res.status(200).json(geoJson);
  } catch (err) {
    next(err);
  }
};

module.exports = {
  getRiskMap
};
