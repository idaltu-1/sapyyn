const axios = require('axios');
const FormData = require('form-data');

class NoCodeBackendService {
    constructor() {
        this.airtableConfig = {
            baseId: process.env.AIRTABLE_BASE_ID,
            apiKey: process.env.AIRTABLE_API_KEY,
            baseUrl: 'https://api.airtable.com/v0'
        };
        
        this.zapierConfig = {
            webhookUrl: process.env.ZAPIER_WEBHOOK_URL,
            apiKey: process.env.ZAPIER_API_KEY
        };
        
        this.n8nConfig = {
            webhookUrl: process.env.N8N_WEBHOOK_URL,
            apiKey: process.env.N8N_API_KEY
        };
        
        this.notionConfig = {
            token: process.env.NOTION_TOKEN,
            databaseId: process.env.NOTION_DATABASE_ID,
            baseUrl: 'https://api.notion.com/v1'
        };
        
        this.makeConfig = {
            webhookUrl: process.env.MAKE_WEBHOOK_URL,
            apiKey: process.env.MAKE_API_KEY
        };
    }

    // Airtable Integration
    async createAirtableRecord(tableName, fields) {
        try {
            const response = await axios.post(
                `${this.airtableConfig.baseUrl}/${this.airtableConfig.baseId}/${tableName}`,
                {
                    fields: fields,
                    typecast: true
                },
                {
                    headers: {
                        'Authorization': `Bearer ${this.airtableConfig.apiKey}`,
                        'Content-Type': 'application/json'
                    }
                }
            );
            
            return response.data;
        } catch (error) {
            console.error('Airtable create error:', error.response?.data || error.message);
            throw new Error('Failed to create Airtable record');
        }
    }

    async updateAirtableRecord(tableName, recordId, fields) {
        try {
            const response = await axios.patch(
                `${this.airtableConfig.baseUrl}/${this.airtableConfig.baseId}/${tableName}/${recordId}`,
                {
                    fields: fields,
                    typecast: true
                },
                {
                    headers: {
                        'Authorization': `Bearer ${this.airtableConfig.apiKey}`,
                        'Content-Type': 'application/json'
                    }
                }
            );
            
            return response.data;
        } catch (error) {
            console.error('Airtable update error:', error.response?.data || error.message);
            throw new Error('Failed to update Airtable record');
        }
    }

    async getAirtableRecords(tableName, filters = {}) {
        try {
            const params = new URLSearchParams();
            
            if (filters.filterByFormula) {
                params.append('filterByFormula', filters.filterByFormula);
            }
            if (filters.sort) {
                filters.sort.forEach(sortField => {
                    params.append('sort[0][field]', sortField.field);
                    params.append('sort[0][direction]', sortField.direction || 'asc');
                });
            }
            if (filters.maxRecords) {
                params.append('maxRecords', filters.maxRecords);
            }

            const response = await axios.get(
                `${this.airtableConfig.baseUrl}/${this.airtableConfig.baseId}/${tableName}?${params}`,
                {
                    headers: {
                        'Authorization': `Bearer ${this.airtableConfig.apiKey}`
                    }
                }
            );
            
            return response.data.records;
        } catch (error) {
            console.error('Airtable fetch error:', error.response?.data || error.message);
            throw new Error('Failed to fetch Airtable records');
        }
    }

    // Zapier Integration
    async triggerZapierWebhook(data, customWebhookUrl = null) {
        try {
            const webhookUrl = customWebhookUrl || this.zapierConfig.webhookUrl;
            
            const response = await axios.post(webhookUrl, {
                ...data,
                timestamp: new Date().toISOString(),
                source: 'sapyyn-platform'
            }, {
                headers: {
                    'Content-Type': 'application/json',
                    'User-Agent': 'Sapyyn-Platform/1.0'
                }
            });
            
            return response.data;
        } catch (error) {
            console.error('Zapier webhook error:', error.response?.data || error.message);
            // Don't throw error for webhooks to prevent blocking main flow
            return { error: error.message };
        }
    }

    // N8N Integration
    async triggerN8NWorkflow(workflowData, workflowId = null) {
        try {
            let url = this.n8nConfig.webhookUrl;
            if (workflowId) {
                url = `${url}/${workflowId}`;
            }

            const response = await axios.post(url, {
                ...workflowData,
                metadata: {
                    timestamp: new Date().toISOString(),
                    source: 'sapyyn-platform',
                    environment: process.env.NODE_ENV || 'development'
                }
            }, {
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.n8nConfig.apiKey}`
                }
            });
            
            return response.data;
        } catch (error) {
            console.error('N8N workflow error:', error.response?.data || error.message);
            return { error: error.message };
        }
    }

    // Notion Integration
    async createNotionPage(databaseId, properties) {
        try {
            const response = await axios.post(
                `${this.notionConfig.baseUrl}/pages`,
                {
                    parent: {
                        database_id: databaseId || this.notionConfig.databaseId
                    },
                    properties: properties
                },
                {
                    headers: {
                        'Authorization': `Bearer ${this.notionConfig.token}`,
                        'Content-Type': 'application/json',
                        'Notion-Version': '2022-06-28'
                    }
                }
            );
            
            return response.data;
        } catch (error) {
            console.error('Notion create error:', error.response?.data || error.message);
            throw new Error('Failed to create Notion page');
        }
    }

    async updateNotionPage(pageId, properties) {
        try {
            const response = await axios.patch(
                `${this.notionConfig.baseUrl}/pages/${pageId}`,
                {
                    properties: properties
                },
                {
                    headers: {
                        'Authorization': `Bearer ${this.notionConfig.token}`,
                        'Content-Type': 'application/json',
                        'Notion-Version': '2022-06-28'
                    }
                }
            );
            
            return response.data;
        } catch (error) {
            console.error('Notion update error:', error.response?.data || error.message);
            throw new Error('Failed to update Notion page');
        }
    }

    // Make.com Integration
    async triggerMakeScenario(data, scenarioId = null) {
        try {
            let url = this.makeConfig.webhookUrl;
            if (scenarioId) {
                url = `${url}?scenario=${scenarioId}`;
            }

            const response = await axios.post(url, {
                ...data,
                metadata: {
                    timestamp: new Date().toISOString(),
                    platform: 'sapyyn',
                    version: '1.0'
                }
            }, {
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.makeConfig.apiKey}`
                }
            });
            
            return response.data;
        } catch (error) {
            console.error('Make scenario error:', error.response?.data || error.message);
            return { error: error.message };
        }
    }

    // Generic Webhook Trigger
    async triggerGenericWebhook(url, data, headers = {}) {
        try {
            const response = await axios.post(url, data, {
                headers: {
                    'Content-Type': 'application/json',
                    ...headers
                }
            });
            
            return response.data;
        } catch (error) {
            console.error('Generic webhook error:', error.response?.data || error.message);
            return { error: error.message };
        }
    }

    // Data Sync Methods
    async syncReferralToAirtable(referral) {
        if (!this.airtableConfig.baseId || !this.airtableConfig.apiKey) {
            return { skipped: 'Airtable not configured' };
        }

        try {
            const airtableFields = {
                'Referral ID': referral.referralId,
                'Patient Name': referral.patientName || 'N/A',
                'Referring Doctor': referral.referringDoctorName || 'N/A',
                'Specialist': referral.specialistName || 'N/A',
                'Type': referral.referralType,
                'Status': referral.status,
                'Urgency': referral.urgency,
                'Created Date': referral.createdAt,
                'Updated Date': referral.updatedAt,
                'Points Awarded': referral.rewardPoints || 0,
                'Notes': referral.clinicalNotes || ''
            };

            return await this.createAirtableRecord('Referrals', airtableFields);
        } catch (error) {
            console.error('Airtable sync error:', error);
            return { error: error.message };
        }
    }

    async syncUserToNotion(user) {
        if (!this.notionConfig.token) {
            return { skipped: 'Notion not configured' };
        }

        try {
            const notionProperties = {
                'Name': {
                    title: [
                        {
                            text: {
                                content: `${user.firstName} ${user.lastName}`
                            }
                        }
                    ]
                },
                'Email': {
                    email: user.email
                },
                'Role': {
                    select: {
                        name: user.role
                    }
                },
                'Reward Points': {
                    number: user.rewardPoints || 0
                },
                'Created Date': {
                    date: {
                        start: user.createdAt
                    }
                },
                'Status': {
                    select: {
                        name: user.isActive ? 'Active' : 'Inactive'
                    }
                }
            };

            return await this.createNotionPage(null, notionProperties);
        } catch (error) {
            console.error('Notion sync error:', error);
            return { error: error.message };
        }
    }

    // Automation Triggers
    async triggerReferralWorkflow(referral, action) {
        const workflowData = {
            event: 'referral_update',
            action: action, // 'created', 'accepted', 'completed', etc.
            referral: {
                id: referral._id,
                referralId: referral.referralId,
                status: referral.status,
                type: referral.referralType,
                urgency: referral.urgency,
                createdAt: referral.createdAt
            },
            timestamp: new Date().toISOString()
        };

        // Trigger multiple automation platforms
        const results = await Promise.allSettled([
            this.triggerZapierWebhook(workflowData),
            this.triggerN8NWorkflow(workflowData),
            this.triggerMakeScenario(workflowData)
        ]);

        return {
            zapier: results[0],
            n8n: results[1],
            make: results[2]
        };
    }

    async triggerRewardWorkflow(user, reward, action) {
        const workflowData = {
            event: 'reward_update',
            action: action, // 'earned', 'redeemed', 'expired'
            user: {
                id: user._id,
                email: user.email,
                name: `${user.firstName} ${user.lastName}`,
                role: user.role,
                totalPoints: user.rewardPoints
            },
            reward: {
                points: reward.points,
                type: reward.type,
                description: reward.description
            },
            timestamp: new Date().toISOString()
        };

        return await this.triggerZapierWebhook(workflowData);
    }

    // Analytics and Reporting
    async syncAnalyticsData(analytics) {
        const analyticsData = {
            event: 'analytics_update',
            data: {
                totalReferrals: analytics.totalReferrals,
                completedReferrals: analytics.completedReferrals,
                activeUsers: analytics.activeUsers,
                rewardPointsDistributed: analytics.rewardPointsDistributed,
                avgCompletionTime: analytics.avgCompletionTime,
                topPerformers: analytics.topPerformers,
                timestamp: new Date().toISOString()
            }
        };

        // Send to multiple platforms for different use cases
        return await Promise.allSettled([
            this.triggerZapierWebhook(analyticsData),
            this.syncAnalyticsToAirtable(analytics),
            this.triggerN8NWorkflow(analyticsData, 'analytics-workflow')
        ]);
    }

    async syncAnalyticsToAirtable(analytics) {
        if (!this.airtableConfig.baseId) return { skipped: 'Not configured' };

        try {
            const analyticsFields = {
                'Date': new Date().toISOString().split('T')[0],
                'Total Referrals': analytics.totalReferrals,
                'Completed Referrals': analytics.completedReferrals,
                'Active Users': analytics.activeUsers,
                'Points Distributed': analytics.rewardPointsDistributed,
                'Avg Completion Time': analytics.avgCompletionTime,
                'Top Performer': analytics.topPerformers[0]?.name || 'N/A'
            };

            return await this.createAirtableRecord('Analytics', analyticsFields);
        } catch (error) {
            return { error: error.message };
        }
    }

    // Health Check
    async healthCheck() {
        const services = {
            airtable: false,
            zapier: false,
            n8n: false,
            notion: false,
            make: false
        };

        // Test Airtable
        if (this.airtableConfig.baseId && this.airtableConfig.apiKey) {
            try {
                await axios.get(
                    `${this.airtableConfig.baseUrl}/${this.airtableConfig.baseId}/Referrals?maxRecords=1`,
                    {
                        headers: {
                            'Authorization': `Bearer ${this.airtableConfig.apiKey}`
                        }
                    }
                );
                services.airtable = true;
            } catch (error) {
                console.log('Airtable health check failed:', error.message);
            }
        }

        // Test Zapier
        if (this.zapierConfig.webhookUrl) {
            try {
                await axios.post(this.zapierConfig.webhookUrl, { test: true }, { timeout: 5000 });
                services.zapier = true;
            } catch (error) {
                console.log('Zapier health check failed:', error.message);
            }
        }

        // Test N8N
        if (this.n8nConfig.webhookUrl) {
            try {
                await axios.post(this.n8nConfig.webhookUrl, { test: true }, { timeout: 5000 });
                services.n8n = true;
            } catch (error) {
                console.log('N8N health check failed:', error.message);
            }
        }

        // Test Notion
        if (this.notionConfig.token) {
            try {
                await axios.get(
                    `${this.notionConfig.baseUrl}/users/me`,
                    {
                        headers: {
                            'Authorization': `Bearer ${this.notionConfig.token}`,
                            'Notion-Version': '2022-06-28'
                        }
                    }
                );
                services.notion = true;
            } catch (error) {
                console.log('Notion health check failed:', error.message);
            }
        }

        return services;
    }
}

module.exports = NoCodeBackendService;