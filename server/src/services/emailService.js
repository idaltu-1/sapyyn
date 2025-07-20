import nodemailer from 'nodemailer';

const transporter = nodemailer.createTransporter({
  host: process.env.SMTP_HOST,
  port: process.env.SMTP_PORT,
  secure: false, // true for 465, false for other ports
  auth: {
    user: process.env.SMTP_USER,
    pass: process.env.SMTP_PASS,
  },
});

export const sendEmail = async (to, subject, text, html = null) => {
  try {
    const mailOptions = {
      from: `"Sapyyn" <${process.env.SMTP_USER}>`,
      to,
      subject,
      text,
      html: html || text,
    };

    const info = await transporter.sendMail(mailOptions);
    console.log('Email sent:', info.messageId);
    return info;
  } catch (error) {
    console.error('Email error:', error);
    throw error;
  }
};

export const sendWelcomeEmail = async (user) => {
  const subject = 'Welcome to Sapyyn!';
  const text = `Hello ${user.firstName},\n\nWelcome to Sapyyn! Your account has been created successfully.\n\nBest regards,\nThe Sapyyn Team`;
  
  return sendEmail(user.email, subject, text);
};

export const sendReferralNotification = async (referral, recipient) => {
  const subject = 'New Patient Referral Received';
  const text = `Hello ${recipient.firstName},\n\nYou have received a new patient referral #${referral.referralNumber}.\n\nPlease log in to your portal to review the details.\n\nBest regards,\nThe Sapyyn Team`;
  
  return sendEmail(recipient.email, subject, text);
};