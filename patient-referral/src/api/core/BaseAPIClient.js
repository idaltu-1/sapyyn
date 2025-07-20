import axios from 'axios';

class BaseAPIClient {
  constructor(config) {
    this.baseURL = config.baseURL;
    this.apiKey = config.apiKey;
    this.timeout = config.timeout || 30000;
    this.retryAttempts = config.retryAttempts || 3;
    this.retryDelay = config.retryDelay || 1000;
    
    this.client = axios.create({
      baseURL: this.baseURL,
      timeout: this.timeout,
      headers: this.getDefaultHeaders(),
    });

    this.setupInterceptors();
  }

  getDefaultHeaders() {
    return {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    };
  }

  setupInterceptors() {
    // Request interceptor
    this.client.interceptors.request.use(
      (config) => {
        // Add timestamp for request tracking
        config.metadata = { startTime: new Date() };
        console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
        return config;
      },
      (error) => {
        console.error('Request error:', error);
        return Promise.reject(error);
      }
    );

    // Response interceptor
    this.client.interceptors.response.use(
      (response) => {
        const duration = new Date() - response.config.metadata.startTime;
        console.log(`API Response: ${response.status} (${duration}ms)`);
        return response;
      },
      async (error) => {
        const { config, response } = error;
        
        // Retry logic
        if (this.shouldRetry(error) && config.__retryCount < this.retryAttempts) {
          config.__retryCount = (config.__retryCount || 0) + 1;
          
          console.log(`Retrying request (${config.__retryCount}/${this.retryAttempts})...`);
          await this.delay(this.retryDelay * config.__retryCount);
          
          return this.client(config);
        }

        // Enhanced error handling
        const enhancedError = this.enhanceError(error);
        console.error('API Error:', enhancedError);
        
        return Promise.reject(enhancedError);
      }
    );
  }

  shouldRetry(error) {
    // Retry on network errors or 5xx errors
    return !error.response || (error.response.status >= 500 && error.response.status < 600);
  }

  enhanceError(error) {
    if (error.response) {
      return {
        status: error.response.status,
        statusText: error.response.statusText,
        data: error.response.data,
        headers: error.response.headers,
        originalError: error,
      };
    } else if (error.request) {
      return {
        message: 'No response received from server',
        request: error.request,
        originalError: error,
      };
    } else {
      return {
        message: error.message,
        originalError: error,
      };
    }
  }

  delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  // HTTP Methods
  async get(endpoint, params = {}) {
    return this.client.get(endpoint, { params });
  }

  async post(endpoint, data = {}) {
    return this.client.post(endpoint, data);
  }

  async put(endpoint, data = {}) {
    return this.client.put(endpoint, data);
  }

  async patch(endpoint, data = {}) {
    return this.client.patch(endpoint, data);
  }

  async delete(endpoint) {
    return this.client.delete(endpoint);
  }

  // Pagination helper
  async getAllPages(endpoint, params = {}, pageParam = 'page') {
    let allData = [];
    let page = 1;
    let hasMore = true;

    while (hasMore) {
      const response = await this.get(endpoint, { ...params, [pageParam]: page });
      const { data, meta } = response.data;
      
      allData = allData.concat(data);
      
      // Check if there are more pages (adjust based on API response structure)
      hasMore = meta?.hasNextPage || (data.length > 0 && data.length === (params.limit || 100));
      page++;
    }

    return allData;
  }

  // Batch operations helper
  async batchOperation(items, operation, batchSize = 10) {
    const results = [];
    
    for (let i = 0; i < items.length; i += batchSize) {
      const batch = items.slice(i, i + batchSize);
      const batchPromises = batch.map(item => operation(item));
      const batchResults = await Promise.allSettled(batchPromises);
      results.push(...batchResults);
    }

    return results;
  }
}

export default BaseAPIClient;