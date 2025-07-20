const mongoose = require('mongoose');

class DatabaseService {
    constructor() {
        this.isConnected = false;
        this.connectionString = process.env.MONGODB_URI || 'mongodb://localhost:27017/sapyyn';
    }

    async connect() {
        try {
            console.log('🔌 Connecting to MongoDB Atlas...');
            
            const options = {
                useNewUrlParser: true,
                useUnifiedTopology: true,
                maxPoolSize: 10,
                serverSelectionTimeoutMS: 5000,
                socketTimeoutMS: 45000,
                family: 4
            };

            await mongoose.connect(this.connectionString, options);
            
            console.log('✅ MongoDB Atlas connected successfully');
            this.isConnected = true;
            
            return true;
        } catch (error) {
            console.error('❌ MongoDB Atlas connection failed:', error.message);
            this.isConnected = false;
            throw error;
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
            name: mongoose.connection.name
        };
    }
}

module.exports = new DatabaseService();
