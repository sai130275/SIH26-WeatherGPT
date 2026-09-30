const mongoose = require('mongoose');

// Connects to MongoDB with a short 500ms discovery timeout to prevent startup stalls;
// gracefully activates an in-memory mock store if MongoDB is offline.
const connectDB = async () => {
  try {
    const uri = process.env.MONGODB_URI || 'mongodb://localhost:27017/weathergpt';
    const conn = await mongoose.connect(uri, {
      serverSelectionTimeoutMS: 500
    });
    console.log(`[MongoDB] Connected: ${conn.connection.host}`);
    return conn;
  } catch (err) {
    console.warn(`[MongoDB Warning] Could not connect to MongoDB at ${process.env.MONGODB_URI}: ${err.message}. Operating in memory-mock mode for database persistence.`);
    return null;
  }
};

module.exports = connectDB;
