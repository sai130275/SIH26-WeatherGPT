/**
 * Standardized API Response Helper
 */

const sendSuccess = (res, data = {}, message = null, statusCode = 200) => {
  return res.status(statusCode).json({
    success: true,
    data,
    message
  });
};

const sendError = (res, code = 'INTERNAL_SERVER_ERROR', message = 'An error occurred', statusCode = 500) => {
  return res.status(statusCode).json({
    success: false,
    error: {
      code,
      message
    }
  });
};

module.exports = {
  sendSuccess,
  sendError
};
