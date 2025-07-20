'use client';

import React from 'react';
import {
  Box,
  Container,
  Typography,
  Grid,
  List,
  ListItem,
  ListItemText,
  IconButton,
  Divider,
} from '@mui/material';
import {
  Facebook,
  Twitter,
  Instagram,
  LinkedIn,
  Email,
  Phone,
} from '@mui/icons-material';
import Image from 'next/image';
import Link from 'next/link';

const Footer: React.FC = () => {
  const quickLinks = [
    { label: 'Case Studies', href: '/casestudies' },
    { label: 'Tutorials', href: '/tutorials' },
    { label: 'How-To Guides', href: '/howtoguides' },
    { label: 'Loyalty Rewards', href: '/loyaltyrewards' },
    { label: 'HIPAA Compliance', href: '/hipaa' },
    { label: 'Privacy Terms', href: '/privacy' },
    { label: 'FAQ', href: '/faq' },
  ];

  const socialLinks = [
    { icon: <Facebook />, href: '#', label: 'Facebook' },
    { icon: <Twitter />, href: '#', label: 'Twitter' },
    { icon: <Instagram />, href: '#', label: 'Instagram' },
    { icon: <LinkedIn />, href: '#', label: 'LinkedIn' },
  ];

  return (
    <Box
      component="footer"
      sx={{
        backgroundColor: '#1a1a1a',
        color: 'white',
        pt: 8,
        pb: 3,
      }}
    >
      <Container maxWidth="xl">
        <Grid container spacing={6}>
          {/* Company Info */}
          <Grid item xs={12} md={4}>
            <Box sx={{ mb: 3 }}>
              <Image
                src="/images/logo-white.png"
                alt="Sapyyn"
                width={150}
                height={50}
                style={{ marginBottom: '20px' }}
              />
            </Box>
            <Typography
              variant="h6"
              sx={{
                fontWeight: 600,
                mb: 2,
                color: 'white',
              }}
            >
              Bridging the Gap Between Providers and Patients Nationwide
            </Typography>
            <Typography
              variant="body2"
              sx={{
                color: '#ccc',
                lineHeight: 1.6,
                mb: 3,
              }}
            >
              Our mission is to facilitate seamless connections between dental providers 
              and patients across the country. With our easy-to-use referral system, 
              you can ensure your patients receive timely and expert care, no matter where they are.
            </Typography>
          </Grid>

          {/* Quick Links */}
          <Grid item xs={12} md={4}>
            <Typography
              variant="h6"
              sx={{
                fontWeight: 600,
                mb: 3,
                color: 'white',
              }}
            >
              Quick Links
            </Typography>
            <List sx={{ p: 0 }}>
              {quickLinks.map((link, index) => (
                <ListItem key={index} sx={{ p: 0, mb: 1 }}>
                  <Link href={link.href} style={{ textDecoration: 'none' }}>
                    <Typography
                      variant="body2"
                      sx={{
                        color: '#ccc',
                        cursor: 'pointer',
                        transition: 'color 0.3s ease',
                        '&:hover': {
                          color: '#cb0c9f',
                        },
                      }}
                    >
                      {link.label}
                    </Typography>
                  </Link>
                </ListItem>
              ))}
            </List>
          </Grid>

          {/* Contact Info */}
          <Grid item xs={12} md={4}>
            <Typography
              variant="h6"
              sx={{
                fontWeight: 600,
                mb: 3,
                color: 'white',
              }}
            >
              Contact Us
            </Typography>
            
            <Box sx={{ mb: 3 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Email sx={{ mr: 2, color: '#cb0c9f' }} />
                <Link href="mailto:contact@sapyyn.com" style={{ textDecoration: 'none' }}>
                  <Typography
                    variant="body2"
                    sx={{
                      color: '#ccc',
                      cursor: 'pointer',
                      '&:hover': {
                        color: '#cb0c9f',
                      },
                    }}
                  >
                    contact@sapyyn.com
                  </Typography>
                </Link>
              </Box>
              
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                <Phone sx={{ mr: 2, color: '#cb0c9f' }} />
                <Typography variant="body2" sx={{ color: '#ccc' }}>
                  1-800-SAPYYN1
                </Typography>
              </Box>
            </Box>

            <Typography
              variant="h6"
              sx={{
                fontWeight: 600,
                mb: 2,
                color: 'white',
              }}
            >
              Follow Us
            </Typography>
            <Box sx={{ display: 'flex', gap: 1 }}>
              {socialLinks.map((social, index) => (
                <IconButton
                  key={index}
                  component="a"
                  href={social.href}
                  target="_blank"
                  rel="noopener noreferrer"
                  sx={{
                    backgroundColor: '#333',
                    color: '#ccc',
                    '&:hover': {
                      backgroundColor: '#cb0c9f',
                      color: 'white',
                      transform: 'translateY(-3px)',
                    },
                    transition: 'all 0.3s ease',
                  }}
                  aria-label={social.label}
                >
                  {social.icon}
                </IconButton>
              ))}
            </Box>
          </Grid>
        </Grid>

        <Divider sx={{ my: 4, borderColor: '#333' }} />

        {/* Bottom Footer */}
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} md={8}>
            <Typography variant="body2" sx={{ color: '#ccc' }}>
              Copyright © {new Date().getFullYear()} | Powered by Sapyyn | All Rights Reserved
            </Typography>
          </Grid>
          
          <Grid item xs={12} md={4}>
            <Box sx={{ display: 'flex', justifyContent: { xs: 'flex-start', md: 'flex-end' }, gap: 3 }}>
              <Link href="/privacy" style={{ textDecoration: 'none' }}>
                <Typography
                  variant="body2"
                  sx={{
                    color: '#ccc',
                    cursor: 'pointer',
                    '&:hover': {
                      color: '#cb0c9f',
                    },
                  }}
                >
                  Privacy Policy
                </Typography>
              </Link>
              <Link href="/terms" style={{ textDecoration: 'none' }}>
                <Typography
                  variant="body2"
                  sx={{
                    color: '#ccc',
                    cursor: 'pointer',
                    '&:hover': {
                      color: '#cb0c9f',
                    },
                  }}
                >
                  Terms of Service
                </Typography>
              </Link>
              <Link href="/sitemap" style={{ textDecoration: 'none' }}>
                <Typography
                  variant="body2"
                  sx={{
                    color: '#ccc',
                    cursor: 'pointer',
                    '&:hover': {
                      color: '#cb0c9f',
                    },
                  }}
                >
                  Sitemap
                </Typography>
              </Link>
            </Box>
          </Grid>
        </Grid>
      </Container>
    </Box>
  );
};

export default Footer;