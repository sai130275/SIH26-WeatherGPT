const jwt = require('jsonwebtoken');
const { sendError } = require('../utils/responseFormatter');
const { JWT_SECRET } = require('../config/env');

const authenticateToken = (req, res, next) => {
  const authHeader = req.headers['authorization'];
  const token = authHeader && authHeader.split(' ')[1];

  if (!token) {
    return sendError(res, 'UNAUTHORIZED', 'Access token required.', 401);
  }

  jwt.verify(token, JWT_SECRET, (err, user) => {
    if (err) {
      return sendError(res, 'INVALID_TOKEN', 'Token invalid or expired.', 403);
    }
    req.user = user;
    next();
  });
};

module.exports = {
  authenticateToken
};
