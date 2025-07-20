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
  Paper,
  Divider,
} from '@mui/material';
import {
  Assignment,
  Schedule,
  CheckCircle,
  TrendingUp,
  Message,
  Visibility,
  CardGiftcard,
  LocalHospital,
  Person,
  Add,
  QrCode,
  ContentCopy,
} from '@mui/icons-material';
import { useAuth } from '../../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-toastify';

interface DashboardStats {
  totalReferrals: number;
  pendingReferrals: number;
  completedReferrals: number;
  monthlyReferrals: number;
  rewardEarnings: number;
}

interface RecentReferral {
  id: string;
  referralNumber: string;
  patientName: string;
  specialist: string;
  specialty: string;
  status: string;
  scheduledDate?: string;
  createdAt: string;
}

const DentistDashboard: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [stats, setStats] = useState<DashboardStats>({
    totalReferrals: 0,
    pendingReferrals: 0,
    completedReferrals: 0,
    monthlyReferrals: 0,
    rewardEarnings: 0,
  });
  const [recentReferrals, setRecentReferrals] = useState<RecentReferral[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      
      // Fetch dashboard stats
      const statsResponse = await fetch('/api/dashboard/dentist/stats', {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('token')}`,
        },
      });

      if (statsResponse.ok) {
        const statsData = await statsResponse.json();
        setStats(statsData);
      }

      // Fetch recent referrals
      const referralsResponse = await fetch('/api/referrals?limit=10', {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('token')}`,
        },
      });

      if (referralsResponse.ok) {
        const referralsData = await referralsResponse.json();
        setRecentReferrals(referralsData.referrals || []);
      }
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const copyDentistCode = () => {
    if (user?.profile?.dentistCode) {
      navigator.clipboard.writeText(user.profile.dentistCode);
      toast.success('Dentist code copied to clipboard!');
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
          Welcome back, Dr. {user?.lastName}!
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Manage your patient referrals and track your practice performance.
        </Typography>
      </Box>

      {/* Dentist Code Card */}
      <Paper sx={{ p: 3, mb: 4, background: 'linear-gradient(135deg, #010187 0%, #cb0c9f 100%)', color: 'white' }}>
        <Grid container spacing={3} alignItems="center">
          <Grid item xs={12} md={8}>
            <Typography variant="h6" gutterBottom>
              Your Referral Code
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
              <Typography variant="h3" fontWeight="bold">
                {user?.profile?.dentistCode}
              </Typography>
              <IconButton onClick={copyDentistCode} sx={{ color: 'white' }}>
                <ContentCopy />
              </IconButton>
            </Box>
            <Typography variant="body2" sx={{ opacity: 0.9 }}>
              Share this 6-digit code with patients for quick referrals
            </Typography>
          </Grid>
          <Grid item xs={12} md={4} sx={{ textAlign: 'center' }}>
            <Box sx={{ mb: 2 }}>
              <QrCode sx={{ fontSize: 80 }} />
            </Box>
            <Button
              variant="outlined"
              sx={{ 
                color: 'white', 
                borderColor: 'white',
                '&:hover': {
                  backgroundColor: 'rgba(255, 255, 255, 0.1)',
                  borderColor: 'white',
                }
              }}
            >
              Generate QR Code
            </Button>
          </Grid>
        </Grid>
      </Paper>

      {/* Quick Actions */}
      <Grid container spacing={2} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Button
            fullWidth
            variant="contained"
            size="large"
            startIcon={<Add />}
            onClick={() => navigate('/referrals/create')}
            sx={{ py: 2 }}
          >
            New Referral
          </Button>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Button
            fullWidth
            variant="outlined"
            size="large"
            startIcon={<Assignment />}
            onClick={() => navigate('/referrals')}
            sx={{ py: 2 }}
          >
            View Referrals
          </Button>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Button
            fullWidth
            variant="outlined"
            size="large"
            startIcon={<Message />}
            onClick={() => navigate('/messages')}
            sx={{ py: 2 }}
          >
            Messages
          </Button>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Button
            fullWidth
            variant="outlined"
            size="large"
            startIcon={<CardGiftcard />}
            onClick={() => navigate('/rewards')}
            sx={{ py: 2 }}
          >
            Rewards
          </Button>
        </Grid>
      </Grid>

      {/* Stats Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={2.4}>
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

        <Grid item xs={12} sm={6} md={2.4}>
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

        <Grid item xs={12} sm={6} md={2.4}>
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

        <Grid item xs={12} sm={6} md={2.4}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <Avatar sx={{ backgroundColor: 'info.main', mr: 2 }}>
                  <TrendingUp />
                </Avatar>
                <Box>
                  <Typography variant="h4" fontWeight="bold">
                    {stats.monthlyReferrals}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    This Month
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={2.4}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <Avatar sx={{ backgroundColor: 'secondary.main', mr: 2 }}>
                  <CardGiftcard />
                </Avatar>
                <Box>
                  <Typography variant="h4" fontWeight="bold">
                    ${stats.rewardEarnings}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Earnings
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Recent Referrals */}
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
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                Start referring patients to specialists
              </Typography>
              <Button
                variant="contained"
                startIcon={<Add />}
                onClick={() => navigate('/referrals/create')}
              >
                Create First Referral
              </Button>
            </Box>
          ) : (
            <List>
              {recentReferrals.map((referral, index) => (
                <React.Fragment key={referral.id}>
                  <ListItem
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
                            Patient: {referral.patientName}
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            Specialist: {referral.specialist} - {referral.specialty}
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
                  {index < recentReferrals.length - 1 && <Divider />}
                </React.Fragment>
              ))}
            </List>
          )}
        </CardContent>
      </Card>
    </Box>
  );
};

export default DentistDashboard;