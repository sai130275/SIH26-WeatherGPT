const mongoose = require('mongoose');

const locationSchema = new mongoose.Schema({
  name: { type: String, required: true },
  district: String,
  state: String,
  country: { type: String, default: 'India' },
  latitude: { type: Number, required: true },
  longitude: { type: Number, required: true },
  cachedAt: { type: Date, default: Date.now }
});

module.exports = mongoose.model('Location', locationSchema);
