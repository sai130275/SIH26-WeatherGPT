const request = require('supertest');
const { app } = require('../src/app');

jest.setTimeout(45000);

describe('WeatherGPT Complete End-to-End API Flow', () => {
  let userToken = '';
  const testEmail = `sih_tester_${Date.now()}@example.com`;

  test('1. Health check returns 200', async () => {
    const res = await request(app).get('/api/health');
    expect(res.statusCode).toEqual(200);
    expect(res.body.success).toBe(true);
    expect(res.body.data.status).toBe('ONLINE');
  });

  test('2. User Registration (POST /api/auth/register)', async () => {
    const res = await request(app)
      .post('/api/auth/register')
      .send({
        name: 'SIH Hacker',
        email: testEmail,
        password: 'password123',
        language: 'te',
        preferredActivity: 'travel'
      });
    expect(res.statusCode).toEqual(201);
    expect(res.body.success).toBe(true);
    expect(res.body.data.token).toBeDefined();
    userToken = res.body.data.token;
  });

  test('3. User Login (POST /api/auth/login)', async () => {
    const res = await request(app)
      .post('/api/auth/login')
      .send({
        email: testEmail,
        password: 'password123'
      });
    expect(res.statusCode).toEqual(200);
    expect(res.body.success).toBe(true);
    expect(res.body.data.token).toBeDefined();
  });

  test('4. Current Weather Retrieval (GET /api/weather/current)', async () => {
    const res = await request(app)
      .get('/api/weather/current')
      .query({ lat: 17.9689, lon: 79.5941 });
    expect(res.statusCode).toEqual(200);
    expect(res.body.success).toBe(true);
    expect(res.body.data.temperature).toBeDefined();
    expect(res.body.data.provider).toBe('Open-Meteo');
  });

  test('5. Forecast Retrieval (GET /api/weather/forecast)', async () => {
    const res = await request(app)
      .get('/api/weather/forecast')
      .query({ lat: 17.9689, lon: 79.5941, days: 3 });
    expect(res.statusCode).toEqual(200);
    expect(res.body.success).toBe(true);
    expect(res.body.data.hourly).toBeDefined();
    expect(Array.isArray(res.body.data.hourly)).toBe(true);
  });

  test('6. WeatherGPT Chat Query (POST /api/chat) - Complete Pipeline Flow', async () => {
    const res = await request(app)
      .post('/api/chat')
      .send({
        message: 'I have to travel tomorrow from 7 AM to 11 AM. What time is better?',
        latitude: 17.9689,
        longitude: 79.5941,
        language: 'en'
      });
    expect(res.statusCode).toEqual(200);
    expect(res.body.success).toBe(true);
    expect(res.body.data.intent).toBeDefined();
    expect(res.body.data.conversation_id).toBeDefined();
    expect(res.body.data.answer).toBeDefined();
  });

  test('7. Multilingual Chat Query (Telugu)', async () => {
    const res = await request(app)
      .post('/api/chat')
      .send({
        message: 'రేపు ప్రయాణం చేయవచ్చా?',
        latitude: 17.9689,
        longitude: 79.5941,
        language: 'te'
      });
    expect(res.statusCode).toEqual(200);
    expect(res.body.success).toBe(true);
    expect(res.body.data.answer).toBeDefined();
  });

  test('8. Fetch Geofenced Alerts (GET /api/alerts)', async () => {
    const res = await request(app)
      .get('/api/alerts')
      .query({ lat: 17.9689, lon: 79.5941 });
    expect(res.statusCode).toEqual(200);
    expect(res.body.success).toBe(true);
    expect(res.body.data.alerts).toBeDefined();
  });

  test('9. Fetch GeoJSON Risk Map (GET /api/risk/map)', async () => {
    const res = await request(app)
      .get('/api/risk/map')
      .query({ lat: 17.9689, lon: 79.5941 });
    expect(res.statusCode).toEqual(200);
    expect(res.body.type).toBe('FeatureCollection');
    expect(Array.isArray(res.body.features)).toBe(true);
  });
});
