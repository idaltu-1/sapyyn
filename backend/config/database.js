const mongoose = require('mongoose');

class DatabaseService {
    constructor() {
        this.isConnected = false;
        this.reconnectTimeout = null;
        this.maxReconnectAttempts = 5;
        this.reconnectAttempts = 0;
    }

    async connect() {
        try {
            const mongoUri = process.env.MONGODB_URI;
            
            if (!mongoUri) {
                throw new Error('MongoDB URI not found in environment variables');
            }

            console.log('🔌 Connecting to MongoDB Atlas...');

            const options = {
                useNewUrlParser: true,
                useUnifiedTopology: true,
                serverSelectionTimeoutMS: 5000,
                socketTimeoutMS: 45000,
                maxPoolSize: 10,
                minPoolSize: 1,
                maxIdleTimeMS: 30000,
                bufferCommands: false,
                bufferMaxEntries: 0
            };

            await mongoose.connect(mongoUri, options);

            this.isConnected = true;
            this.reconnectAttempts = 0;
            
            console.log('✅ MongoDB Atlas connected successfully!');
            console.log(`📊 Database: ${mongoose.connection.db.databaseName}`);

            this.setupEventListeners();
            return true;
        } catch (error) {
            console.error('❌ MongoDB Atlas connection failed:', error.message);
            throw error;
        }
    }

    setupEventListeners() {
        mongoose.connection.on('connected', () => {
            console.log('✅ MongoDB Atlas connection established');
            this.isConnected = true;
        });

        mongoose.connection.on('error', (error) => {
            console.error('❌ MongoDB Atlas connection error:', error);
            this.isConnected = false;
        });

        mongoose.connection.on('disconnected', () => {
            console.warn('⚠️ MongoDB Atlas disconnected');
            this.isConnected = false;
        });

        process.on('SIGINT', () => this.gracefulShutdown('SIGINT'));
        process.on('SIGTERM', () => this.gracefulShutdown('SIGTERM'));
    }

    async gracefulShutdown(signal) {
        console.log(`📤 Received ${signal}. Gracefully shutting down MongoDB connection...`);
        
        try {
            await mongoose.connection.close();
            console.log('✅ MongoDB Atlas connection closed gracefully');
            process.exit(0);
        } catch (error) {
            console.error('❌ Error during graceful shutdown:', error);
            process.exit(1);
        }
    }

    async healthCheck() {
        try {
            if (!this.isConnected) {
                return {
                    status: 'disconnected',
                    message: 'Not connected to MongoDB Atlas'
                };
            }

            await mongoose.connection.db.admin().ping();
            
            return {
                status: 'healthy',
                message: 'MongoDB Atlas connection is healthy',
                details: {
                    host: mongoose.connection.host,
                    database: mongoose.connection.db.databaseName,
                    readyState: mongoose.connection.readyState
                }
            };
        } catch (error) {
            return {
                status: 'unhealthy',
                message: 'MongoDB Atlas health check failed',
                error: error.message
            };
        }
    }

    async initializeDatabase() {
        try {
            console.log('🏗️ Initializing database structure...');
            await this.createIndexes();
            console.log('✅ Database initialization complete');
        } catch (error) {
            console.error('❌ Database initialization failed:', error);
            throw error;
        }
    }

    async createIndexes() {
        await mongoose.connection.db.collection('users').createIndex({ email: 1 }, { unique: true });
        await mongoose.connection.db.collection('referrals').createIndex({ patientEmail: 1 });
        await mongoose.connection.db.collection('referrals').createIndex({ status: 1 });
        console.log('📊 Database indexes created successfully');
    }
}

module.exports = new DatabaseService();
