const express = require('express');
const router = express.Router();
const { getRiskMap } = require('../controllers/mapController');

router.get('/map', getRiskMap);

module.exports = router;
