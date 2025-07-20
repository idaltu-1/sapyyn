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
  Tabs,
  Tab,
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
  CheckBox,
  Close,
  QrCode,
  ContentCopy,
  CalendarToday,
} from '@mui/icons-material';
import { useAuth } from '../../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-toastify';

interface DashboardStats {
  totalReferrals: number;
  pendingReferrals: number;
  acceptedReferrals: number;
  completedReferrals: number;
  monthlyReferrals: number;
  rewardEarnings: number;
}

interface ReferralRequest {
  id: string;
  referralNumber: string;
  patientName: string;
  dentistName: string;
  specialty: string;
  urgency: string;
  reason: string;
  createdAt: string;
  scheduledDate?: string;
}

const SpecialistDashboard: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [tabValue, setTabValue] = useState(0);
  const [stats, setStats] = useState<DashboardStats>({
    totalReferrals: 0,
    pendingReferrals: 0,
    acceptedReferrals: 0,
    completedReferrals: 0,
    monthlyReferrals: 0,
    rewardEarnings: 0,
  });
  const [pendingReferrals, setPendingReferrals] = useState<ReferralRequest[]>([]);
  const [acceptedReferrals, setAcceptedReferrals] = useState<ReferralRequest[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      
      // Fetch dashboard stats
      const statsResponse = await fetch('/api/dashboard/specialist/stats', {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('token')}`,
        },
      });

      if (statsResponse.ok) {
        const statsData = await statsResponse.json();
        setStats(statsData);
      }

      // Fetch pending referrals
      const pendingResponse = await fetch('/api/referrals?status=pending&limit=10', {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('token')}`,
        },
      });

      if (pendingResponse.ok) {
        const pendingData = await pendingResponse.json();
        setPendingReferrals(pendingData.referrals || []);
      }

      // Fetch accepted referrals
      const acceptedResponse = await fetch('/api/referrals?status=accepted&limit=10', {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('token')}`,
        },
      });

      if (acceptedResponse.ok) {
        const acceptedData = await acceptedResponse.json();
        setAcceptedReferrals(acceptedData.referrals || []);
      }
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const copySpecialistCode = () => {
    if (user?.profile?.specialistCode) {
      navigator.clipboard.writeText(user.profile.specialistCode);
      toast.success('Specialist code copied to clipboard!');
    }
  };

  const handleReferralAction = async (referralId: string, action: 'accept' | 'reject') => {
    try {
      const response = await fetch(`/api/referrals/${referralId}/${action}`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        toast.success(`Referral ${action}ed successfully!`);
        fetchDashboardData(); // Refresh data
      } else {
        toast.error(`Failed to ${action} referral`);
      }
    } catch (error) {
      console.error(`Error ${action}ing referral:`, error);
      toast.error(`Failed to ${action} referral`);
    }
  };

  const getUrgencyColor = (urgency: string) => {
    switch (urgency.toLowerCase()) {
      case 'urgent':
        return 'error';
      case 'high':
        return 'warning';
      case 'normal':
        return 'info';
      case 'low':
        return 'default';
      default:
        return 'default';
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
          Review patient referrals and manage your specialist practice.
        </Typography>
      </Box>

      {/* Specialist Code Card */}
      <Paper sx={{ p: 3, mb: 4, background: 'linear-gradient(135deg, #cb0c9f 0%, #010187 100%)', color: 'white' }}>
        <Grid container spacing={3} alignItems="center">
          <Grid item xs={12} md={8}>
            <Typography variant="h6" gutterBottom>
              Your Specialist Code
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
              <Typography variant="h3" fontWeight="bold">
                {user?.profile?.specialistCode}
              </Typography>
              <IconButton onClick={copySpecialistCode} sx={{ color: 'white' }}>
                <ContentCopy />
              </IconButton>
            </Box>
            <Typography variant="body2" sx={{ opacity: 0.9 }}>
              Specialization: {user?.profile?.specialization}
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

      {/* Stats Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={2}>
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
                    Total
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={2}>
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

        <Grid item xs={12} sm={6} md={2}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <Avatar sx={{ backgroundColor: 'info.main', mr: 2 }}>
                  <CheckBox />
                </Avatar>
                <Box>
                  <Typography variant="h4" fontWeight="bold">
                    {stats.acceptedReferrals}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Accepted
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={2}>
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

        <Grid item xs={12} sm={6} md={2}>
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

        <Grid item xs={12} sm={6} md={2}>
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

      {/* Referral Management */}
      <Card>
        <CardContent>
          <Typography variant="h6" fontWeight="bold" sx={{ mb: 2 }}>
            Referral Management
          </Typography>
          
          <Tabs value={tabValue} onChange={(e, newValue) => setTabValue(newValue)} sx={{ mb: 3 }}>
            <Tab label={`Pending (${stats.pendingReferrals})`} />
            <Tab label={`Accepted (${stats.acceptedReferrals})`} />
          </Tabs>

          {/* Pending Referrals Tab */}
          {tabValue === 0 && (
            <Box>
              {pendingReferrals.length === 0 ? (
                <Box sx={{ textAlign: 'center', py: 4 }}>
                  <Schedule sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
                  <Typography variant="body1" color="text.secondary">
                    No pending referrals
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    New referral requests will appear here
                  </Typography>
                </Box>
              ) : (
                <List>
                  {pendingReferrals.map((referral, index) => (
                    <React.Fragment key={referral.id}>
                      <ListItem
                        secondaryAction={
                          <Box sx={{ display: 'flex', gap: 1 }}>
                            <Button
                              variant="contained"
                              color="success"
                              size="small"
                              startIcon={<CheckBox />}
                              onClick={() => handleReferralAction(referral.id, 'accept')}
                            >
                              Accept
                            </Button>
                            <Button
                              variant="outlined"
                              color="error"
                              size="small"
                              startIcon={<Close />}
                              onClick={() => handleReferralAction(referral.id, 'reject')}
                            >
                              Reject
                            </Button>
                            <IconButton
                              onClick={() => navigate(`/referrals/${referral.id}`)}
                            >
                              <Visibility />
                            </IconButton>
                          </Box>
                        }
                      >
                        <ListItemAvatar>
                          <Avatar>
                            <Person />
                          </Avatar>
                        </ListItemAvatar>
                        <ListItemText
                          primary={
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                              <Typography variant="subtitle2">
                                {referral.referralNumber}
                              </Typography>
                              <Chip
                                label={referral.urgency}
                                size="small"
                                color={getUrgencyColor(referral.urgency) as any}
                              />
                            </Box>
                          }
                          secondary={
                            <Box>
                              <Typography variant="body2" color="text.secondary">
                                Patient: {referral.patientName}
                              </Typography>
                              <Typography variant="body2" color="text.secondary">
                                Referring Dr: {referral.dentistName}
                              </Typography>
                              <Typography variant="body2" color="text.secondary">
                                Reason: {referral.reason}
                              </Typography>
                              <Typography variant="caption" color="text.secondary">
                                Received: {new Date(referral.createdAt).toLocaleDateString()}
                              </Typography>
                            </Box>
                          }
                        />
                      </ListItem>
                      {index < pendingReferrals.length - 1 && <Divider />}
                    </React.Fragment>
                  ))}
                </List>
              )}
            </Box>
          )}

          {/* Accepted Referrals Tab */}
          {tabValue === 1 && (
            <Box>
              {acceptedReferrals.length === 0 ? (
                <Box sx={{ textAlign: 'center', py: 4 }}>
                  <CalendarToday sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
                  <Typography variant="body1" color="text.secondary">
                    No accepted referrals
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Accepted referrals will appear here for scheduling
                  </Typography>
                </Box>
              ) : (
                <List>
                  {acceptedReferrals.map((referral, index) => (
                    <React.Fragment key={referral.id}>
                      <ListItem
                        secondaryAction={
                          <Box sx={{ display: 'flex', gap: 1 }}>
                            <Button
                              variant="outlined"
                              size="small"
                              startIcon={<CalendarToday />}
                            >
                              Schedule
                            </Button>
                            <IconButton
                              onClick={() => navigate(`/referrals/${referral.id}`)}
                            >
                              <Visibility />
                            </IconButton>
                          </Box>
                        }
                      >
                        <ListItemAvatar>
                          <Avatar sx={{ backgroundColor: 'success.main' }}>
                            <CheckBox />
                          </Avatar>
                        </ListItemAvatar>
                        <ListItemText
                          primary={
                            <Typography variant="subtitle2">
                              {referral.referralNumber}
                            </Typography>
                          }
                          secondary={
                            <Box>
                              <Typography variant="body2" color="text.secondary">
                                Patient: {referral.patientName}
                              </Typography>
                              <Typography variant="body2" color="text.secondary">
                                Referring Dr: {referral.dentistName}
                              </Typography>
                              {referral.scheduledDate ? (
                                <Typography variant="body2" color="success.main" fontWeight="bold">
                                  Scheduled: {new Date(referral.scheduledDate).toLocaleDateString()}
                                </Typography>
                              ) : (
                                <Typography variant="body2" color="warning.main">
                                  Needs scheduling
                                </Typography>
                              )}
                            </Box>
                          }
                        />
                      </ListItem>
                      {index < acceptedReferrals.length - 1 && <Divider />}
                    </React.Fragment>
                  ))}
                </List>
              )}
            </Box>
          )}
        </CardContent>
      </Card>
    </Box>
  );
};

export default SpecialistDashboard;