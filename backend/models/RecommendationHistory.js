const mongoose = require('mongoose');

const recommendationHistorySchema = new mongoose.Schema({
  soilParameters: {
    N: { type: Number, required: true },
    P: { type: Number, required: true },
    K: { type: Number, required: true },
    temperature: { type: Number, required: true },
    humidity: { type: Number, required: true },
    ph: { type: Number, required: true },
    rainfall: { type: Number, required: true },
    location: { type: String, required: true }
  },
  recommendedCrop: {
    crop: { type: String, required: true },
    confidence: { type: Number },
    marketScore: { type: Number },
    nearbyFarmerScore: { type: Number },
    finalScore: { type: Number }
  },
  fertilizerRecommendation: {
    type: String,
    required: true
  },
  createdAt: {
    type: Date,
    default: Date.now
  }
});

module.exports = mongoose.model('RecommendationHistory', recommendationHistorySchema);
