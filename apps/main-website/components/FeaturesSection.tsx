'use client';

import React from 'react';
import {
  Box,
  Container,
  Typography,
  Grid,
  Card,
  CardContent,
  Avatar,
} from '@mui/material';
import { motion } from 'framer-motion';
import {
  QrCode2,
  Message,
  Security,
  Speed,
  CloudUpload,
  Analytics,
  Notifications,
  Integration,
} from '@mui/icons-material';

const FeaturesSection: React.FC = () => {
  const features = [
    {
      icon: <QrCode2 sx={{ fontSize: 32, color: 'white' }} />,
      title: 'QR Code & Digital Referrals',
      description: 'Instant patient referrals using QR codes, 6-digit codes, or text messages. No more paperwork or phone calls.',
    },
    {
      icon: <Message sx={{ fontSize: 32, color: 'white' }} />,
      title: 'Real-Time Communication',
      description: 'Secure messaging system between providers and patients with instant notifications and updates.',
    },
    {
      icon: <Security sx={{ fontSize: 32, color: 'white' }} />,
      title: 'HIPAA Compliant Security',
      description: 'Bank-level encryption and HIPAA compliance ensure patient data is always protected and secure.',
    },
    {
      icon: <Speed sx={{ fontSize: 32, color: 'white' }} />,
      title: 'Lightning Fast Processing',
      description: 'Referrals are processed instantly with automated workflows and real-time status updates.',
    },
    {
      icon: <CloudUpload sx={{ fontSize: 32, color: 'white' }} />,
      title: 'Document Management',
      description: 'Secure upload, storage, and sharing of medical documents, X-rays, and patient files.',
    },
    {
      icon: <Analytics sx={{ fontSize: 32, color: 'white' }} />,
      title: 'Analytics & Reporting',
      description: 'Comprehensive analytics dashboard with referral tracking, success rates, and performance metrics.',
    },
    {
      icon: <Notifications sx={{ fontSize: 32, color: 'white' }} />,
      title: 'Smart Notifications',
      description: 'Automated notifications via email, SMS, and push notifications to keep everyone informed.',
    },
    {
      icon: <Integration sx={{ fontSize: 32, color: 'white' }} />,
      title: 'Practice Management Integration',
      description: 'Seamless integration with popular practice management software and electronic health records.',
    },
  ];

  return (
    <Box sx={{ py: 10, backgroundColor: 'white' }}>
      <Container maxWidth="xl">
        <Box sx={{ textAlign: 'center', mb: 8 }}>
          <Typography
            variant="h2"
            sx={{
              fontSize: { xs: '2rem', md: '2.5rem' },
              fontWeight: 700,
              color: 'primary.main',
              mb: 2,
            }}
          >
            Powerful Features for Modern Healthcare
          </Typography>
          <Typography
            variant="h6"
            sx={{
              color: 'text.secondary',
              maxWidth: 600,
              mx: 'auto',
            }}
          >
            Everything you need to streamline patient referrals and improve care coordination
          </Typography>
        </Box>

        <Grid container spacing={4}>
          {features.map((feature, index) => (
            <Grid item xs={12} sm={6} md={3} key={index}>
              <motion.div
                initial={{ opacity: 0, y: 50 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: index * 0.1 }}
                viewport={{ once: true }}
              >
                <Card
                  sx={{
                    height: '100%',
                    p: 3,
                    boxShadow: '0 4px 20px rgba(0, 0, 0, 0.1)',
                    borderRadius: 3,
                    transition: 'all 0.3s ease',
                    '&:hover': {
                      transform: 'translateY(-10px)',
                      boxShadow: '0 20px 40px rgba(0, 0, 0, 0.15)',
                    },
                  }}
                >
                  <CardContent sx={{ p: 0 }}>
                    <Avatar
                      sx={{
                        width: 80,
                        height: 80,
                        background: 'linear-gradient(135deg, #010187 0%, #cb0c9f 100%)',
                        mb: 3,
                      }}
                    >
                      {feature.icon}
                    </Avatar>
                    <Typography
                      variant="h6"
                      sx={{
                        fontWeight: 600,
                        color: 'primary.main',
                        mb: 2,
                      }}
                    >
                      {feature.title}
                    </Typography>
                    <Typography
                      variant="body2"
                      sx={{
                        color: 'text.secondary',
                        lineHeight: 1.6,
                      }}
                    >
                      {feature.description}
                    </Typography>
                  </CardContent>
                </Card>
              </motion.div>
            </Grid>
          ))}
        </Grid>
      </Container>
    </Box>
  );
};

export default FeaturesSection;