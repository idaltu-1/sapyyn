const mongoose = require('mongoose');

class DatabaseService {
    constructor() {
        this.isConnected = false;
        this.connectionString = process.env.MONGODB_URI || 'mongodb://localhost:27017/sapyyn';
    }

    async connect() {
        try {
            console.log('🔌 Connecting to MongoDB...');
            
            const options = {
                useNewUrlParser: true,
                useUnifiedTopology: true,
                maxPoolSize: 10,
                serverSelectionTimeoutMS: 5000,
                socketTimeoutMS: 45000,
                family: 4
            };

            await mongoose.connect(this.connectionString, options);
            
            console.log('✅ MongoDB connected successfully');
            this.isConnected = true;
            
            return true;
        } catch (error) {
            console.error('❌ MongoDB connection failed:', error.message);
            console.log('⚠️  Starting server without database connection...');
            this.isConnected = false;
            // Don't throw error - allow server to start without DB
            return false;
        }
    }

    async disconnect() {
        try {
            await mongoose.disconnect();
            console.log('📴 MongoDB disconnected');
            this.isConnected = false;
        } catch (error) {
            console.error('❌ Error disconnecting from MongoDB:', error.message);
        }
    }

    getStatus() {
        return {
            connected: this.isConnected,
            readyState: mongoose.connection.readyState,
            host: mongoose.connection.host,
            name: mongoose.connection.name,
            message: this.isConnected ? 'Connected' : 'Disconnected - Running in demo mode'
        };
    }
}

module.exports = new DatabaseService();
