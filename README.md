# Sapyyn Patient Referral System

A web-based patient referral management system designed for healthcare providers to efficiently manage and track patient referrals.

## Features

- **Patient Referral Submission**: Create new patient referrals with detailed information
- **Referral Management**: View and track all submitted referrals
- **File Upload System**: Upload and manage various document types including:
  - Medical reports
  - Insurance documents  
  - Experience documents
  - Qualification documents
  - Supporting documents
  - Profile pictures
  - Testimonial images
- **Multiple Urgency Levels**: Routine, Urgent, Emergency
- **Referral Types**: Specialist consultation, Diagnostic testing, Emergency care, Surgical consultation, Rehabilitation, Second opinion
- **Responsive Design**: Works on desktop and mobile devices

## Getting Started

### Prerequisites

- Node.js (version 14 or higher)
- npm (comes with Node.js)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/idaltu-1/sapyyn.git
   cd sapyyn
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm start
   ```

4. Open your browser and navigate to:
   ```
   http://localhost:3000
   ```

### Usage

1. **Creating a New Referral**:
   - Fill in patient information (name, ID)
   - Select referral type and urgency level
   - Add clinical notes
   - Optionally attach supporting documents
   - Click "Submit Referral"

2. **Viewing Referrals**:
   - Switch to the "View Referrals" tab
   - Click "Refresh" to load the latest referrals
   - Review patient details, referral types, and urgency levels

3. **File Upload**:
   - Use the "File Upload" tab for standalone file uploads
   - Select document type from dropdown
   - Choose file and upload

## Technical Details

- **Backend**: Node.js with Express
- **Frontend**: HTML5, CSS3, JavaScript (ES6+)
- **File Storage**: Local filesystem with organized naming convention
- **Data Storage**: JSON files (suitable for testing/development)

## File Structure

```
sapyyn/
├── server.js              # Express server
├── package.json           # Node.js dependencies
├── public/                # Frontend assets
│   ├── index.html        # Main application page
│   ├── styles.css        # Application styling
│   └── script.js         # Frontend JavaScript
├── patient-referral/     # File storage and data
└── README.md            # This file
```

## API Endpoints

- `GET /` - Serve main application page
- `POST /submit-referral` - Submit new patient referral
- `GET /referrals` - Retrieve all referrals
- `POST /upload` - Upload single file

## Development

To contribute to this project:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test the application thoroughly
5. Submit a pull request

## Security Considerations

This is a development/testing version. For production use, consider:

- Implementing proper authentication and authorization
- Using a secure database instead of JSON files
- Adding HTTPS encryption
- Implementing proper file validation and scanning
- Adding audit logging
- Following HIPAA compliance requirements for patient data

## License

MIT License - see LICENSE file for details
