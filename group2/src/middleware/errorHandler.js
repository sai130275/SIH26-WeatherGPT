const { sendError } = require('../utils/responseFormatter');
const { NODE_ENV } = require('../config/env');

const errorHandler = (err, req, res, next) => {
  console.error(`[API Error] ${err.stack || err.message}`);

  const statusCode = err.statusCode || 500;
  const errorCode = err.code || 'INTERNAL_SERVER_ERROR';

  // Don't leak internal error details in production
  const errorMessage = NODE_ENV === 'production'
    ? 'An unexpected error occurred.'
    : (err.message || 'An unexpected error occurred.');

  return sendError(res, errorCode, errorMessage, statusCode);
};

module.exports = errorHandler;
