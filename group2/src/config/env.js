/**
 * Centralized Environment Configuration
 * Validates required environment variables at startup and provides a single source of truth.
 */
require('dotenv').config();

const JWT_SECRET = process.env.JWT_SECRET;
if (!JWT_SECRET) {
  throw new Error('FATAL: JWT_SECRET environment variable is required. Set it in your .env file.');
}

module.exports = {
  JWT_SECRET,
  PORT: parseInt(process.env.PORT, 10) || 5000,
  NODE_ENV: process.env.NODE_ENV || 'development',
  MONGODB_URI: process.env.MONGODB_URI || 'mongodb://localhost:27017/weathergpt',
  REDIS_URL: process.env.REDIS_URL || 'redis://localhost:6379',
  // Strips trailing slashes to prevent double-slash route failures (e.g. //chat 404s) on FastAPI
  GROUP3_URL: (process.env.GROUP3_URL || 'http://localhost:8000').trim().replace(/\/+$/, ''),
  OPEN_METEO_BASE_URL: process.env.OPEN_METEO_BASE_URL || 'https://api.open-meteo.com/v1',
  GEMINI_API_KEY: (process.env.GEMINI_API_KEY || '').trim() || null,
  OPENAI_API_KEY: (process.env.OPENAI_API_KEY || '').trim() || null,
  GEMINI_MODEL: process.env.GEMINI_MODEL || 'gemini-2.0-flash',
  OPENAI_MODEL: process.env.OPENAI_MODEL || 'gpt-4o-mini',
};
