'use client';

import React, { useState, useEffect } from 'react';
import {
  AppBar,
  Toolbar,
  Container,
  Typography,
  Button,
  Box,
  IconButton,
  Drawer,
  List,
  ListItem,
  ListItemText,
  useMediaQuery,
  useTheme,
} from '@mui/material';
import { Menu as MenuIcon, Close as CloseIcon } from '@mui/icons-material';
import Image from 'next/image';
import Link from 'next/link';

const Header: React.FC = () => {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };

  useEffect(() => {
    const handleScroll = () => {
      const isScrolled = window.scrollY > 10;
      setScrolled(isScrolled);
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const menuItems = [
    { label: 'Home', href: '/' },
    { label: 'Referrals', href: '/referrals' },
    { label: 'About', href: '/about' },
    { label: 'Pricing', href: '/pricing' },
    { label: 'Resources', href: '/resources' },
    { label: 'Contact', href: '/contact' },
  ];

  const drawer = (
    <Box onClick={handleDrawerToggle} sx={{ textAlign: 'center' }}>
      <Box sx={{ p: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Image src="/images/logo.png" alt="Sapyyn" width={120} height={40} />
        <IconButton>
          <CloseIcon />
        </IconButton>
      </Box>
      <List>
        {menuItems.map((item) => (
          <ListItem key={item.label} component={Link} href={item.href}>
            <ListItemText primary={item.label} />
          </ListItem>
        ))}
        <ListItem>
          <Button
            component={Link}
            href="https://portal.sapyyn.com/signup"
            variant="outlined"
            fullWidth
            sx={{ mr: 1 }}
          >
            Create Account
          </Button>
        </ListItem>
        <ListItem>
          <Button
            component={Link}
            href="https://portal.sapyyn.com/login"
            variant="contained"
            fullWidth
          >
            Login
          </Button>
        </ListItem>
      </List>
    </Box>
  );

  return (
    <>
      <AppBar
        position="fixed"
        sx={{
          backgroundColor: scrolled ? 'rgba(255, 255, 255, 0.95)' : 'transparent',
          backdropFilter: scrolled ? 'blur(10px)' : 'none',
          boxShadow: scrolled ? '0 2px 20px rgba(0, 0, 0, 0.1)' : 'none',
          transition: 'all 0.3s ease',
          color: scrolled ? 'primary.main' : 'white',
        }}
      >
        <Container maxWidth="xl">
          <Toolbar disableGutters>
            <Box sx={{ display: 'flex', alignItems: 'center', flexGrow: 1 }}>
              <Image 
                src="/images/logo.png" 
                alt="Sapyyn" 
                width={140} 
                height={45}
                style={{ cursor: 'pointer' }}
              />
            </Box>

            {isMobile ? (
              <IconButton
                color="inherit"
                aria-label="open drawer"
                edge="start"
                onClick={handleDrawerToggle}
              >
                <MenuIcon />
              </IconButton>
            ) : (
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                {menuItems.map((item) => (
                  <Link key={item.label} href={item.href}>
                    <Typography
                      variant="body1"
                      sx={{
                        cursor: 'pointer',
                        fontWeight: 500,
                        '&:hover': {
                          color: 'secondary.main',
                        },
                        transition: 'color 0.2s ease',
                      }}
                    >
                      {item.label}
                    </Typography>
                  </Link>
                ))}
                <Button
                  component={Link}
                  href="https://portal.sapyyn.com/signup"
                  variant="outlined"
                  sx={{ 
                    ml: 2,
                    borderColor: scrolled ? 'primary.main' : 'white',
                    color: scrolled ? 'primary.main' : 'white',
                    '&:hover': {
                      borderColor: 'secondary.main',
                      backgroundColor: 'secondary.main',
                      color: 'white',
                    }
                  }}
                >
                  Create Account
                </Button>
                <Button
                  component={Link}
                  href="https://portal.sapyyn.com/login"
                  variant="contained"
                  sx={{
                    background: 'linear-gradient(135deg, #cb0c9f 0%, #010187 100%)',
                    '&:hover': {
                      background: 'linear-gradient(135deg, #ad0a87 0%, #000066 100%)',
                      transform: 'translateY(-1px)',
                    },
                    transition: 'all 0.2s ease',
                  }}
                >
                  Login
                </Button>
              </Box>
            )}
          </Toolbar>
        </Container>
      </AppBar>

      <Drawer
        variant="temporary"
        open={mobileOpen}
        onClose={handleDrawerToggle}
        ModalProps={{
          keepMounted: true,
        }}
        sx={{
          display: { xs: 'block', md: 'none' },
          '& .MuiDrawer-paper': { boxSizing: 'border-box', width: 280 },
        }}
      >
        {drawer}
      </Drawer>
    </>
  );
};

export default Header;