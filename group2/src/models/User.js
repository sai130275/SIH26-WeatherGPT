const mongoose = require('mongoose');

const userSchema = new mongoose.Schema({
  name: { type: String, required: true },
  email: { type: String, required: true, unique: true },
  password: { type: String, required: true },
  language: { type: String, default: 'en' },
  preferredActivity: { type: String, default: 'travel' },
  savedLocations: [{
    name: String,
    latitude: Number,
    longitude: Number
  }],
  createdAt: { type: Date, default: Date.now }
});

module.exports = mongoose.model('User', userSchema);
