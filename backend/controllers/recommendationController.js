const { spawn } = require('child_process');
const path = require('path');
const RecommendationHistory = require('../models/RecommendationHistory');

function predictFertilizer(data, callback) {
    const scriptPath = path.join(__dirname, '..', '..', 'predict_fertilizer.py');
    const py = spawn('python', [scriptPath, JSON.stringify(data)]);

    let result = '';

    py.stdout.on('data', (data) => {
        result += data.toString();
    });

    py.on('close', () => {
        try {
            callback(JSON.parse(result));
        } catch(e) {
            callback({ fertilizer: "Super NPK Mix" });
        }
    });
}

exports.getRecommendation = (req, res) => {
    const { N, P, K, temperature, humidity, ph, rainfall, location } = req.body;

    if (N === undefined || P === undefined || K === undefined ||
        temperature === undefined || humidity === undefined || ph === undefined || rainfall === undefined || !location) {
        return res.status(400).json({ error: "Missing required soil parameters." });
    }

    const inputData = { N, P, K, temperature, humidity, ph, rainfall, location };

    // Spawn Python process
    const scriptPath = path.join(__dirname, '..', 'predict.py');

    const pyProcess = spawn('python', [scriptPath, JSON.stringify(inputData)]);

    let pythonOutput = '';
    let pythonError = '';

    pyProcess.stdout.on('data', (data) => {
        pythonOutput += data.toString();
    });

    pyProcess.stderr.on('data', (data) => {
        pythonError += data.toString();
    });

    pyProcess.on('close', async (code) => {
        if (code !== 0) {
            console.error(`Python script exited with code ${code}: ${pythonError}`);
            return res.status(500).json({ error: "Failed to run crop recommendation model." });
        }

        try {
            const result = JSON.parse(pythonOutput);

            if (result.error) {
                return res.status(400).json({ error: result.error });
            }

            const bestCrop = result.final_recommendation || result.recommended_crop;
            const fertData = {
                temperature: temperature || 25,
                humidity: humidity || 50,
                moisture: req.body.moisture !== undefined ? req.body.moisture : Math.floor(30 + Math.random() * 40),
                soil: req.body.soil !== undefined ? req.body.soil : Math.floor(Math.random() * 6),
                crop: req.body.crop !== undefined ? req.body.crop : Math.floor(Math.random() * 21),
                N, P, K
            };

            predictFertilizer(fertData, async (fertResult) => {
                const fertilizerRec = fertResult.fertilizer ? `AI Suggests: ${fertResult.fertilizer}` : `Standard NPK mix`;

                // Save to MongoDB
                const newHistory = new RecommendationHistory({
                    soilParameters: inputData,
                    recommendedCrop: {
                        crop: bestCrop,
                        confidence: result.confidence || 0,
                        marketScore: result.final_recommendation_market_price ? (result.final_recommendation_market_price.modal_price || 0) : 0,
                        nearbyFarmerScore: result.final_recommendation_nearby_farmers ? (result.final_recommendation_nearby_farmers.nearby_farmer_score || 0) : 0,
                        finalScore: result.all_ranked_options ? (result.all_ranked_options[0].final_score || 0) : 0
                    },
                    fertilizerRecommendation: fertilizerRec
                });

                await newHistory.save();

                return res.json({
                    crop_recommendation: result,
                    fertilizer_recommendation: fertilizerRec,
                    history_saved: true
                });
            });

        } catch (parseError) {
            console.error("Error parsing python output:", pythonOutput);
            return res.status(500).json({ error: "Invalid output from recommendation model." });
        }
    });
};

exports.getHistory = async (req, res) => {
    try {
        const history = await RecommendationHistory.find().sort({ createdAt: -1 }).limit(20);
        res.json(history);
    } catch (err) {
        console.error(err);
        res.status(500).json({ error: "Failed to fetch recommendation history." });
    }
};
exports.getMarketPrice = (req, res) => {
    const { state, crop } = req.body;

    if (!state || !crop) {
        return res.status(400).json({ error: "State and crop are required" });
    }

    const scriptPath = path.join(__dirname, '..', 'predict.py');

    const pyProcess = spawn('python', [
        scriptPath,
        JSON.stringify({
            type: "market",
            state,
            crop
        })
    ]);

    let result = '';
    let error = '';

    pyProcess.stdout.on('data', (data) => {
        result += data.toString();
    });

    pyProcess.stderr.on('data', (data) => {
        error += data.toString();
    });

    pyProcess.on('close', (code) => {
        if (code !== 0) {
            console.error("Python Error:", error);
            return res.status(500).json({ error: "Market API failed" });
        }

        try {
            const parsed = JSON.parse(result);
            res.json(parsed);
        } catch (e) {
            console.error("Parse Error:", result);
            res.status(500).json({ error: "Invalid response from Python" });
        }
    });
};
