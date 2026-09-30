const Redis = require('ioredis');

// Distributed cache abstraction with transparent fallback to an in-memory Map with TTL
// when a Redis server is not deployed or unreachable.
let redisClient = null;
const memoryCache = new Map();

try {
  const redisUrl = process.env.REDIS_URL || 'redis://localhost:6379';
  redisClient = new Redis(redisUrl, {
    maxRetriesPerRequest: 1,
    retryStrategy: () => null, // Stop retrying immediately if Redis server isn't installed locally
    lazyConnect: true
  });

  redisClient.connect().then(() => {
    console.log('[Redis] Connected successfully');
  }).catch((err) => {
    console.warn(`[Redis Warning] Redis server unreachable (${err.message}). Falling back to In-Memory Cache.`);
    redisClient = null;
  });
} catch (e) {
  console.warn('[Redis Warning] Failed to initialize Redis client. Falling back to In-Memory Cache.');
  redisClient = null;
}

const getCache = async (key) => {
  if (redisClient) {
    try {
      const data = await redisClient.get(key);
      return data ? JSON.parse(data) : null;
    } catch (e) {
      // Fallback to memory
    }
  }
  const item = memoryCache.get(key);
  if (!item) return null;
  if (item.expiresAt && Date.now() > item.expiresAt) {
    memoryCache.delete(key);
    return null;
  }
  return item.value;
};

const setCache = async (key, value, ttlSeconds = 900) => {
  if (redisClient) {
    try {
      await redisClient.set(key, JSON.stringify(value), 'EX', ttlSeconds);
      return;
    } catch (e) {
      // Fallback
    }
  }
  memoryCache.set(key, {
    value,
    expiresAt: Date.now() + ttlSeconds * 1000
  });
};

module.exports = {
  getCache,
  setCache
};
