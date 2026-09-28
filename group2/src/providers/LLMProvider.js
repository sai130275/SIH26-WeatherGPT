/**
 * Abstract LLMProvider Base Class
 * Standardizes prompt building and generative advice across OpenAI, Gemini, or Mock LLM backends.
 */
class LLMProvider {
  constructor(name) {
    if (new.target === LLMProvider) {
      throw new TypeError("Cannot instantiate abstract class LLMProvider directly.");
    }
    this.name = name;
  }

  async generateAdvisory({
    message,
    intent,
    activity,
    location,
    weather,
    riskResults,
    windowComparison,
    evidence,
    language = 'en'
  }) {
    throw new Error("Method 'generateAdvisory()' must be implemented.");
  }
}

module.exports = LLMProvider;
