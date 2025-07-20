const express = require('express');
const multer = require('multer');
const fetch = require('node-fetch');
const cors = require('cors');

// Configure multer to keep file data in memory. In production you should store
// files in a cloud bucket (e.g. S3, Google Cloud Storage) and save the
// resulting URL instead of a dummy placeholder.
const upload = multer({ storage: multer.memoryStorage() });

const app = express();
app.use(cors());
app.use(express.json());

// Serve static assets from multiple directories
// This allows access to API pages in public/, main site files in root, and assets
app.use(express.static('public'));
app.use(express.static('.'));
app.use('/css', express.static('css'));
app.use('/js', express.static('js'));
app.use('/images', express.static('images'));
app.use('/static', express.static('static'));

// Environment variables for Stackby API. The uploads and referrals tables
// should be defined in your Stackby base with the appropriate columns.
const {
  STACKBY_UPLOADS_API_URL,
  STACKBY_REFERRALS_API_URL,
  STACKBY_API_KEY
} = process.env;

// NOTE: For demonstration purposes the USERS array stores a single valid
// credential. In a real application you would integrate with a proper
// authentication provider or database and hash passwords.
const USERS = [
  { email: 'demo@example.com', password: 'secret123' }
];

/**
 * POST /api/login
 * Accepts JSON with `email` and `password` and returns a simple success
 * message if the credentials match the in‑memory USERS list. Otherwise
 * responds with 401 Unauthorized. This endpoint does NOT set a session
 * cookie or JWT – it simply demonstrates how to validate a login request.
 */
app.post('/api/login', (req, res) => {
  const { email, password } = req.body || {};
  const matched = USERS.find(
    (user) => user.email === email && user.password === password
  );
  if (!matched) {
    return res.status(401).json({ error: 'Invalid credentials' });
  }
  return res.status(200).json({ message: 'Login successful' });
});

/**
 * POST /api/upload
 * Handles file uploads plus metadata from the upload page. Saves file
 * metadata to Stackby via the uploads table. The file itself is not
 * persisted and is discarded after the request completes. Configure
 * STACKBY_UPLOADS_API_URL and STACKBY_API_KEY in your environment.
 */
app.post('/api/upload', upload.single('file'), async (req, res) => {
  const { file } = req;
  const { fileName, category, notes } = req.body;
  if (!file || !fileName) {
    return res.status(400).json({ error: 'File and fileName are required.' });
  }
  // Dummy URL; replace with the URL of the stored file in real deployments.
  const fileUrl = `https://example.com/uploads/${encodeURIComponent(
    file.originalname
  )}`;
  const payload = {
    data: [
      {
        file_name: fileName,
        file_url: fileUrl,
        uploaded_date: new Date().toISOString(),
        category,
        notes
      }
    ]
  };
  try {
    const response = await fetch(STACKBY_UPLOADS_API_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'api-key': STACKBY_API_KEY
      },
      body: JSON.stringify(payload)
    });
    if (!response.ok) {
      const text = await response.text();
      console.error('Stackby upload error:', text);
      return res.status(500).json({ error: 'Failed to write to Stackby' });
    }
    return res.status(200).json({ message: 'Upload successful' });
  } catch (err) {
    console.error(err);
    return res.status(500).json({ error: 'Server error' });
  }
});

/**
 * POST /api/referral
 * Accepts a referral form submission. The payload may include an optional
 * attachment. It writes the referral data to a separate referrals table
 * in Stackby. The referral form fields should include `patientName`,
 * `contact`, `procedureType`, and `notes`. If a file is included, its
 * dummy URL is saved in the `file_url` column; replace with real storage
 * logic for production use.
 */
app.post('/api/referral', upload.single('file'), async (req, res) => {
  const { file } = req;
  const { patientName, contact, procedureType, notes } = req.body;
  if (!patientName || !contact || !procedureType) {
    return res
      .status(400)
      .json({ error: 'Patient name, contact and procedure type are required.' });
  }
  // Dummy file URL; replace with real storage and path in production.
  const fileUrl = file
    ? `https://example.com/referrals/${encodeURIComponent(file.originalname)}`
    : '';
  const payload = {
    data: [
      {
        patient_name: patientName,
        contact,
        procedure_type: procedureType,
        file_url: fileUrl,
        notes,
        submitted_date: new Date().toISOString()
      }
    ]
  };
  try {
    const response = await fetch(STACKBY_REFERRALS_API_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'api-key': STACKBY_API_KEY
      },
      body: JSON.stringify(payload)
    });
    if (!response.ok) {
      const text = await response.text();
      console.error('Stackby referral error:', text);
      return res.status(500).json({ error: 'Failed to write to Stackby' });
    }
    return res.status(200).json({ message: 'Referral submitted' });
  } catch (err) {
    console.error(err);
    return res.status(500).json({ error: 'Server error' });
  }
});

const port = process.env.PORT || 3000;
app.listen(port, () => {
  console.log(`Server running on port ${port}`);
});