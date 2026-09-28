const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const mongoose = require('mongoose');
const User = require('../models/User');
const { sendSuccess, sendError } = require('../utils/responseFormatter');
const { JWT_SECRET } = require('../config/env');
const mockUsers = new Map();

const register = async (req, res, next) => {
  try {
    const { name, email, password, language, preferredActivity } = req.body;

    if (!name || !email || !password) {
      return sendError(res, 'VALIDATION_ERROR', 'Name, email and password are required.', 400);
    }

    const hashedPassword = await bcrypt.hash(password, 10);

    let userDoc;
    try {
      if (mongoose.connection.readyState !== 1) {
        throw new Error("MongoDB connection not active");
      }
      const existingUser = await User.findOne({ email }).maxTimeMS(500);
      if (existingUser) {
        return sendError(res, 'USER_EXISTS', 'User email is already registered.', 400);
      }
      userDoc = await User.create({
        name,
        email,
        password: hashedPassword,
        language: language || 'en',
        preferredActivity: preferredActivity || 'travel'
      });
    } catch (dbErr) {
      // Fallback in-memory
      if (mockUsers.has(email)) {
        return sendError(res, 'USER_EXISTS', 'User email is already registered.', 400);
      }
      userDoc = {
        _id: 'mock_user_' + Date.now(),
        name,
        email,
        language: language || 'en',
        preferredActivity: preferredActivity || 'travel'
      };
      mockUsers.set(email, { ...userDoc, password: hashedPassword });
    }

    const token = jwt.sign(
      { id: userDoc._id, email: userDoc.email, name: userDoc.name },
      JWT_SECRET,
      { expiresIn: '7d' }
    );

    return sendSuccess(res, {
      token,
      user: {
        id: userDoc._id,
        name: userDoc.name,
        email: userDoc.email,
        language: userDoc.language,
        preferredActivity: userDoc.preferredActivity
      }
    }, 'User registered successfully', 201);
  } catch (err) {
    next(err);
  }
};

const login = async (req, res, next) => {
  try {
    const { email, password } = req.body;

    if (!email || !password) {
      return sendError(res, 'VALIDATION_ERROR', 'Email and password are required.', 400);
    }

    let user = null;
    let hashedPassword = null;

    try {
      if (mongoose.connection.readyState !== 1) {
        throw new Error("MongoDB connection not active");
      }
      user = await User.findOne({ email }).maxTimeMS(500);
      if (user) hashedPassword = user.password;
    } catch (dbErr) {
      user = mockUsers.get(email);
      if (user) hashedPassword = user.password;
    }

    if (!user || !hashedPassword) {
      return sendError(res, 'INVALID_CREDENTIALS', 'Invalid email or password.', 401);
    }

    const isMatch = await bcrypt.compare(password, hashedPassword);
    if (!isMatch) {
      return sendError(res, 'INVALID_CREDENTIALS', 'Invalid email or password.', 401);
    }

    const token = jwt.sign(
      { id: user._id || user.id, email: user.email, name: user.name },
      JWT_SECRET,
      { expiresIn: '7d' }
    );

    return sendSuccess(res, {
      token,
      user: {
        id: user._id || user.id,
        name: user.name,
        email: user.email,
        language: user.language || 'en',
        preferredActivity: user.preferredActivity || 'travel'
      }
    }, 'Login successful');
  } catch (err) {
    next(err);
  }
};

const getMe = async (req, res, next) => {
  try {
    return sendSuccess(res, {
      user: req.user
    });
  } catch (err) {
    next(err);
  }
};

module.exports = {
  register,
  login,
  getMe
};
