const axios = require('axios');
const { calculateRisk } = require('../src/services/riskClient');
const { fetchAdvisory } = require('../src/services/advisoryClient');
const { handleChat } = require('../src/controllers/chatController');
const { weatherProvider } = require('../src/providers');

jest.mock('axios');
jest.mock('../src/providers'); // mock weatherProvider

describe('Group 2 to Group 3 API Integration', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('RiskClient -> /risk', () => {
    const mockWeather = {
      location: 'Test',
      temperature: 30,
      humidity: 60,
      precipitation: 10,
      wind_speed: 15,
      visibility: 5,
      pressure: 1000
    };

    it('should successfully proxy risk data from Group 3', async () => {
      const mockResponse = { data: { risks: [], overall_score: 10, overall_level: 'LOW' } };
      axios.post.mockResolvedValue(mockResponse);

      const result = await calculateRisk(mockWeather);
      expect(result.overall_score).toBe(10);
      expect(axios.post).toHaveBeenCalledWith(expect.stringContaining('/risk'), expect.any(Object), expect.any(Object));
    });

    it('should fail gracefully if Group 3 is unavailable (500/timeout)', async () => {
      axios.post.mockRejectedValue(new Error('Network Error'));
      await expect(calculateRisk(mockWeather)).rejects.toThrow('Network Error');
    });
  });

  describe('AdvisoryClient -> /advisory', () => {
    const mockWeather = { temperature: 30 };
    const mockRisk = { overall_score: 10 };

    it('should successfully proxy advisory data from Group 3', async () => {
      const mockResponse = { data: { impacts: [], advisories: [], overall_risk_level: 'LOW' } };
      axios.post.mockResolvedValue(mockResponse);

      const result = await fetchAdvisory(mockWeather, mockRisk);
      expect(result.overall_risk_level).toBe('LOW');
      expect(axios.post).toHaveBeenCalledWith(expect.stringContaining('/advisory'), expect.any(Object), expect.any(Object));
    });

    it('should throw error on 4xx/5xx', async () => {
      axios.post.mockRejectedValue(new Error('Bad Request'));
      await expect(fetchAdvisory(mockWeather, mockRisk)).rejects.toThrow('Bad Request');
    });
  });

  describe('ChatController -> /chat', () => {
    it('should proxy chat requests to Group 3 and return result', async () => {
      weatherProvider.getCurrentWeather = jest.fn().mockResolvedValue({ temperature: 25 });
      axios.post.mockResolvedValue({ data: { answer: 'All good!', intent: 'general' } });

      const req = { body: { message: 'Hello', latitude: 10, longitude: 20 } };
      const res = {
        status: jest.fn().mockReturnThis(),
        json: jest.fn()
      };
      const next = jest.fn();

      await handleChat(req, res, next);

      expect(weatherProvider.getCurrentWeather).toHaveBeenCalledWith(10, 20);
      expect(axios.post).toHaveBeenCalledWith(expect.stringContaining('/chat'), expect.objectContaining({
        message: 'Hello'
      }), expect.any(Object));

      expect(res.status).toHaveBeenCalledWith(200);
      expect(res.json).toHaveBeenCalledWith(expect.objectContaining({
        success: true,
        data: expect.objectContaining({ answer: 'All good!' })
      }));
    });

    it('should fail gracefully if Group 3 throws an error', async () => {
      weatherProvider.getCurrentWeather = jest.fn().mockResolvedValue({ temperature: 25 });
      const error = new Error('Group 3 Timeout');
      axios.post.mockRejectedValue(error);

      const req = { body: { message: 'Hello', latitude: 10, longitude: 20 } };
      const res = {
        status: jest.fn().mockReturnThis(),
        json: jest.fn()
      };
      const next = jest.fn();

      await handleChat(req, res, next);

      expect(next).toHaveBeenCalledWith(error); // Should pass error to Express error handler
    });
  });
});
