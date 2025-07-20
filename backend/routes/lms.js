const express = require('express');
const router = express.Router();
const { authenticateToken } = require('../middleware/auth');
const LMSCourse = require('../models/LMSCourse');
const UserProgress = require('../models/UserProgress');
const User = require('../models/User');

// Get user LMS profile
router.get('/profile', authenticateToken, async (req, res) => {
    try {
        const user = await User.findById(req.user.userId).select('-password');
        
        if (!user) {
            return res.status(404).json({ error: 'User not found' });
        }

        // Calculate learning progress
        const enrolledCourses = await UserProgress.countDocuments({
            userId: user._id,
            status: { $in: ['enrolled', 'in_progress', 'completed'] }
        });

        const completedCourses = await UserProgress.countDocuments({
            userId: user._id,
            status: 'completed'
        });

        const totalTimeSpent = await UserProgress.aggregate([
            { $match: { userId: user._id } },
            { $group: { _id: null, totalTime: { $sum: '$timeSpent' } } }
        ]);

        const totalLearningPoints = await UserProgress.aggregate([
            { $match: { userId: user._id, status: 'completed' } },
            { $group: { _id: null, totalPoints: { $sum: '$pointsEarned' } } }
        ]);

        const overallProgress = enrolledCourses > 0 ? Math.round((completedCourses / enrolledCourses) * 100) : 0;

        const progress = {
            overallProgress,
            certificatesEarned: completedCourses,
            totalLearningPoints: totalLearningPoints[0]?.totalPoints || 0,
            studyTime: totalTimeSpent[0]?.totalTime || 0,
            learningRank: 1, // Would calculate actual rank
            learningStreak: 0 // Would calculate actual streak
        };

        res.json({ user, progress });
    } catch (error) {
        console.error('Get LMS profile error:', error);
        res.status(500).json({ error: 'Failed to fetch LMS profile' });
    }
});

// Get current courses (in progress)
router.get('/courses/current', authenticateToken, async (req, res) => {
    try {
        const userId = req.user.userId;
        
        const currentCourses = await UserProgress.find({
            userId,
            status: { $in: ['enrolled', 'in_progress'] }
        })
        .populate('courseId')
        .sort({ lastAccessedAt: -1 });

        const formattedCourses = currentCourses.map(progress => ({
            ...progress.courseId.toObject(),
            progress: progress.overallProgress,
            isEnrolled: true,
            lastAccessed: progress.lastAccessedAt
        }));

        res.json(formattedCourses);
    } catch (error) {
        console.error('Get current courses error:', error);
        res.status(500).json({ error: 'Failed to fetch current courses' });
    }
});

// Get recommended courses
router.get('/courses/recommended', authenticateToken, async (req, res) => {
    try {
        const userId = req.user.userId;
        const user = await User.findById(userId);
        
        // Get courses not enrolled in, relevant to user's role
        const enrolledCourseIds = await UserProgress.find({ userId }).distinct('courseId');
        
        const recommendedCourses = await LMSCourse.find({
            _id: { $nin: enrolledCourseIds },
            status: 'published',
            targetAudience: { $in: [user.role] }
        })
        .sort({ isFeatured: -1, averageRating: -1 })
        .limit(6);

        const formattedCourses = recommendedCourses.map(course => ({
            ...course.toObject(),
            isEnrolled: false
        }));

        res.json(formattedCourses);
    } catch (error) {
        console.error('Get recommended courses error:', error);
        res.status(500).json({ error: 'Failed to fetch recommended courses' });
    }
});

// Get all courses with filters
router.get('/courses', authenticateToken, async (req, res) => {
    try {
        const userId = req.user.userId;
        const { search, category, difficulty, duration, sort = 'popular' } = req.query;
        
        // Build query
        let query = { status: 'published' };
        
        if (search) {
            query.$text = { $search: search };
        }
        
        if (category && category !== 'all') {
            query.category = category;
        }
        
        if (difficulty) {
            query.difficulty = difficulty;
        }
        
        if (duration) {
            switch (duration) {
                case 'short':
                    query.totalDuration = { $lt: 60 };
                    break;
                case 'medium':
                    query.totalDuration = { $gte: 60, $lt: 180 };
                    break;
                case 'long':
                    query.totalDuration = { $gte: 180 };
                    break;
            }
        }

        // Build sort
        let sortQuery = {};
        switch (sort) {
            case 'newest':
                sortQuery = { publishedAt: -1 };
                break;
            case 'rating':
                sortQuery = { averageRating: -1 };
                break;
            case 'duration':
                sortQuery = { totalDuration: 1 };
                break;
            default: // popular
                sortQuery = { enrollmentCount: -1 };
        }

        const courses = await LMSCourse.find(query)
            .sort(sortQuery)
            .limit(50);

        // Check enrollment status for each course
        const enrolledCourseIds = await UserProgress.find({ userId }).distinct('courseId');
        
        const formattedCourses = courses.map(course => ({
            ...course.toObject(),
            isEnrolled: enrolledCourseIds.includes(course._id)
        }));

        res.json(formattedCourses);
    } catch (error) {
        console.error('Get courses error:', error);
        res.status(500).json({ error: 'Failed to fetch courses' });
    }
});

// Get specific course details
router.get('/courses/:courseId', authenticateToken, async (req, res) => {
    try {
        const { courseId } = req.params;
        const userId = req.user.userId;
        
        const course = await LMSCourse.findById(courseId);
        if (!course) {
            return res.status(404).json({ error: 'Course not found' });
        }

        // Check if user is enrolled
        const userProgress = await UserProgress.findOne({
            userId,
            courseId
        });

        const courseData = {
            ...course.toObject(),
            isEnrolled: !!userProgress,
            userProgress: userProgress || null
        };

        res.json(courseData);
    } catch (error) {
        console.error('Get course error:', error);
        res.status(500).json({ error: 'Failed to fetch course' });
    }
});

// Enroll in course
router.post('/courses/:courseId/enroll', authenticateToken, async (req, res) => {
    try {
        const { courseId } = req.params;
        const userId = req.user.userId;
        
        const course = await LMSCourse.findById(courseId);
        if (!course) {
            return res.status(404).json({ error: 'Course not found' });
        }

        // Check if already enrolled
        const existingProgress = await UserProgress.findOne({
            userId,
            courseId
        });

        if (existingProgress) {
            return res.status(400).json({ error: 'Already enrolled in this course' });
        }

        // Create user progress record
        const userProgress = new UserProgress({
            userId,
            courseId,
            status: 'enrolled',
            lessonsProgress: course.lessons.map(lesson => ({
                lessonId: lesson._id,
                completed: false,
                timeSpent: 0,
                lastPosition: 0
            }))
        });

        await userProgress.save();

        // Update course enrollment count
        await LMSCourse.findByIdAndUpdate(courseId, {
            $inc: { enrollmentCount: 1 }
        });

        res.json({
            message: 'Successfully enrolled in course',
            userProgress
        });
    } catch (error) {
        console.error('Enroll course error:', error);
        res.status(500).json({ error: 'Failed to enroll in course' });
    }
});

// Get course progress
router.get('/courses/:courseId/progress', authenticateToken, async (req, res) => {
    try {
        const { courseId } = req.params;
        const userId = req.user.userId;
        
        const userProgress = await UserProgress.findOne({
            userId,
            courseId
        });

        if (!userProgress) {
            return res.status(404).json({ error: 'Not enrolled in this course' });
        }

        res.json(userProgress);
    } catch (error) {
        console.error('Get progress error:', error);
        res.status(500).json({ error: 'Failed to fetch progress' });
    }
});

// Mark lesson as complete
router.post('/lessons/:lessonId/complete', authenticateToken, async (req, res) => {
    try {
        const { lessonId } = req.params;
        const userId = req.user.userId;
        const { timeSpent = 0 } = req.body;
        
        // Find the user progress record that contains this lesson
        const userProgress = await UserProgress.findOne({
            userId,
            'lessonsProgress.lessonId': lessonId
        });

        if (!userProgress) {
            return res.status(404).json({ error: 'Lesson not found in your progress' });
        }

        // Mark lesson as complete
        userProgress.completeLesson(lessonId, timeSpent);
        await userProgress.save();

        // If course is completed, award points
        if (userProgress.status === 'completed') {
            const course = await LMSCourse.findById(userProgress.courseId);
            if (course) {
                userProgress.pointsEarned = course.pointsValue + course.bonusPoints;
                await userProgress.save();

                // Update user points
                await User.findByIdAndUpdate(userId, {
                    $inc: { rewardPoints: course.pointsValue + course.bonusPoints }
                });

                // Update course completion count
                await LMSCourse.findByIdAndUpdate(userProgress.courseId, {
                    $inc: { completionCount: 1 }
                });
            }
        }

        res.json({
            message: 'Lesson completed successfully',
            progress: userProgress
        });
    } catch (error) {
        console.error('Complete lesson error:', error);
        res.status(500).json({ error: 'Failed to complete lesson' });
    }
});

// Save lesson progress
router.post('/lessons/:lessonId/progress', authenticateToken, async (req, res) => {
    try {
        const { lessonId } = req.params;
        const userId = req.user.userId;
        const { currentTime } = req.body;
        
        const userProgress = await UserProgress.findOne({
            userId,
            'lessonsProgress.lessonId': lessonId
        });

        if (!userProgress) {
            return res.status(404).json({ error: 'Lesson not found in your progress' });
        }

        // Update lesson position
        const lessonProgress = userProgress.lessonsProgress.find(lp => lp.lessonId === lessonId);
        if (lessonProgress) {
            lessonProgress.lastPosition = currentTime;
            userProgress.lastAccessedAt = new Date();
            await userProgress.save();
        }

        res.json({ message: 'Progress saved' });
    } catch (error) {
        console.error('Save progress error:', error);
        res.status(500).json({ error: 'Failed to save progress' });
    }
});

// Get/save lesson notes
router.get('/lessons/:lessonId/notes', authenticateToken, async (req, res) => {
    try {
        const { lessonId } = req.params;
        const userId = req.user.userId;
        
        const userProgress = await UserProgress.findOne({
            userId,
            'lessonsProgress.lessonId': lessonId
        });

        if (!userProgress) {
            return res.status(404).json({ error: 'Lesson not found' });
        }

        const lessonProgress = userProgress.lessonsProgress.find(lp => lp.lessonId === lessonId);
        res.json({ content: lessonProgress?.notes || '' });
    } catch (error) {
        console.error('Get notes error:', error);
        res.status(500).json({ error: 'Failed to get notes' });
    }
});

router.post('/lessons/:lessonId/notes', authenticateToken, async (req, res) => {
    try {
        const { lessonId } = req.params;
        const userId = req.user.userId;
        const { content } = req.body;
        
        const userProgress = await UserProgress.findOne({
            userId,
            'lessonsProgress.lessonId': lessonId
        });

        if (!userProgress) {
            return res.status(404).json({ error: 'Lesson not found' });
        }

        const lessonProgress = userProgress.lessonsProgress.find(lp => lp.lessonId === lessonId);
        if (lessonProgress) {
            lessonProgress.notes = content;
            await userProgress.save();
        }

        res.json({ message: 'Notes saved successfully' });
    } catch (error) {
        console.error('Save notes error:', error);
        res.status(500).json({ error: 'Failed to save notes' });
    }
});

// Complete course
router.post('/courses/:courseId/complete', authenticateToken, async (req, res) => {
    try {
        const { courseId } = req.params;
        const userId = req.user.userId;
        
        const userProgress = await UserProgress.findOne({
            userId,
            courseId
        });

        if (!userProgress) {
            return res.status(404).json({ error: 'Not enrolled in this course' });
        }

        const course = await LMSCourse.findById(courseId);
        if (!course) {
            return res.status(404).json({ error: 'Course not found' });
        }

        // Generate certificate (mock implementation)
        const certificateUrl = `/certificates/${userId}-${courseId}-${Date.now()}.pdf`;
        userProgress.certificateIssued = true;
        userProgress.certificateUrl = certificateUrl;
        
        await userProgress.save();

        res.json({
            message: 'Course completed successfully',
            certificateUrl,
            pointsEarned: userProgress.pointsEarned
        });
    } catch (error) {
        console.error('Complete course error:', error);
        res.status(500).json({ error: 'Failed to complete course' });
    }
});

module.exports = router;