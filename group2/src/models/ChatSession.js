const mongoose = require('mongoose');

const chatSessionSchema = new mongoose.Schema({
  userId: { type: String, required: true },
  language: { type: String, default: 'en' },
  lastActivity: { type: String, default: 'general' },
  createdAt: { type: Date, default: Date.now },
  updatedAt: { type: Date, default: Date.now }
});

const chatMessageSchema = new mongoose.Schema({
  sessionId: { type: String, required: true },
  role: { type: String, enum: ['user', 'assistant'], required: true },
  message: { type: String, required: true },
  structuredData: { type: Object },
  createdAt: { type: Date, default: Date.now }
});

module.exports = {
  ChatSession: mongoose.model('ChatSession', chatSessionSchema),
  ChatMessage: mongoose.model('ChatMessage', chatMessageSchema)
};
