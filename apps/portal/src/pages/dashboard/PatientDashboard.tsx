import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Button,
  Avatar,
  Chip,
  List,
  ListItem,
  ListItemText,
  ListItemAvatar,
  IconButton,
  Alert,
  LinearProgress,
} from '@mui/material';
import {
  Assignment,
  Schedule,
  CheckCircle,
  Warning,
  Message,
  Visibility,
  CardGiftcard,
  LocalHospital,
  Person,
} from '@mui/icons-material';
import { useAuth } from '../../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';

interface DashboardStats {
  totalReferrals: number;
  pendingReferrals: number;
  completedReferrals: number;
  rewardPoints: number;
}

interface RecentReferral {
  id: string;
  referralNumber: string;
  provider: string;
  specialty: string;
  status: string;
  scheduledDate?: string;
  createdAt: string;
}

interface RecentMessage {
  id: string;
  sender: string;
  subject: string;
  createdAt: string;
  isRead: boolean;
}

const PatientDashboard: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [stats, setStats] = useState<DashboardStats>({
    totalReferrals: 0,
    pendingReferrals: 0,
    completedReferrals: 0,
    rewardPoints: 0,
  });
  const [recentReferrals, setRecentReferrals] = useState<RecentReferral[]>([]);
  const [recentMessages, setRecentMessages] = useState<RecentMessage[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      
      // Fetch dashboard stats
      const statsResponse = await fetch('/api/dashboard/patient/stats', {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('token')}`,
        },
      });

      if (statsResponse.ok) {
        const statsData = await statsResponse.json();
        setStats(statsData);
      }

      // Fetch recent referrals
      const referralsResponse = await fetch('/api/referrals?limit=5', {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('token')}`,
        },
      });

      if (referralsResponse.ok) {
        const referralsData = await referralsResponse.json();
        setRecentReferrals(referralsData.referrals || []);
      }

      // Fetch recent messages
      const messagesResponse = await fetch('/api/messages?limit=5', {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('token')}`,
        },
      });

      if (messagesResponse.ok) {
        const messagesData = await messagesResponse.json();
        setRecentMessages(messagesData.messages || []);
      }
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'completed':
        return 'success';
      case 'pending':
        return 'warning';
      case 'rejected':
        return 'error';
      case 'accepted':
        return 'info';
      default:
        return 'default';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status.toLowerCase()) {
      case 'completed':
        return <CheckCircle color="success" />;
      case 'pending':
        return <Schedule color="warning" />;
      case 'rejected':
        return <Warning color="error" />;
      case 'accepted':
        return <Assignment color="info" />;
      default:
        return <Assignment />;
    }
  };

  if (loading) {
    return (
      <Box>
        <Typography variant="h4" gutterBottom>
          Loading Dashboard...
        </Typography>
        <LinearProgress />
      </Box>
    );
  }

  return (
    <Box>
      {/* Welcome Message */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" gutterBottom>
          Welcome back, {user?.firstName}!
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Here's an overview of your referrals and recent activity.
        </Typography>
      </Box>

      {/* Profile Completion Alert */}
      {!user?.profile?.dateOfBirth && (
        <Alert 
          severity="info" 
          sx={{ mb: 3 }}
          action={
            <Button
              color="inherit"
              size="small"
              onClick={() => navigate('/profile')}
            >
              Complete Profile
            </Button>
          }
        >
          Complete your profile to get better referral recommendations.
        </Alert>
      )}

      {/* Stats Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <Avatar sx={{ backgroundColor: 'primary.main', mr: 2 }}>
                  <Assignment />
                </Avatar>
                <Box>
                  <Typography variant="h4" fontWeight="bold">
                    {stats.totalReferrals}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Total Referrals
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <Avatar sx={{ backgroundColor: 'warning.main', mr: 2 }}>
                  <Schedule />
                </Avatar>
                <Box>
                  <Typography variant="h4" fontWeight="bold">
                    {stats.pendingReferrals}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Pending
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <Avatar sx={{ backgroundColor: 'success.main', mr: 2 }}>
                  <CheckCircle />
                </Avatar>
                <Box>
                  <Typography variant="h4" fontWeight="bold">
                    {stats.completedReferrals}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Completed
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <Avatar sx={{ backgroundColor: 'secondary.main', mr: 2 }}>
                  <CardGiftcard />
                </Avatar>
                <Box>
                  <Typography variant="h4" fontWeight="bold">
                    {stats.rewardPoints}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Reward Points
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Recent Activity */}
      <Grid container spacing={3}>
        {/* Recent Referrals */}
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6" fontWeight="bold">
                  Recent Referrals
                </Typography>
                <Button
                  variant="outlined"
                  size="small"
                  onClick={() => navigate('/referrals')}
                >
                  View All
                </Button>
              </Box>

              {recentReferrals.length === 0 ? (
                <Box sx={{ textAlign: 'center', py: 4 }}>
                  <LocalHospital sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
                  <Typography variant="body1" color="text.secondary">
                    No referrals yet
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Your referrals will appear here once they are created
                  </Typography>
                </Box>
              ) : (
                <List>
                  {recentReferrals.map((referral) => (
                    <ListItem
                      key={referral.id}
                      divider
                      secondaryAction={
                        <IconButton
                          onClick={() => navigate(`/referrals/${referral.id}`)}
                        >
                          <Visibility />
                        </IconButton>
                      }
                    >
                      <ListItemAvatar>
                        <Avatar>
                          {getStatusIcon(referral.status)}
                        </Avatar>
                      </ListItemAvatar>
                      <ListItemText
                        primary={
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <Typography variant="subtitle2">
                              {referral.referralNumber}
                            </Typography>
                            <Chip
                              label={referral.status}
                              size="small"
                              color={getStatusColor(referral.status) as any}
                            />
                          </Box>
                        }
                        secondary={
                          <Box>
                            <Typography variant="body2" color="text.secondary">
                              {referral.provider} - {referral.specialty}
                            </Typography>
                            {referral.scheduledDate && (
                              <Typography variant="caption" color="text.secondary">
                                Scheduled: {new Date(referral.scheduledDate).toLocaleDateString()}
                              </Typography>
                            )}
                          </Box>
                        }
                      />
                    </ListItem>
                  ))}
                </List>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Recent Messages */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6" fontWeight="bold">
                  Messages
                </Typography>
                <Button
                  variant="outlined"
                  size="small"
                  onClick={() => navigate('/messages')}
                >
                  View All
                </Button>
              </Box>

              {recentMessages.length === 0 ? (
                <Box sx={{ textAlign: 'center', py: 4 }}>
                  <Message sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
                  <Typography variant="body2" color="text.secondary">
                    No messages yet
                  </Typography>
                </Box>
              ) : (
                <List>
                  {recentMessages.map((message) => (
                    <ListItem
                      key={message.id}
                      divider
                      sx={{
                        backgroundColor: message.isRead ? 'transparent' : 'action.hover',
                      }}
                    >
                      <ListItemAvatar>
                        <Avatar>
                          <Person />
                        </Avatar>
                      </ListItemAvatar>
                      <ListItemText
                        primary={
                          <Typography
                            variant="subtitle2"
                            fontWeight={message.isRead ? 'normal' : 'bold'}
                          >
                            {message.sender}
                          </Typography>
                        }
                        secondary={
                          <Box>
                            <Typography
                              variant="body2"
                              color="text.secondary"
                              sx={{
                                overflow: 'hidden',
                                textOverflow: 'ellipsis',
                                whiteSpace: 'nowrap',
                              }}
                            >
                              {message.subject}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              {new Date(message.createdAt).toLocaleDateString()}
                            </Typography>
                          </Box>
                        }
                      />
                    </ListItem>
                  ))}
                </List>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default PatientDashboard;