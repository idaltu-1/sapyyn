export const config = {
  app: {
    name: 'Sapyyn Patient Referral System',
    version: '1.0.0',
    environment: process.env.NODE_ENV || 'development',
    port: process.env.PORT || 3000,
  },
  
  aws: {
    region: process.env.AWS_REGION || 'us-east-2',
    s3: {
      bucketName: process.env.S3_BUCKET_NAME || 'sapyyn',
      maxFileSize: 10 * 1024 * 1024, // 10MB
      allowedFileTypes: [
        'application/pdf',
        'image/jpeg',
        'image/png',
        'image/webp',
      ],
    },
  },
  
  security: {
    jwtSecret: process.env.JWT_SECRET,
    sessionSecret: process.env.SESSION_SECRET,
    bcryptRounds: 10,
  },
  
  features: {
    enableQRCodes: process.env.ENABLE_QR_CODES === 'true',
    enableNotifications: process.env.ENABLE_NOTIFICATIONS === 'true',
  },
  
  fileCategories: {
    medical: 'Medical Reports',
    insurance: 'Insurance Documents',
    qualification: 'Qualification Documents',
    experience: 'Experience Documents',
    supporting: 'Supporting Documents',
    profilePictures: 'Profile Pictures',
    qrCodes: 'QR Codes',
    messageAttachments: 'Message Attachments',
    testimonials: 'Testimonials',
    broadcast: 'Broadcast Files',
    uploaded: 'General Uploads',
  },
};