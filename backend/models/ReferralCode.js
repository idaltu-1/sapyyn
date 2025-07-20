const mongoose = require('mongoose');

const ReferralCodeSchema = new mongoose.Schema({
    code: {
        type: String,
        required: true,
        unique: true,
        length: 6,
        uppercase: true,
        match: /^[A-Z0-9]{6}$/
    },
    doctorId: {
        type: mongoose.Schema.Types.ObjectId,
        ref: 'User',
        required: true,
        unique: true
    },
    isActive: {
        type: Boolean,
        default: true
    },
    usageCount: {
        type: Number,
        default: 0
    },
    lastUsed: Date,
    expiresAt: {
        type: Date,
        default: () => new Date(Date.now() + 365 * 24 * 60 * 60 * 1000) // 1 year
    },
    metadata: {
        practiceId: {
            type: mongoose.Schema.Types.ObjectId,
            ref: 'Practice'
        },
        specialization: String,
        region: String,
        generatedBy: {
            type: mongoose.Schema.Types.ObjectId,
            ref: 'User'
        }
    },
    analytics: {
        totalReferrals: { type: Number, default: 0 },
        successfulReferrals: { type: Number, default: 0 },
        averageRating: { type: Number, default: 0 },
        lastReferralDate: Date
    },
    restrictions: {
        maxUsagePerDay: { type: Number, default: 50 },
        maxUsagePerMonth: { type: Number, default: 500 },
        allowedSpecialties: [String],
        allowedRegions: [String]
    }
}, {
    timestamps: true
});

// Index for efficient lookups
ReferralCodeSchema.index({ code: 1 });
ReferralCodeSchema.index({ doctorId: 1 });
ReferralCodeSchema.index({ isActive: 1, expiresAt: 1 });

// Pre-save middleware to ensure code format
ReferralCodeSchema.pre('save', function(next) {
    if (this.code) {
        this.code = this.code.toUpperCase();
    }
    next();
});

// Static method to generate unique code
ReferralCodeSchema.statics.generateUniqueCode = async function() {
    const characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
    let code;
    let exists;
    
    do {
        code = '';
        for (let i = 0; i < 6; i++) {
            code += characters.charAt(Math.floor(Math.random() * characters.length));
        }
        exists = await this.findOne({ code });
    } while (exists);
    
    return code;
};

// Instance method to check if code is valid for use
ReferralCodeSchema.methods.isValidForUse = function() {
    return this.isActive && 
           new Date() < this.expiresAt &&
           !this.isRateLimited();
};

// Instance method to check rate limiting
ReferralCodeSchema.methods.isRateLimited = function() {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    
    // Check daily usage (simplified - would need more complex tracking in production)
    return this.usageCount > this.restrictions.maxUsagePerDay;
};

// Instance method to record usage
ReferralCodeSchema.methods.recordUsage = async function() {
    this.usageCount += 1;
    this.lastUsed = new Date();
    this.analytics.totalReferrals += 1;
    await this.save();
};

module.exports = mongoose.model('ReferralCode', ReferralCodeSchema);