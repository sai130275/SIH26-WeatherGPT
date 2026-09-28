const express = require('express');
const router = express.Router();
const { getCurrentWeather, getForecast, getHistory } = require('../controllers/weatherController');

router.get('/current', getCurrentWeather);
router.get('/forecast', getForecast);
router.get('/history', getHistory);

module.exports = router;
