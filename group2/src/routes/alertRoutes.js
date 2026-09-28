const express = require('express');
const router = express.Router();
const { getAlerts, checkAlerts } = require('../controllers/alertController');

router.get('/', getAlerts);
router.post('/check', checkAlerts);

module.exports = router;
