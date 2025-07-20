'use client';

import React, { useState } from 'react';
import {
  Box,
  Container,
  Typography,
  Grid,
  Card,
  CardContent,
  TextField,
  Button,
  Alert,
} from '@mui/material';
import { motion } from 'framer-motion';
import { Email, Phone, LocationOn, Send } from '@mui/icons-material';
import { useForm } from 'react-hook-form';
import { toast } from 'react-toastify';

interface ContactFormData {
  name: string;
  email: string;
  subject: string;
  message: string;
}

const ContactSection: React.FC = () => {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { register, handleSubmit, reset, formState: { errors } } = useForm<ContactFormData>();

  const onSubmit = async (data: ContactFormData) => {
    setIsSubmitting(true);
    try {
      const response = await fetch('/api/contact', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      });

      if (response.ok) {
        toast.success('Message sent successfully! We\'ll get back to you soon.');
        reset();
      } else {
        toast.error('Failed to send message. Please try again.');
      }
    } catch (error) {
      toast.error('Failed to send message. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const contactInfo = [
    {
      icon: <Email sx={{ fontSize: 32, color: 'primary.main' }} />,
      title: 'Email Us',
      details: 'contact@sapyyn.com',
      description: 'Send us an email and we\'ll respond within 24 hours',
    },
    {
      icon: <Phone sx={{ fontSize: 32, color: 'primary.main' }} />,
      title: 'Call Us',
      details: '1-800-SAPYYN1',
      description: 'Mon-Fri 9AM-6PM EST',
    },
    {
      icon: <LocationOn sx={{ fontSize: 32, color: 'primary.main' }} />,
      title: 'Visit Us',
      details: 'Nationwide Coverage',
      description: 'Serving healthcare providers across the United States',
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
            Get in Touch
          </Typography>
          <Typography
            variant="h6"
            sx={{
              color: 'text.secondary',
              maxWidth: 600,
              mx: 'auto',
            }}
          >
            Ready to streamline your patient referrals? Contact us today to learn more about Sapyyn
          </Typography>
        </Box>

        <Grid container spacing={6}>
          {/* Contact Information */}
          <Grid item xs={12} md={5}>
            <Box sx={{ mb: 4 }}>
              <Typography
                variant="h4"
                sx={{
                  fontWeight: 600,
                  color: 'primary.main',
                  mb: 3,
                }}
              >
                Let's Connect
              </Typography>
              <Typography
                variant="body1"
                sx={{
                  color: 'text.secondary',
                  mb: 4,
                  lineHeight: 1.6,
                }}
              >
                Whether you're a healthcare provider looking to streamline referrals or a patient 
                seeking better care coordination, we're here to help. Reach out to learn how 
                Sapyyn can transform your healthcare experience.
              </Typography>
            </Box>

            <Grid container spacing={3}>
              {contactInfo.map((info, index) => (
                <Grid item xs={12} key={index}>
                  <motion.div
                    initial={{ opacity: 0, x: -50 }}
                    whileInView={{ opacity: 1, x: 0 }}
                    transition={{ duration: 0.6, delay: index * 0.1 }}
                    viewport={{ once: true }}
                  >
                    <Card
                      sx={{
                        p: 3,
                        boxShadow: '0 2px 10px rgba(0, 0, 0, 0.05)',
                        borderRadius: 2,
                        transition: 'all 0.3s ease',
                        '&:hover': {
                          boxShadow: '0 4px 20px rgba(0, 0, 0, 0.1)',
                        },
                      }}
                    >
                      <Box sx={{ display: 'flex', alignItems: 'flex-start' }}>
                        <Box sx={{ mr: 3 }}>
                          {info.icon}
                        </Box>
                        <Box>
                          <Typography
                            variant="h6"
                            sx={{ fontWeight: 600, color: 'primary.main', mb: 1 }}
                          >
                            {info.title}
                          </Typography>
                          <Typography
                            variant="subtitle1"
                            sx={{ fontWeight: 500, mb: 1 }}
                          >
                            {info.details}
                          </Typography>
                          <Typography
                            variant="body2"
                            sx={{ color: 'text.secondary' }}
                          >
                            {info.description}
                          </Typography>
                        </Box>
                      </Box>
                    </Card>
                  </motion.div>
                </Grid>
              ))}
            </Grid>
          </Grid>

          {/* Contact Form */}
          <Grid item xs={12} md={7}>
            <motion.div
              initial={{ opacity: 0, x: 50 }}
              whileInView={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.6 }}
              viewport={{ once: true }}
            >
              <Card
                sx={{
                  p: 4,
                  boxShadow: '0 4px 20px rgba(0, 0, 0, 0.1)',
                  borderRadius: 3,
                }}
              >
                <Typography
                  variant="h5"
                  sx={{
                    fontWeight: 600,
                    color: 'primary.main',
                    mb: 3,
                  }}
                >
                  Send us a Message
                </Typography>

                <Box component="form" onSubmit={handleSubmit(onSubmit)}>
                  <Grid container spacing={3}>
                    <Grid item xs={12} sm={6}>
                      <TextField
                        fullWidth
                        label="Full Name"
                        variant="outlined"
                        {...register('name', { required: 'Name is required' })}
                        error={!!errors.name}
                        helperText={errors.name?.message}
                      />
                    </Grid>
                    <Grid item xs={12} sm={6}>
                      <TextField
                        fullWidth
                        label="Email Address"
                        type="email"
                        variant="outlined"
                        {...register('email', {
                          required: 'Email is required',
                          pattern: {
                            value: /^\S+@\S+$/i,
                            message: 'Invalid email address',
                          },
                        })}
                        error={!!errors.email}
                        helperText={errors.email?.message}
                      />
                    </Grid>
                    <Grid item xs={12}>
                      <TextField
                        fullWidth
                        label="Subject"
                        variant="outlined"
                        {...register('subject', { required: 'Subject is required' })}
                        error={!!errors.subject}
                        helperText={errors.subject?.message}
                      />
                    </Grid>
                    <Grid item xs={12}>
                      <TextField
                        fullWidth
                        label="Message"
                        multiline
                        rows={6}
                        variant="outlined"
                        {...register('message', { required: 'Message is required' })}
                        error={!!errors.message}
                        helperText={errors.message?.message}
                      />
                    </Grid>
                    <Grid item xs={12}>
                      <Button
                        type="submit"
                        variant="contained"
                        size="large"
                        disabled={isSubmitting}
                        startIcon={<Send />}
                        sx={{
                          background: 'linear-gradient(135deg, #010187 0%, #cb0c9f 100%)',
                          px: 4,
                          py: 1.5,
                          '&:hover': {
                            background: 'linear-gradient(135deg, #000066 0%, #ad0a87 100%)',
                          },
                        }}
                      >
                        {isSubmitting ? 'Sending...' : 'Send Message'}
                      </Button>
                    </Grid>
                  </Grid>
                </Box>
              </Card>
            </motion.div>
          </Grid>
        </Grid>
      </Container>
    </Box>
  );
};

export default ContactSection;