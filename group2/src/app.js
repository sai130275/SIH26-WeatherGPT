const http = require('http');
const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const rateLimit = require('express-rate-limit');
const morgan = require('morgan');
const { Server } = require('socket.io');
const mongoose = require('mongoose');
const env = require('./config/env');

const connectDB = require('./config/db');
const errorHandler = require('./middleware/errorHandler');

// Route imports
const authRoutes = require('./routes/authRoutes');
const weatherRoutes = require('./routes/weatherRoutes');
const chatRoutes = require('./routes/chatRoutes');
const alertRoutes = require('./routes/alertRoutes');
const mapRoutes = require('./routes/mapRoutes');
const healthRoutes = require('./routes/healthRoutes');

const app = express();
const server = http.createServer(app);

// Allowed origins (restrict in production)
const allowedOrigins = env.NODE_ENV === 'production'
  ? (process.env.ALLOWED_ORIGINS || '').split(',').filter(Boolean)
  : ['*'];

// Socket.IO setup
const io = new Server(server, {
  cors: {
    origin: env.NODE_ENV === 'production' ? allowedOrigins : '*',
    methods: ['GET', 'POST']
  }
});

io.on('connection', (socket) => {
  console.log(`[Socket.IO] Client connected: ${socket.id}`);

  socket.on('join_location', (data) => {
    if (data && data.location) {
      // Sanitize location to prevent room injection
      const sanitized = String(data.location).replace(/[^a-zA-Z0-9_.\-]/g, '').slice(0, 100);
      if (sanitized.length > 0) {
        socket.join(`location_${sanitized}`);
        console.log(`[Socket.IO] Client ${socket.id} joined location_${sanitized}`);
      }
    }
  });

  socket.on('disconnect', () => {
    console.log(`[Socket.IO] Client disconnected: ${socket.id}`);
  });
});

// Attach socket server to app context
app.set('io', io);

// Security & Middleware
app.use(helmet());
app.use(cors({
  origin: env.NODE_ENV === 'production' ? allowedOrigins : '*'
}));
app.use(express.json({ limit: '10kb' }));

// HTTP request logging
if (env.NODE_ENV !== 'test') {
  app.use(morgan('combined'));
}

// Global rate limiter
const globalLimiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 200,
  message: { success: false, error: { code: 'TOO_MANY_REQUESTS', message: 'Rate limit exceeded. Try again later.' } }
});
app.use(globalLimiter);

// Stricter rate limiter for LLM/Chat endpoints
const chatLimiter = rateLimit({
  windowMs: 60 * 1000,
  max: 10,
  message: { success: false, error: { code: 'TOO_MANY_REQUESTS', message: 'Chat rate limit exceeded. Please wait before sending another query.' } }
});

// API Routes
app.use('/api/auth', authRoutes);
app.use('/api/weather', weatherRoutes);
app.use('/api/chat', chatLimiter, chatRoutes);
app.use('/api/alerts', alertRoutes);
app.use('/api/risk', mapRoutes);
app.use('/api/health', healthRoutes);

// Root route
app.get('/', (req, res) => {
  res.json({
    name: 'WeatherGPT Backend Service',
    version: '1.0.0',
    hackathon: 'Smart India Hackathon 2026',
    status: 'ONLINE',
    docs: '/api/health'
  });
});

// Centralized error handler
app.use(errorHandler);

const PORT = env.PORT;

const startServer = async () => {
  await connectDB();
  server.listen(PORT, () => {
    console.log(`===================================================`);
    console.log(`[WeatherGPT Backend] Server running on port ${PORT}`);
    console.log(`[API Base] http://localhost:${PORT}/api`);
    console.log(`[Environment] ${env.NODE_ENV}`);
    console.log(`===================================================`);
  });
};

// Graceful shutdown
const shutdown = async (signal) => {
  console.log(`\n[Shutdown] Received ${signal}. Shutting down gracefully...`);
  server.close(async () => {
    try {
      if (mongoose.connection.readyState === 1) {
        await mongoose.connection.close();
        console.log('[Shutdown] MongoDB connection closed.');
      }
    } catch (e) {
      console.error('[Shutdown] Error closing MongoDB:', e.message);
    }
    console.log('[Shutdown] Process exiting.');
    process.exit(0);
  });

  // Force exit if graceful shutdown takes too long
  setTimeout(() => {
    console.error('[Shutdown] Forced exit after timeout.');
    process.exit(1);
  }, 10000);
};

process.on('SIGTERM', () => shutdown('SIGTERM'));
process.on('SIGINT', () => shutdown('SIGINT'));

if (env.NODE_ENV !== 'test') {
  startServer();
}

module.exports = { app, server };
