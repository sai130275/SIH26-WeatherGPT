const { calculateRisk } = require('./src/services/riskClient');
const { fetchAdvisory } = require('./src/services/advisoryClient');
const axios = require('axios');

async function runTests() {
  console.log("=== Testing Group 2 -> Group 3 Integration ===");

  const weatherData = {
    location: "Warangal",
    latitude: 17.9689,
    longitude: 79.5941,
    temperature: 42,
    humidity: 90,
    precipitation: 72,
    wind_speed: 85,
    visibility: 0.5,
    pressure: 995
  };

  try {
    // 1. Risk
    console.log("\n--- Testing Risk ---");
    const riskData = await calculateRisk(weatherData);
    console.log("Risk output received successfully!");
    console.log(`overall_score: ${riskData.overall_score}`);
    console.log(`overall_level: ${riskData.overall_level}`);
    if (riskData.risks) {
      console.log(`risks count: ${riskData.risks.length}`);
      if (riskData.risks.length > 0) {
        console.log(`First risk reasons: ${JSON.stringify(riskData.risks[0].reasons)}`);
      }
    } else {
      console.log("No risks array found!");
    }

    // 2. Advisory
    console.log("\n--- Testing Advisory ---");
    const advisoryData = await fetchAdvisory(weatherData, riskData);
    console.log("Advisory output received successfully!");
    console.log(`overall_risk_level: ${advisoryData.overall_risk_level}`);
    if (advisoryData.impacts) {
      console.log(`impacts count: ${advisoryData.impacts.length}`);
    }
    if (advisoryData.advisories) {
      console.log(`advisories count: ${advisoryData.advisories.length}`);
    }

    // 3. Chat Endpoint (End-to-End)
    console.log("\n--- Testing Chat (HTTP POST /api/chat) ---");
    const chatPayload = {
      message: "Can I travel today?",
      latitude: 17.9689,
      longitude: 79.5941
    };
    const chatResponse = await axios.post('http://localhost:5001/api/chat', chatPayload);
    console.log("Chat response received successfully!");
    const chatData = chatResponse.data.data;
    console.log(`intent: ${chatData.intent}`);
    console.log(`answer: ${chatData.answer ? chatData.answer.substring(0, 50) + "..." : "No answer"}`);
    
    // 4. Test Failure Handling (Invalid URL)
    console.log("\n--- Testing Failure Handling ---");
    process.env.GROUP3_URL = "http://localhost:9999";
    try {
      await calculateRisk(weatherData);
      console.error("FAIL: Expected calculateRisk to throw an error, but it succeeded.");
    } catch (err) {
      console.log(`SUCCESS: Caught expected error for invalid URL: ${err.message}`);
    }

  } catch (err) {
    console.error("Test execution failed:", err.message);
    if (err.response) {
      console.error("Response data:", err.response.data);
    }
  }
}

runTests();
