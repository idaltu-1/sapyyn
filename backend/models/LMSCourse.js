const mongoose = require('mongoose');

const LessonSchema = new mongoose.Schema({
    title: { type: String, required: true },
    description: String,
    videoUrl: String,
    duration: Number, // in minutes
    materials: [{
        title: String,
        type: { type: String, enum: ['pdf', 'doc', 'link', 'quiz'] },
        url: String,
        downloadable: { type: Boolean, default: true }
    }],
    order: { type: Number, required: true },
    isPreview: { type: Boolean, default: false }
});

const AssessmentQuestionSchema = new mongoose.Schema({
    question: { type: String, required: true },
    type: { 
        type: String, 
        enum: ['multiple_choice', 'true_false', 'short_answer', 'essay'],
        required: true 
    },
    options: [String], // For multiple choice
    correctAnswer: String,
    points: { type: Number, default: 1 },
    explanation: String
});

const LMSCourseSchema = new mongoose.Schema({
    title: { type: String, required: true },
    description: { type: String, required: true },
    shortDescription: String,
    category: {
        type: String,
        enum: ['clinical', 'compliance', 'technology', 'communication', 'business'],
        required: true
    },
    difficulty: {
        type: String,
        enum: ['beginner', 'intermediate', 'advanced'],
        default: 'beginner'
    },
    thumbnailUrl: String,
    previewVideoUrl: String,
    
    // Course Structure
    lessons: [LessonSchema],
    totalDuration: Number, // in minutes
    estimatedCompletion: String, // e.g., "2-3 hours"
    
    // Assessment
    hasAssessment: { type: Boolean, default: false },
    assessmentQuestions: [AssessmentQuestionSchema],
    passingScore: { type: Number, default: 80 }, // percentage
    maxAttempts: { type: Number, default: 3 },
    
    // Certification
    certificateTemplate: String,
    certificateTitle: String,
    certificateDescription: String,
    
    // Metadata
    tags: [String],
    prerequisites: [{
        type: mongoose.Schema.Types.ObjectId,
        ref: 'LMSCourse'
    }],
    targetAudience: [String], // ['dentist', 'specialist', 'admin']
    learningObjectives: [String],
    
    // Publishing
    status: {
        type: String,
        enum: ['draft', 'published', 'archived'],
        default: 'draft'
    },
    publishedAt: Date,
    authorId: {
        type: mongoose.Schema.Types.ObjectId,
        ref: 'User',
        required: true
    },
    
    // Rewards
    pointsValue: { type: Number, default: 100 },
    bonusPoints: { type: Number, default: 0 },
    
    // Analytics
    enrollmentCount: { type: Number, default: 0 },
    completionCount: { type: Number, default: 0 },
    averageRating: { type: Number, default: 0 },
    totalRatings: { type: Number, default: 0 },
    
    // Settings
    isFeatured: { type: Boolean, default: false },
    isRequired: { type: Boolean, default: false }, // For compliance courses
    expiresAfter: Number, // months after completion
    
}, {
    timestamps: true
});

// Virtual for completion rate
LMSCourseSchema.virtual('completionRate').get(function() {
    if (this.enrollmentCount === 0) return 0;
    return Math.round((this.completionCount / this.enrollmentCount) * 100);
});

// Index for search and filtering
LMSCourseSchema.index({ title: 'text', description: 'text', tags: 'text' });
LMSCourseSchema.index({ category: 1, difficulty: 1 });
LMSCourseSchema.index({ status: 1, publishedAt: -1 });

module.exports = mongoose.model('LMSCourse', LMSCourseSchema);