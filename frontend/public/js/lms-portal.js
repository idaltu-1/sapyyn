// Enhanced LMS Portal JavaScript
class LMSPortal {
    constructor() {
        this.currentUser = null;
        this.currentCourse = null;
        this.currentLesson = null;
        this.videoPlayer = null;
        this.progressData = {
            overallProgress: 0,
            certificatesEarned: 0,
            totalLearningPoints: 0,
            studyTime: 0,
            learningRank: 0,
            learningStreak: 0
        };
        this.currentView = 'dashboard';
        this.init();
    }

    async init() {
        await this.loadUserData();
        this.setupEventListeners();
        this.showDashboard();
        this.updateProgressDisplay();
    }

    // Load user data and learning progress
    async loadUserData() {
        try {
            const token = localStorage.getItem('sapyyn_token') || sessionStorage.getItem('sapyyn_token');
            const response = await fetch('/api/lms/profile', {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                this.currentUser = data.user;
                this.progressData = { ...this.progressData, ...data.progress };
                this.updateUIWithUserData();
            }
        } catch (error) {
            console.error('Error loading user data:', error);
            this.showToast('error', 'Failed to load learning data');
        }
    }

    // Setup event listeners
    setupEventListeners() {
        // Category links
        document.querySelectorAll('.category-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                this.filterCourses(link.dataset.category);
            });
        });

        // Course search
        const searchInput = document.getElementById('courseSearch');
        if (searchInput) {
            searchInput.addEventListener('input', this.debounce(() => {
                this.searchCourses(searchInput.value);
            }, 300));
        }

        // Filter controls
        const filters = ['difficultyFilter', 'durationFilter', 'sortFilter'];
        filters.forEach(filterId => {
            const element = document.getElementById(filterId);
            if (element) {
                element.addEventListener('change', () => {
                    this.applyCourseFilters();
                });
            }
        });

        // Video player events
        this.setupVideoPlayerEvents();
    }

    // Setup video player events
    setupVideoPlayerEvents() {
        const videoElement = document.getElementById('courseVideo');
        if (videoElement && window.videojs) {
            this.videoPlayer = videojs(videoElement, {
                responsive: true,
                fluid: true,
                playbackRates: [0.5, 1, 1.25, 1.5, 2],
                plugins: {
                    hotkeys: {
                        volumeStep: 0.1,
                        seekStep: 5,
                        enableModifiersForNumbers: false
                    }
                }
            });

            // Track progress
            this.videoPlayer.on('timeupdate', () => {
                this.updateVideoProgress();
            });

            this.videoPlayer.on('ended', () => {
                this.handleVideoCompleted();
            });
        }
    }

    // Update UI with user data
    updateUIWithUserData() {
        // Update user name
        const userNameElements = document.querySelectorAll('#userName, #welcomeUserName');
        userNameElements.forEach(el => {
            if (el) el.textContent = `${this.currentUser.firstName} ${this.currentUser.lastName}`;
        });

        // Update progress sidebar
        document.getElementById('overallProgress').textContent = this.progressData.overallProgress + '%';
        document.getElementById('overallProgressBar').style.width = this.progressData.overallProgress + '%';
        document.getElementById('certificatesEarned').textContent = this.progressData.certificatesEarned;
        document.getElementById('totalLearningPoints').textContent = this.progressData.totalLearningPoints.toLocaleString();

        // Update quick stats
        document.getElementById('studyTime').textContent = this.formatStudyTime(this.progressData.studyTime);
        document.getElementById('learningRank').textContent = '#' + (this.progressData.learningRank || '-');
        document.getElementById('learningStreak').textContent = this.progressData.learningStreak + ' days';

        // Update current level
        document.getElementById('currentLevel').textContent = this.getCurrentLevel();
    }

    // Get current level based on progress
    getCurrentLevel() {
        const points = this.progressData.totalLearningPoints;
        if (points >= 5000) return 'Expert';
        if (points >= 2500) return 'Advanced';
        if (points >= 1000) return 'Intermediate';
        return 'Beginner';
    }

    // Format study time
    formatStudyTime(minutes) {
        if (minutes >= 60) {
            const hours = Math.floor(minutes / 60);
            const remainingMinutes = minutes % 60;
            return remainingMinutes > 0 ? `${hours}h ${remainingMinutes}m` : `${hours}h`;
        }
        return `${minutes}m`;
    }

    // Show dashboard view
    async showDashboard() {
        this.switchView('dashboard');
        await this.loadCurrentCourses();
        await this.loadRecommendedCourses();
        await this.loadRecentAchievements();
    }

    // Show catalog view
    async showCatalog() {
        this.switchView('catalog');
        await this.loadAllCourses();
    }

    // Switch between views
    switchView(viewName) {
        // Hide all views
        document.querySelectorAll('.content-view').forEach(view => {
            view.style.display = 'none';
        });

        // Show selected view
        const targetView = document.getElementById(`${viewName}View`);
        if (targetView) {
            targetView.style.display = 'block';
        }

        this.currentView = viewName;
    }

    // Load current courses (in progress)
    async loadCurrentCourses() {
        try {
            const response = await fetch('/api/lms/courses/current');
            if (response.ok) {
                const courses = await response.json();
                this.displayCurrentCourses(courses);
            }
        } catch (error) {
            console.error('Error loading current courses:', error);
        }
    }

    // Display current courses
    displayCurrentCourses(courses) {
        const container = document.getElementById('currentCourses');
        if (!container) return;

        if (courses.length === 0) {
            container.innerHTML = `
                <div class="col-12">
                    <div class="text-center py-4">
                        <i class="fas fa-book-open fa-3x text-muted mb-3"></i>
                        <h5 class="text-muted">No courses in progress</h5>
                        <p class="text-muted">Start learning by browsing our course catalog</p>
                        <button class="btn btn-primary" onclick="lmsPortal.showCatalog()">
                            Browse Courses
                        </button>
                    </div>
                </div>
            `;
            return;
        }

        container.innerHTML = '';
        courses.forEach(course => {
            const courseCard = this.createCourseCard(course, true);
            container.appendChild(courseCard);
        });
    }

    // Load recommended courses
    async loadRecommendedCourses() {
        try {
            const response = await fetch('/api/lms/courses/recommended');
            if (response.ok) {
                const courses = await response.json();
                this.displayRecommendedCourses(courses);
            }
        } catch (error) {
            console.error('Error loading recommended courses:', error);
        }
    }

    // Display recommended courses
    displayRecommendedCourses(courses) {
        const container = document.getElementById('recommendedCourses');
        if (!container) return;

        container.innerHTML = '';
        courses.slice(0, 3).forEach(course => {
            const courseCard = this.createCourseCard(course, false);
            container.appendChild(courseCard);
        });
    }

    // Create course card element
    createCourseCard(course, showProgress = false) {
        const card = document.createElement('div');
        card.className = 'col-lg-4 col-md-6 mb-3';

        const progress = showProgress ? course.progress || 0 : 0;
        const difficultyColor = this.getDifficultyColor(course.difficulty);
        const enrollmentStatus = course.isEnrolled ? 'enrolled' : 'not-enrolled';

        card.innerHTML = `
            <div class="card h-100 course-card" data-course-id="${course._id}">
                <div class="position-relative">
                    <img src="${course.thumbnailUrl || '/images/default-course.jpg'}" 
                         class="card-img-top" style="height: 150px; object-fit: cover;" 
                         alt="${course.title}">
                    <div class="position-absolute top-0 end-0 m-2">
                        <span class="badge bg-${difficultyColor}">${course.difficulty}</span>
                    </div>
                    ${course.isFeatured ? '<div class="position-absolute top-0 start-0 m-2"><span class="badge bg-warning">Featured</span></div>' : ''}
                </div>
                <div class="card-body d-flex flex-column">
                    <h6 class="card-title">${course.title}</h6>
                    <p class="card-text text-muted small flex-grow-1">${course.shortDescription || course.description}</p>
                    
                    <div class="course-meta mb-2">
                        <small class="text-muted">
                            <i class="fas fa-clock me-1"></i>${course.estimatedCompletion || this.formatDuration(course.totalDuration)}
                            <i class="fas fa-users ms-2 me-1"></i>${course.enrollmentCount || 0}
                            <i class="fas fa-star ms-2 me-1"></i>${course.averageRating || 0}/5
                        </small>
                    </div>

                    ${showProgress ? `
                        <div class="progress mb-2" style="height: 4px;">
                            <div class="progress-bar bg-success" style="width: ${progress}%"></div>
                        </div>
                        <small class="text-muted">${progress}% complete</small>
                    ` : ''}

                    <div class="mt-auto">
                        ${course.isEnrolled ? `
                            <button class="btn btn-primary btn-sm w-100" onclick="lmsPortal.continueCourse('${course._id}')">
                                ${progress > 0 ? 'Continue Learning' : 'Start Course'}
                            </button>
                        ` : `
                            <button class="btn btn-outline-primary btn-sm w-100" onclick="lmsPortal.enrollInCourse('${course._id}')">
                                Enroll Now
                            </button>
                        `}
                    </div>
                </div>
            </div>
        `;

        return card;
    }

    // Get difficulty color
    getDifficultyColor(difficulty) {
        const colors = {
            beginner: 'success',
            intermediate: 'warning',
            advanced: 'danger'
        };
        return colors[difficulty] || 'secondary';
    }

    // Format duration
    formatDuration(minutes) {
        if (!minutes) return 'N/A';
        if (minutes >= 60) {
            const hours = Math.floor(minutes / 60);
            const remainingMinutes = minutes % 60;
            return remainingMinutes > 0 ? `${hours}h ${remainingMinutes}m` : `${hours}h`;
        }
        return `${minutes}m`;
    }

    // Load all courses for catalog
    async loadAllCourses() {
        try {
            const params = this.buildCourseParams();
            const response = await fetch(`/api/lms/courses?${params}`);
            if (response.ok) {
                const courses = await response.json();
                this.displayCourseGrid(courses);
            }
        } catch (error) {
            console.error('Error loading courses:', error);
        }
    }

    // Build course parameters for filtering
    buildCourseParams() {
        const params = new URLSearchParams();
        
        const search = document.getElementById('courseSearch')?.value;
        if (search) params.append('search', search);
        
        const difficulty = document.getElementById('difficultyFilter')?.value;
        if (difficulty) params.append('difficulty', difficulty);
        
        const duration = document.getElementById('durationFilter')?.value;
        if (duration) params.append('duration', duration);
        
        const sort = document.getElementById('sortFilter')?.value;
        if (sort) params.append('sort', sort);

        return params.toString();
    }

    // Display course grid
    displayCourseGrid(courses) {
        const container = document.getElementById('courseGrid');
        if (!container) return;

        if (courses.length === 0) {
            container.innerHTML = `
                <div class="col-12 text-center py-5">
                    <i class="fas fa-search fa-3x text-muted mb-3"></i>
                    <h5 class="text-muted">No courses found</h5>
                    <p class="text-muted">Try adjusting your search criteria</p>
                </div>
            `;
            return;
        }

        container.innerHTML = '';
        courses.forEach(course => {
            const courseCard = this.createCourseCard(course, course.isEnrolled);
            container.appendChild(courseCard);
        });
    }

    // Enroll in course
    async enrollInCourse(courseId) {
        try {
            const response = await fetch(`/api/lms/courses/${courseId}/enroll`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('sapyyn_token') || sessionStorage.getItem('sapyyn_token')}`
                }
            });

            if (response.ok) {
                const result = await response.json();
                this.showToast('success', 'Successfully enrolled in course!');
                
                // Refresh course display
                if (this.currentView === 'catalog') {
                    this.loadAllCourses();
                } else {
                    this.loadCurrentCourses();
                    this.loadRecommendedCourses();
                }
            } else {
                const error = await response.json();
                this.showToast('error', error.message || 'Failed to enroll in course');
            }
        } catch (error) {
            console.error('Error enrolling in course:', error);
            this.showToast('error', 'Failed to enroll in course');
        }
    }

    // Continue course
    async continueCourse(courseId) {
        try {
            const response = await fetch(`/api/lms/courses/${courseId}`);
            if (response.ok) {
                const course = await response.json();
                this.currentCourse = course;
                await this.showCoursePlayer(course);
            }
        } catch (error) {
            console.error('Error loading course:', error);
            this.showToast('error', 'Failed to load course');
        }
    }

    // Show course player
    async showCoursePlayer(course) {
        this.switchView('player');
        
        // Update course header
        document.getElementById('courseTitle').textContent = course.title;
        document.getElementById('courseDescription').textContent = course.description;
        document.getElementById('courseDifficulty').textContent = course.difficulty;
        document.getElementById('courseDuration').textContent = course.estimatedCompletion || this.formatDuration(course.totalDuration);
        document.getElementById('coursePoints').textContent = `+${course.pointsValue} points`;

        // Load course outline
        this.displayCourseOutline(course.lessons);
        
        // Load course materials
        this.displayCourseMaterials(course.materials || []);
        
        // Load progress
        await this.loadCourseProgress(course._id);
        
        // Load the first lesson or last viewed lesson
        if (course.lessons && course.lessons.length > 0) {
            const lessonToLoad = this.getResumeLesson(course.lessons) || course.lessons[0];
            this.loadLesson(lessonToLoad);
        }
    }

    // Display course outline
    displayCourseOutline(lessons) {
        const container = document.getElementById('courseOutline');
        if (!container) return;

        container.innerHTML = '';
        
        lessons.forEach((lesson, index) => {
            const lessonItem = document.createElement('div');
            lessonItem.className = 'lesson-item';
            
            const isCompleted = lesson.isCompleted || false;
            const isCurrent = lesson._id === this.currentLesson?._id;
            
            lessonItem.innerHTML = `
                <div class="lesson-item-content ${isCurrent ? 'active' : ''}" 
                     onclick="lmsPortal.loadLesson(${JSON.stringify(lesson).replace(/"/g, '&quot;')})">
                    <div class="d-flex align-items-center">
                        <div class="lesson-number me-2">
                            ${isCompleted ? '<i class="fas fa-check-circle text-success"></i>' : index + 1}
                        </div>
                        <div class="flex-grow-1">
                            <h6 class="mb-0">${lesson.title}</h6>
                            <small class="text-muted">${this.formatDuration(lesson.duration)}</small>
                        </div>
                        ${lesson.isPreview ? '<span class="badge bg-info">Preview</span>' : ''}
                    </div>
                </div>
            `;
            
            container.appendChild(lessonItem);
        });
    }

    // Display course materials
    displayCourseMaterials(materials) {
        const container = document.getElementById('courseMaterials');
        if (!container) return;

        if (materials.length === 0) {
            container.innerHTML = '<p class="text-muted">No additional materials for this course.</p>';
            return;
        }

        container.innerHTML = '';
        
        materials.forEach(material => {
            const materialItem = document.createElement('div');
            materialItem.className = 'material-item mb-2';
            
            const icon = this.getMaterialIcon(material.type);
            
            materialItem.innerHTML = `
                <div class="d-flex align-items-center">
                    <i class="fas ${icon} me-2"></i>
                    <div class="flex-grow-1">
                        <a href="${material.url}" target="_blank" class="text-decoration-none">
                            ${material.title}
                        </a>
                    </div>
                    ${material.downloadable ? '<i class="fas fa-download text-muted"></i>' : ''}
                </div>
            `;
            
            container.appendChild(materialItem);
        });
    }

    // Get material icon
    getMaterialIcon(type) {
        const icons = {
            pdf: 'fa-file-pdf text-danger',
            doc: 'fa-file-word text-primary',
            link: 'fa-external-link-alt text-info',
            quiz: 'fa-question-circle text-warning'
        };
        return icons[type] || 'fa-file';
    }

    // Load lesson
    loadLesson(lesson) {
        this.currentLesson = lesson;
        
        // Update active lesson in outline
        document.querySelectorAll('.lesson-item-content').forEach(item => {
            item.classList.remove('active');
        });
        event?.currentTarget?.classList.add('active');
        
        // Load video
        if (lesson.videoUrl && this.videoPlayer) {
            this.videoPlayer.src({
                type: 'video/mp4',
                src: lesson.videoUrl
            });
            
            // Resume from last position if available
            if (lesson.lastPosition) {
                this.videoPlayer.currentTime(lesson.lastPosition);
            }
        }
        
        // Load lesson notes if available
        this.loadLessonNotes(lesson._id);
    }

    // Get lesson to resume
    getResumeLesson(lessons) {
        // Find last incomplete lesson
        for (let lesson of lessons) {
            if (!lesson.isCompleted) {
                return lesson;
            }
        }
        return null;
    }

    // Load course progress
    async loadCourseProgress(courseId) {
        try {
            const response = await fetch(`/api/lms/courses/${courseId}/progress`);
            if (response.ok) {
                const progress = await response.json();
                this.updateCourseProgress(progress);
            }
        } catch (error) {
            console.error('Error loading course progress:', error);
        }
    }

    // Update course progress display
    updateCourseProgress(progress) {
        const progressBar = document.getElementById('courseProgressBar');
        const progressText = document.getElementById('courseProgressText');
        
        if (progressBar && progressText) {
            progressBar.style.width = progress.overallProgress + '%';
            progressText.textContent = progress.overallProgress + '%';
        }
    }

    // Update video progress
    updateVideoProgress() {
        if (!this.videoPlayer || !this.currentLesson) return;
        
        const currentTime = this.videoPlayer.currentTime();
        const duration = this.videoPlayer.duration();
        
        if (duration > 0) {
            const progress = (currentTime / duration) * 100;
            
            // Save progress periodically
            if (Math.floor(currentTime) % 30 === 0) { // Every 30 seconds
                this.saveLessonProgress(this.currentLesson._id, currentTime);
            }
        }
    }

    // Handle video completed
    async handleVideoCompleted() {
        if (!this.currentLesson) return;
        
        try {
            await this.markLessonComplete(this.currentLesson._id);
            this.showToast('success', 'Lesson completed! Points earned.');
            
            // Update UI
            this.updateLessonCompletionStatus();
            
            // Move to next lesson
            const nextLesson = this.getNextLesson();
            if (nextLesson) {
                setTimeout(() => {
                    this.loadLesson(nextLesson);
                }, 2000);
            } else {
                // Course completed
                this.handleCourseCompleted();
            }
            
        } catch (error) {
            console.error('Error marking lesson complete:', error);
        }
    }

    // Mark lesson as complete
    async markLessonComplete(lessonId) {
        const response = await fetch(`/api/lms/lessons/${lessonId}/complete`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('sapyyn_token') || sessionStorage.getItem('sapyyn_token')}`
            }
        });
        
        if (!response.ok) {
            throw new Error('Failed to mark lesson complete');
        }
        
        return response.json();
    }

    // Save lesson progress
    async saveLessonProgress(lessonId, currentTime) {
        try {
            await fetch(`/api/lms/lessons/${lessonId}/progress`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('sapyyn_token') || sessionStorage.getItem('sapyyn_token')}`
                },
                body: JSON.stringify({ currentTime })
            });
        } catch (error) {
            console.error('Error saving lesson progress:', error);
        }
    }

    // Get next lesson
    getNextLesson() {
        if (!this.currentCourse || !this.currentLesson) return null;
        
        const lessons = this.currentCourse.lessons;
        const currentIndex = lessons.findIndex(l => l._id === this.currentLesson._id);
        
        return currentIndex < lessons.length - 1 ? lessons[currentIndex + 1] : null;
    }

    // Handle course completed
    async handleCourseCompleted() {
        try {
            const response = await fetch(`/api/lms/courses/${this.currentCourse._id}/complete`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('sapyyn_token') || sessionStorage.getItem('sapyyn_token')}`
                }
            });
            
            if (response.ok) {
                const result = await response.json();
                this.showCourseCompletionModal(result);
            }
        } catch (error) {
            console.error('Error completing course:', error);
        }
    }

    // Show course completion modal
    showCourseCompletionModal(result) {
        // Implementation for showing completion celebration
        this.showToast('success', 'Congratulations! Course completed successfully!');
        
        // Show certificate if available
        if (result.certificateUrl) {
            const viewCertificateBtn = document.getElementById('viewCertificate');
            if (viewCertificateBtn) {
                viewCertificateBtn.style.display = 'block';
                viewCertificateBtn.onclick = () => {
                    window.open(result.certificateUrl, '_blank');
                };
            }
        }
    }

    // Load and save notes
    async loadLessonNotes(lessonId) {
        try {
            const response = await fetch(`/api/lms/lessons/${lessonId}/notes`);
            if (response.ok) {
                const notes = await response.json();
                const notesTextarea = document.getElementById('courseNotes');
                if (notesTextarea) {
                    notesTextarea.value = notes.content || '';
                }
            }
        } catch (error) {
            console.error('Error loading notes:', error);
        }
    }

    async saveNotes() {
        if (!this.currentLesson) return;
        
        const notesTextarea = document.getElementById('courseNotes');
        if (!notesTextarea) return;
        
        try {
            await fetch(`/api/lms/lessons/${this.currentLesson._id}/notes`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('sapyyn_token') || sessionStorage.getItem('sapyyn_token')}`
                },
                body: JSON.stringify({ content: notesTextarea.value })
            });
            
            this.showToast('success', 'Notes saved successfully');
        } catch (error) {
            console.error('Error saving notes:', error);
            this.showToast('error', 'Failed to save notes');
        }
    }

    // Utility functions
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    // Show toast notification
    showToast(type, message, duration = 5000) {
        // Create and show toast notification
        const toast = document.createElement('div');
        toast.className = `alert alert-${type === 'success' ? 'success' : 'danger'} alert-dismissible fade show position-fixed`;
        toast.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        toast.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(toast);
        
        setTimeout(() => {
            toast.remove();
        }, duration);
    }

    // Update progress display
    updateProgressDisplay() {
        // Update sidebar progress
        document.getElementById('overallProgress').textContent = this.progressData.overallProgress + '%';
        document.getElementById('overallProgressBar').style.width = this.progressData.overallProgress + '%';
    }
}

// Global functions
function continueLastCourse() {
    if (window.lmsPortal) {
        window.lmsPortal.showDashboard();
    }
}

function showAllCourses() {
    if (window.lmsPortal) {
        window.lmsPortal.showCatalog();
    }
}

function backToCatalog() {
    if (window.lmsPortal) {
        window.lmsPortal.showCatalog();
    }
}

function clearFilters() {
    document.getElementById('courseSearch').value = '';
    document.getElementById('difficultyFilter').value = '';
    document.getElementById('durationFilter').value = '';
    document.getElementById('sortFilter').value = 'popular';
    
    if (window.lmsPortal) {
        window.lmsPortal.loadAllCourses();
    }
}

function saveNotes() {
    if (window.lmsPortal) {
        window.lmsPortal.saveNotes();
    }
}

function logout() {
    localStorage.removeItem('sapyyn_token');
    sessionStorage.removeItem('sapyyn_token');
    window.location.href = '/portal';
}

// Initialize LMS Portal when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.lmsPortal = new LMSPortal();
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = LMSPortal;
}