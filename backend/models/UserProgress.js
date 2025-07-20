const mongoose = require('mongoose');

const LessonProgressSchema = new mongoose.Schema({
    lessonId: String,
    completed: { type: Boolean, default: false },
    timeSpent: { type: Number, default: 0 }, // in minutes
    lastPosition: { type: Number, default: 0 }, // video position in seconds
    completedAt: Date,
    notes: String
});

const AssessmentAttemptSchema = new mongoose.Schema({
    attemptNumber: { type: Number, required: true },
    score: { type: Number, required: true },
    totalQuestions: { type: Number, required: true },
    correctAnswers: { type: Number, required: true },
    timeSpent: Number, // in minutes
    answers: [{
        questionId: String,
        userAnswer: String,
        isCorrect: Boolean,
        points: Number
    }],
    passed: { type: Boolean, required: true },
    completedAt: { type: Date, default: Date.now }
});

const UserProgressSchema = new mongoose.Schema({
    userId: {
        type: mongoose.Schema.Types.ObjectId,
        ref: 'User',
        required: true
    },
    courseId: {
        type: mongoose.Schema.Types.ObjectId,
        ref: 'LMSCourse',
        required: true
    },
    
    // Enrollment
    enrolledAt: { type: Date, default: Date.now },
    status: {
        type: String,
        enum: ['enrolled', 'in_progress', 'completed', 'dropped'],
        default: 'enrolled'
    },
    
    // Progress Tracking
    lessonsProgress: [LessonProgressSchema],
    overallProgress: { type: Number, default: 0 }, // percentage
    timeSpent: { type: Number, default: 0 }, // total minutes
    lastAccessedAt: Date,
    
    // Assessment
    assessmentAttempts: [AssessmentAttemptSchema],
    bestScore: { type: Number, default: 0 },
    hasPassedAssessment: { type: Boolean, default: false },
    
    // Completion
    completedAt: Date,
    certificateIssued: { type: Boolean, default: false },
    certificateUrl: String,
    
    // Rewards
    pointsEarned: { type: Number, default: 0 },
    bonusPointsEarned: { type: Number, default: 0 },
    
    // Rating
    rating: Number, // 1-5 stars
    review: String,
    reviewedAt: Date
    
}, {
    timestamps: true
});

// Compound index for user-course combination
UserProgressSchema.index({ userId: 1, courseId: 1 }, { unique: true });

// Index for analytics
UserProgressSchema.index({ status: 1, completedAt: -1 });
UserProgressSchema.index({ userId: 1, status: 1 });

// Method to calculate progress
UserProgressSchema.methods.calculateProgress = function() {
    if (this.lessonsProgress.length === 0) return 0;
    
    const completedLessons = this.lessonsProgress.filter(lesson => lesson.completed).length;
    const progress = Math.round((completedLessons / this.lessonsProgress.length) * 100);
    
    this.overallProgress = progress;
    
    if (progress === 100 && !this.completedAt) {
        this.status = 'completed';
        this.completedAt = new Date();
    } else if (progress > 0 && this.status === 'enrolled') {
        this.status = 'in_progress';
    }
    
    return progress;
};

// Method to mark lesson as completed
UserProgressSchema.methods.completeLesson = function(lessonId, timeSpent = 0) {
    let lessonProgress = this.lessonsProgress.find(lp => lp.lessonId === lessonId);
    
    if (!lessonProgress) {
        lessonProgress = {
            lessonId,
            completed: false,
            timeSpent: 0,
            lastPosition: 0
        };
        this.lessonsProgress.push(lessonProgress);
    }
    
    lessonProgress.completed = true;
    lessonProgress.timeSpent += timeSpent;
    lessonProgress.completedAt = new Date();
    
    this.timeSpent += timeSpent;
    this.lastAccessedAt = new Date();
    
    this.calculateProgress();
};

// Method to record assessment attempt
UserProgressSchema.methods.recordAssessmentAttempt = function(score, totalQuestions, correctAnswers, timeSpent, answers, passingScore) {
    const passed = score >= passingScore;
    const attemptNumber = this.assessmentAttempts.length + 1;
    
    const attempt = {
        attemptNumber,
        score,
        totalQuestions,
        correctAnswers,
        timeSpent,
        answers,
        passed
    };
    
    this.assessmentAttempts.push(attempt);
    
    if (score > this.bestScore) {
        this.bestScore = score;
    }
    
    if (passed && !this.hasPassedAssessment) {
        this.hasPassedAssessment = true;
        // Trigger certificate generation
    }
    
    return attempt;
};

module.exports = mongoose.model('UserProgress', UserProgressSchema);