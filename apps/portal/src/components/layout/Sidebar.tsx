import React from 'react';
import {
  Box,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Divider,
  Typography,
  Chip,
} from '@mui/material';
import {
  Dashboard,
  Assignment,
  FolderOpen,
  Message,
  Person,
  CardGiftcard,
  Add,
  Group,
  Analytics,
  Settings,
  Business,
} from '@mui/icons-material';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';

interface SidebarProps {
  onMobileClose?: () => void;
}

const Sidebar: React.FC<SidebarProps> = ({ onMobileClose }) => {
  const location = useLocation();
  const navigate = useNavigate();
  const { user } = useAuth();

  const handleNavigation = (path: string) => {
    navigate(path);
    if (onMobileClose) {
      onMobileClose();
    }
  };

  const getMenuItems = () => {
    const baseItems = [
      { text: 'Dashboard', icon: <Dashboard />, path: '/dashboard' },
      { text: 'Referrals', icon: <Assignment />, path: '/referrals' },
      { text: 'Documents', icon: <FolderOpen />, path: '/documents' },
      { text: 'Messages', icon: <Message />, path: '/messages' },
      { text: 'Profile', icon: <Person />, path: '/profile' },
    ];

    const roleSpecificItems = [];

    if (user?.role === 'PATIENT') {
      roleSpecificItems.push(
        { text: 'My Referrals', icon: <Assignment />, path: '/referrals' },
        { text: 'Rewards', icon: <CardGiftcard />, path: '/rewards' }
      );
    }

    if (user?.role === 'DENTIST' || user?.role === 'SPECIALIST') {
      roleSpecificItems.push(
        { text: 'Create Referral', icon: <Add />, path: '/referrals/create' },
        { text: 'My Network', icon: <Group />, path: '/network' },
        { text: 'Analytics', icon: <Analytics />, path: '/analytics' },
        { text: 'Rewards', icon: <CardGiftcard />, path: '/rewards' }
      );
    }

    if (user?.role === 'DENTIST_ADMIN' || user?.role === 'SPECIALIST_ADMIN' || user?.role === 'SUPER_ADMIN') {
      roleSpecificItems.push(
        { text: 'User Management', icon: <Group />, path: '/admin/users' },
        { text: 'Practice Management', icon: <Business />, path: '/admin/practices' },
        { text: 'Analytics', icon: <Analytics />, path: '/admin/analytics' },
        { text: 'System Settings', icon: <Settings />, path: '/admin/settings' }
      );
    }

    return [...baseItems, ...roleSpecificItems];
  };

  const menuItems = getMenuItems();

  return (
    <Box>
      {/* Logo */}
      <Box sx={{ p: 3, textAlign: 'center' }}>
        <img
          src="/images/logo.png"
          alt="Sapyyn"
          style={{ height: 40, marginBottom: 16 }}
        />
        <Typography variant="subtitle2" color="text.secondary">
          Healthcare Referral Platform
        </Typography>
      </Box>

      <Divider />

      {/* User Info */}
      <Box sx={{ p: 2 }}>
        <Box
          sx={{
            p: 2,
            backgroundColor: 'primary.main',
            borderRadius: 2,
            color: 'white',
            textAlign: 'center',
          }}
        >
          <Typography variant="subtitle1" fontWeight="bold">
            {user?.firstName} {user?.lastName}
          </Typography>
          <Chip
            label={user?.role?.replace('_', ' ')}
            size="small"
            sx={{
              backgroundColor: 'rgba(255, 255, 255, 0.2)',
              color: 'white',
              mt: 1,
            }}
          />
          {(user?.role === 'DENTIST' || user?.role === 'SPECIALIST') && user?.profile && (
            <Typography variant="caption" display="block" sx={{ mt: 1 }}>
              Code: {user.profile.dentistCode || user.profile.specialistCode}
            </Typography>
          )}
        </Box>
      </Box>

      <Divider />

      {/* Navigation Menu */}
      <List sx={{ px: 1 }}>
        {menuItems.map((item) => (
          <ListItem key={item.text} disablePadding sx={{ mb: 0.5 }}>
            <ListItemButton
              onClick={() => handleNavigation(item.path)}
              selected={location.pathname === item.path}
              sx={{
                borderRadius: 2,
                '&.Mui-selected': {
                  backgroundColor: 'primary.main',
                  color: 'white',
                  '&:hover': {
                    backgroundColor: 'primary.dark',
                  },
                  '& .MuiListItemIcon-root': {
                    color: 'white',
                  },
                },
                '&:hover': {
                  backgroundColor: 'primary.light',
                  color: 'white',
                  '& .MuiListItemIcon-root': {
                    color: 'white',
                  },
                },
              }}
            >
              <ListItemIcon
                sx={{
                  minWidth: 40,
                  color: location.pathname === item.path ? 'white' : 'text.secondary',
                }}
              >
                {item.icon}
              </ListItemIcon>
              <ListItemText
                primary={item.text}
                primaryTypographyProps={{
                  fontSize: '0.875rem',
                  fontWeight: location.pathname === item.path ? 600 : 400,
                }}
              />
            </ListItemButton>
          </ListItem>
        ))}
      </List>

      <Divider sx={{ mt: 2 }} />

      {/* Quick Actions */}
      {(user?.role === 'DENTIST' || user?.role === 'SPECIALIST') && (
        <Box sx={{ p: 2 }}>
          <Typography variant="caption" color="text.secondary" sx={{ mb: 1, display: 'block' }}>
            QUICK ACTIONS
          </Typography>
          <ListItemButton
            onClick={() => handleNavigation('/referrals/create')}
            sx={{
              borderRadius: 2,
              backgroundColor: 'secondary.main',
              color: 'white',
              '&:hover': {
                backgroundColor: 'secondary.dark',
              },
            }}
          >
            <ListItemIcon sx={{ minWidth: 40, color: 'white' }}>
              <Add />
            </ListItemIcon>
            <ListItemText
              primary="New Referral"
              primaryTypographyProps={{
                fontSize: '0.875rem',
                fontWeight: 600,
              }}
            />
          </ListItemButton>
        </Box>
      )}

      {/* Footer */}
      <Box sx={{ position: 'absolute', bottom: 0, left: 0, right: 0, p: 2 }}>
        <Typography variant="caption" color="text.secondary" align="center" display="block">
          © 2024 Sapyyn. All rights reserved.
        </Typography>
      </Box>
    </Box>
  );
};

export default Sidebar;