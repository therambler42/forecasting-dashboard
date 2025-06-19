import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('errors');
const responseTime = new Trend('response_time');

// Test configuration
export const options = {
  stages: [
    { duration: '30s', target: 100 },   // Ramp up to 100 users
    { duration: '1m', target: 500 },    // Ramp up to 500 users
    { duration: '2m', target: 1000 },   // Ramp up to 1000 users (1k RPS target)
    { duration: '2m', target: 1000 },   // Stay at 1000 users
    { duration: '30s', target: 0 },     // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<300'],   // 95% of requests must be below 300ms
    http_req_failed: ['rate<0.1'],      // Error rate must be below 10%
    errors: ['rate<0.1'],               // Custom error rate
  },
};

const BASE_URL = 'http://localhost:8000';

// Test data
const items = ['ITEM001', 'ITEM002', 'ITEM003', 'ITEM004', 'ITEM005'];
const models = ['prophet', 'arima'];
const forecastDays = [30, 60, 90];

export default function () {
  // Select random test parameters
  const item = items[Math.floor(Math.random() * items.length)];
  const model = models[Math.floor(Math.random() * models.length)];
  const days = forecastDays[Math.floor(Math.random() * forecastDays.length)];
  
  // Test forecast endpoint
  const forecastUrl = `${BASE_URL}/forecast/${item}?days=${days}&model=${model}`;
  
  const startTime = Date.now();
  const response = http.get(forecastUrl);
  const endTime = Date.now();
  
  const duration = endTime - startTime;
  responseTime.add(duration);
  
  // Check response
  const success = check(response, {
    'status is 200': (r) => r.status === 200,
    'response time < 300ms': (r) => r.timings.duration < 300,
    'response has forecasts': (r) => {
      try {
        const data = JSON.parse(r.body);
        return data.forecasts && data.forecasts.length > 0;
      } catch (e) {
        return false;
      }
    },
    'MAE is reasonable': (r) => {
      try {
        const data = JSON.parse(r.body);
        return data.mae_demand !== null && data.mae_price !== null;
      } catch (e) {
        return false;
      }
    },
  });
  
  if (!success) {
    errorRate.add(1);
  } else {
    errorRate.add(0);
  }
  
  // Test other endpoints occasionally
  if (Math.random() < 0.1) {
    // Test metrics endpoint
    const metricsResponse = http.get(`${BASE_URL}/metrics/${item}?model=${model}`);
    check(metricsResponse, {
      'metrics status is 200': (r) => r.status === 200,
    });
  }
  
  if (Math.random() < 0.05) {
    // Test cost analysis endpoint
    const costResponse = http.get(`${BASE_URL}/cost-analysis/${item}?period=30d`);
    check(costResponse, {
      'cost analysis status is 200': (r) => r.status === 200,
    });
  }
  
  if (Math.random() < 0.02) {
    // Test health endpoint
    const healthResponse = http.get(`${BASE_URL}/health`);
    check(healthResponse, {
      'health status is 200': (r) => r.status === 200,
    });
  }
  
  // Small sleep to simulate real user behavior
  sleep(0.1);
}

export function handleSummary(data) {
  return {
    'load_test_results.json': JSON.stringify(data, null, 2),
    stdout: `
=== Load Test Results ===
Duration: ${data.state.testRunDurationMs}ms
VUs: ${data.metrics.vus.values.max}
Requests: ${data.metrics.http_reqs.values.count}
Request Rate: ${(data.metrics.http_reqs.values.rate || 0).toFixed(2)} req/s
Failed Requests: ${(data.metrics.http_req_failed.values.rate * 100 || 0).toFixed(2)}%

Response Times:
- Average: ${(data.metrics.http_req_duration.values.avg || 0).toFixed(2)}ms
- p95: ${(data.metrics.http_req_duration.values['p(95)'] || 0).toFixed(2)}ms
- p99: ${(data.metrics.http_req_duration.values['p(99)'] || 0).toFixed(2)}ms

Thresholds:
- p95 < 300ms: ${(data.metrics.http_req_duration.values['p(95)'] || 0) < 300 ? 'PASS' : 'FAIL'}
- Error rate < 10%: ${(data.metrics.http_req_failed.values.rate * 100 || 0) < 10 ? 'PASS' : 'FAIL'}

=== Test ${data.metrics.http_req_duration.values['p(95)'] < 300 && data.metrics.http_req_failed.values.rate < 0.1 ? 'PASSED' : 'FAILED'} ===
`,
  };
}

