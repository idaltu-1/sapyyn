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
  Rating,
} from '@mui/material';
import { motion } from 'framer-motion';
import { FormatQuote } from '@mui/icons-material';

const TestimonialsSection: React.FC = () => {
  const testimonials = [
    {
      name: 'Dr. Sarah Johnson',
      title: 'General Dentist',
      location: 'Austin, TX',
      rating: 5,
      comment: 'Sapyyn has revolutionized how I refer patients to specialists. The process is seamless, secure, and my patients love how easy it is to get connected with the right care.',
      avatar: '/images/testimonials/doctor1.jpg',
    },
    {
      name: 'Dr. Michael Chen',
      title: 'Oral Surgeon',
      location: 'San Francisco, CA',
      rating: 5,
      comment: 'As a specialist, I receive higher quality referrals through Sapyyn. The platform provides all the information I need upfront, making consultations more efficient.',
      avatar: '/images/testimonials/doctor2.jpg',
    },
    {
      name: 'Dr. Emily Rodriguez',
      title: 'Orthodontist',
      location: 'Miami, FL',
      rating: 5,
      comment: 'The real-time communication features have improved my patient relationships significantly. Parents can track their child\'s referral status and feel more involved in the process.',
      avatar: '/images/testimonials/doctor3.jpg',
    },
    {
      name: 'Jennifer Walsh',
      title: 'Patient',
      location: 'Denver, CO',
      rating: 5,
      comment: 'I was nervous about seeing a specialist, but Sapyyn made the entire process transparent and easy. I knew exactly what to expect and felt prepared for my appointment.',
      avatar: '/images/testimonials/patient1.jpg',
    },
    {
      name: 'Dr. Robert Kim',
      title: 'Periodontist',
      location: 'Seattle, WA',
      rating: 5,
      comment: 'The document sharing capabilities are fantastic. I can review X-rays and treatment notes before the patient arrives, allowing me to provide better care from day one.',
      avatar: '/images/testimonials/doctor4.jpg',
    },
    {
      name: 'Maria Gonzalez',
      title: 'Patient',
      location: 'Phoenix, AZ',
      rating: 5,
      comment: 'My dentist referred me through Sapyyn and I was able to schedule with a specialist the same day. The convenience and speed were incredible.',
      avatar: '/images/testimonials/patient2.jpg',
    },
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
            What Our Users Say
          </Typography>
          <Typography
            variant="h6"
            sx={{
              color: 'text.secondary',
              maxWidth: 600,
              mx: 'auto',
            }}
          >
            Join thousands of satisfied healthcare providers and patients who trust Sapyyn
          </Typography>
        </Box>

        <Grid container spacing={4}>
          {testimonials.map((testimonial, index) => (
            <Grid item xs={12} md={6} lg={4} key={index}>
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
                    position: 'relative',
                    '&:hover': {
                      transform: 'translateY(-5px)',
                      boxShadow: '0 15px 30px rgba(0, 0, 0, 0.15)',
                    },
                  }}
                >
                  <FormatQuote
                    sx={{
                      position: 'absolute',
                      top: 16,
                      right: 16,
                      fontSize: 40,
                      color: 'primary.light',
                      opacity: 0.3,
                    }}
                  />
                  
                  <CardContent sx={{ p: 0 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                      <Avatar
                        src={testimonial.avatar}
                        sx={{ width: 60, height: 60, mr: 2 }}
                      >
                        {testimonial.name.charAt(0)}
                      </Avatar>
                      <Box>
                        <Typography
                          variant="h6"
                          sx={{ fontWeight: 600, color: 'primary.main' }}
                        >
                          {testimonial.name}
                        </Typography>
                        <Typography variant="body2" sx={{ color: 'text.secondary' }}>
                          {testimonial.title}
                        </Typography>
                        <Typography variant="caption" sx={{ color: 'text.secondary' }}>
                          {testimonial.location}
                        </Typography>
                      </Box>
                    </Box>
                    
                    <Rating
                      value={testimonial.rating}
                      readOnly
                      sx={{ mb: 2 }}
                    />
                    
                    <Typography
                      variant="body2"
                      sx={{
                        color: 'text.secondary',
                        lineHeight: 1.6,
                        fontStyle: 'italic',
                      }}
                    >
                      "{testimonial.comment}"
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

export default TestimonialsSection;