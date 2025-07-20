'use client';

import React from 'react';
import {
  Box,
  Container,
  Typography,
  Grid,
  Card,
  CardContent,
} from '@mui/material';
import { motion } from 'framer-motion';
import { People, LocalHospital, BusinessCenter, EmojiEvents } from '@mui/icons-material';

const StatsSection: React.FC = () => {
  const stats = [
    {
      icon: <People sx={{ fontSize: 48, color: 'primary.main' }} />,
      number: '500+',
      label: 'Doctors',
      description: 'Trusted healthcare providers'
    },
    {
      icon: <LocalHospital sx={{ fontSize: 48, color: 'primary.main' }} />,
      number: '720',
      label: 'Clinics',
      description: 'Partner medical facilities'
    },
    {
      icon: <BusinessCenter sx={{ fontSize: 48, color: 'primary.main' }} />,
      number: '14,500',
      label: 'Patients',
      description: 'Successfully referred patients'
    },
    {
      icon: <EmojiEvents sx={{ fontSize: 48, color: 'primary.main' }} />,
      number: '9',
      label: 'Awards',
      description: 'Industry recognitions'
    }
  ];

  return (
    <Box sx={{ py: 10, backgroundColor: '#f8f9fa' }}>
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
            Trusted by Healthcare Professionals Nationwide
          </Typography>
          <Typography
            variant="h6"
            sx={{
              color: 'text.secondary',
              maxWidth: 600,
              mx: 'auto',
            }}
          >
            Join thousands of healthcare providers who trust Sapyyn for seamless patient referrals
          </Typography>
        </Box>

        <Grid container spacing={4}>
          {stats.map((stat, index) => (
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
                    textAlign: 'center',
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
                  <CardContent>
                    <Box sx={{ mb: 2 }}>
                      {stat.icon}
                    </Box>
                    <Typography
                      variant="h2"
                      sx={{
                        fontSize: '3rem',
                        fontWeight: 700,
                        background: 'linear-gradient(135deg, #010187 0%, #cb0c9f 100%)',
                        WebkitBackgroundClip: 'text',
                        WebkitTextFillColor: 'transparent',
                        backgroundClip: 'text',
                        mb: 1,
                      }}
                    >
                      {stat.number}
                    </Typography>
                    <Typography
                      variant="h5"
                      sx={{
                        fontWeight: 600,
                        color: 'primary.main',
                        mb: 1,
                      }}
                    >
                      {stat.label}
                    </Typography>
                    <Typography
                      variant="body2"
                      sx={{
                        color: 'text.secondary',
                      }}
                    >
                      {stat.description}
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

export default StatsSection;