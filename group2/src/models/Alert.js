const mongoose = require('mongoose');

const alertSchema = new mongoose.Schema({
  title: { type: String, required: true },
  description: { type: String, required: true },
  level: { type: String, enum: ['INFO', 'WATCH', 'WARNING', 'EMERGENCY'], default: 'WATCH' },
  sourceType: { type: String, enum: ['OFFICIAL_WARNING', 'WEATHERGPT_RISK_ASSESSMENT'], required: true },
  latitude: { type: Number, required: true },
  longitude: { type: Number, required: true },
  radiusKm: { type: Number, default: 25 },
  activeFrom: { type: Date, default: Date.now },
  expiresAt: { type: Date, required: true }
});

module.exports = mongoose.model('Alert', alertSchema);
