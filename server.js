const express = require('express');
const multer = require('multer');
const path = require('path');
const fs = require('fs');
const cors = require('cors');

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(express.static('public'));

// Ensure upload directory exists
const uploadDir = path.join(__dirname, 'patient-referral');
if (!fs.existsSync(uploadDir)) {
    fs.mkdirSync(uploadDir, { recursive: true });
}

// Configure multer for file uploads
const storage = multer.diskStorage({
    destination: function (req, file, cb) {
        cb(null, uploadDir);
    },
    filename: function (req, file, cb) {
        const fileType = req.body.fileType || 'general';
        const timestamp = Date.now();
        const filename = `fileType-${fileType}=fileName-${file.originalname.replace(/\s+/g, '_')}_${timestamp}${path.extname(file.originalname)}`;
        cb(null, filename);
    }
});

const upload = multer({ 
    storage: storage,
    limits: {
        fileSize: 10 * 1024 * 1024 // 10MB limit
    },
    fileFilter: function (req, file, cb) {
        // Allow common document and image types
        const allowedTypes = /jpeg|jpg|png|gif|pdf|doc|docx/;
        const extname = allowedTypes.test(path.extname(file.originalname).toLowerCase());
        const mimetype = allowedTypes.test(file.mimetype);
        
        if (mimetype && extname) {
            return cb(null, true);
        } else {
            cb(new Error('Only images and documents are allowed'));
        }
    }
});

// Routes
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

app.post('/upload', upload.single('file'), (req, res) => {
    try {
        if (!req.file) {
            return res.status(400).json({ error: 'No file uploaded' });
        }
        
        res.json({
            message: 'File uploaded successfully',
            filename: req.file.filename,
            fileType: req.body.fileType,
            size: req.file.size
        });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

app.post('/submit-referral', upload.array('documents', 10), (req, res) => {
    try {
        const referralData = {
            patientName: req.body.patientName,
            patientId: req.body.patientId,
            referralType: req.body.referralType,
            urgency: req.body.urgency,
            notes: req.body.notes,
            uploadedFiles: req.files ? req.files.map(file => file.filename) : [],
            timestamp: new Date().toISOString()
        };
        
        // Save referral data (in a real app, this would go to a database)
        const referralsFile = path.join(__dirname, 'patient-referral', 'referrals.json');
        let referrals = [];
        
        if (fs.existsSync(referralsFile)) {
            const data = fs.readFileSync(referralsFile, 'utf8');
            referrals = JSON.parse(data);
        }
        
        referrals.push(referralData);
        fs.writeFileSync(referralsFile, JSON.stringify(referrals, null, 2));
        
        res.json({
            message: 'Referral submitted successfully',
            referralId: referrals.length,
            data: referralData
        });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

app.get('/referrals', (req, res) => {
    try {
        const referralsFile = path.join(__dirname, 'patient-referral', 'referrals.json');
        if (fs.existsSync(referralsFile)) {
            const data = fs.readFileSync(referralsFile, 'utf8');
            const referrals = JSON.parse(data);
            res.json(referrals);
        } else {
            res.json([]);
        }
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Error handling middleware
app.use((error, req, res, next) => {
    if (error instanceof multer.MulterError) {
        if (error.code === 'LIMIT_FILE_SIZE') {
            return res.status(400).json({ error: 'File too large' });
        }
    }
    res.status(500).json({ error: error.message });
});

app.listen(PORT, () => {
    console.log(`Sapyyn Patient Referral System running on http://localhost:${PORT}`);
    console.log('Ready for testing!');
});