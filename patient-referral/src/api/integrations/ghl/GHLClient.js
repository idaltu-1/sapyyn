import BaseAPIClient from '../../core/BaseAPIClient.js';

class GHLClient extends BaseAPIClient {
  constructor(config) {
    super({
      baseURL: config.baseURL || 'https://api.gohighlevel.com/v1',
      apiKey: config.apiKey,
      timeout: config.timeout || 30000,
    });
    
    this.locationId = config.locationId;
  }

  getDefaultHeaders() {
    return {
      ...super.getDefaultHeaders(),
      'Authorization': `Bearer ${this.apiKey}`,
    };
  }

  // Contacts
  async getContacts(params = {}) {
    return this.get('/contacts', { locationId: this.locationId, ...params });
  }

  async getContact(contactId) {
    return this.get(`/contacts/${contactId}`);
  }

  async createContact(data) {
    return this.post('/contacts', { locationId: this.locationId, ...data });
  }

  async updateContact(contactId, data) {
    return this.put(`/contacts/${contactId}`, data);
  }

  async deleteContact(contactId) {
    return this.delete(`/contacts/${contactId}`);
  }

  // Opportunities (Pipelines)
  async getOpportunities(params = {}) {
    return this.get('/opportunities', { locationId: this.locationId, ...params });
  }

  async createOpportunity(data) {
    return this.post('/opportunities', { locationId: this.locationId, ...data });
  }

  async updateOpportunity(opportunityId, data) {
    return this.put(`/opportunities/${opportunityId}`, data);
  }

  // Appointments
  async getAppointments(params = {}) {
    return this.get('/appointments', { locationId: this.locationId, ...params });
  }

  async createAppointment(data) {
    return this.post('/appointments', { locationId: this.locationId, ...data });
  }

  async updateAppointment(appointmentId, data) {
    return this.put(`/appointments/${appointmentId}`, data);
  }

  // Custom Fields
  async getCustomFields() {
    return this.get('/custom-fields', { locationId: this.locationId });
  }

  async createCustomField(data) {
    return this.post('/custom-fields', { locationId: this.locationId, ...data });
  }

  // Tags
  async getTags() {
    return this.get('/tags', { locationId: this.locationId });
  }

  async addTagToContact(contactId, tagId) {
    return this.post(`/contacts/${contactId}/tags`, { tags: [tagId] });
  }

  async removeTagFromContact(contactId, tagId) {
    return this.delete(`/contacts/${contactId}/tags/${tagId}`);
  }

  // Workflows
  async triggerWorkflow(workflowId, contactId) {
    return this.post(`/workflows/${workflowId}/trigger`, { contactId });
  }

  // Conversations
  async getConversations(params = {}) {
    return this.get('/conversations', { locationId: this.locationId, ...params });
  }

  async sendMessage(conversationId, message) {
    return this.post(`/conversations/${conversationId}/messages`, { 
      type: 'SMS',
      message 
    });
  }

  // Forms
  async getForms() {
    return this.get('/forms', { locationId: this.locationId });
  }

  async getFormSubmissions(formId, params = {}) {
    return this.get(`/forms/${formId}/submissions`, params);
  }

  // Webhooks
  async createWebhook(data) {
    return this.post('/webhooks', { locationId: this.locationId, ...data });
  }

  async getWebhooks() {
    return this.get('/webhooks', { locationId: this.locationId });
  }

  async deleteWebhook(webhookId) {
    return this.delete(`/webhooks/${webhookId}`);
  }
}

export default GHLClient;