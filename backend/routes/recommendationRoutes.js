const express = require('express');
const router = express.Router();
const recommendationController = require('../controllers/recommendationController');

router.post('/recommend', recommendationController.getRecommendation);
router.get('/history', recommendationController.getHistory);
router.post('/market', recommendationController.getMarketPrice); // 

module.exports = router;