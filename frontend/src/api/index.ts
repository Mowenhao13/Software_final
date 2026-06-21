import axios from 'axios';

const http = axios.create({
  baseURL: '/api',
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' },
});

http.interceptors.response.use(
  (res) => res.data,
  (err) => {
    console.error('API Error:', err.message);
    return Promise.reject(err);
  }
);

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const api = {
  get: <T = any>(url: string, config?: any): Promise<T> => http.get(url, config) as any,
  post: <T = any>(url: string, data?: any, config?: any): Promise<T> => http.post(url, data, config) as any,
  put: <T = any>(url: string, data?: any, config?: any): Promise<T> => http.put(url, data, config) as any,
  delete: <T = any>(url: string, config?: any): Promise<T> => http.delete(url, config) as any,
};

// ========== Dashboard ==========
export const getKPIs = () => api.get('/dashboard/kpis');
export const getTrends = () => api.get('/dashboard/trends');
export const getSupplierDist = () => api.get('/dashboard/supplier-distribution');
export const getOrderStatus = () => api.get('/dashboard/order-status');
export const getCategoryDistribution = () => api.get('/dashboard/category-distribution');
export const getItemsSummary = () => api.get('/dashboard/items-summary');
export const getItemCatalog = () => api.get('/dashboard/item-catalog');

// ========== Supply Chain ==========
export const getShipmentMap = () => api.get('/supply-chain/map');
export const getShipmentStats = () => api.get('/supply-chain/stats');

// ========== Forecast ==========
export const getForecastModels = () => api.get('/forecast/models');
export const getForecastItems = () => api.get('/forecast/items');
export const getDemandForecast = (itemId: string, horizon = 12, model = 'auto') =>
  api.get(`/forecast/demand/${itemId}?horizon=${horizon}&model=${model}`);
export const getDemandHistory = (itemId: string, weeks = 52) =>
  api.get(`/forecast/history/${itemId}?weeks=${weeks}`);
export const batchForecast = (itemIds: string[], horizon = 12, model = 'auto') =>
  api.post('/forecast/batch', { item_ids: itemIds, horizon, model });

// ========== Optimization ==========
export const getOptimizationGraph = () => api.get('/optimization/graph');
export const findRoute = (data: any) => api.post('/optimization/route', data);
export const findRouteWithForecast = (data: any) => api.post('/optimization/route/with-forecast', data);

// ========== Risk Monitor ==========
export const getRiskOverview = () => api.get('/risk-monitor/overview');
export const getSupplyRisks = () => api.get('/risk-monitor/supply-risks');
export const getDemandRisks = () => api.get('/risk-monitor/demand-risks');
export const getLogisticsRisks = () => api.get('/risk-monitor/logistics-risks');
export const getRiskAlerts = () => api.get('/risk-monitor/alerts');