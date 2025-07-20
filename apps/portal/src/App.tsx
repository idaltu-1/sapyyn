import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { Box } from '@mui/material';

// Auth components
import Login from './pages/auth/Login';
import Register from './pages/auth/Register';
import ForgotPassword from './pages/auth/ForgotPassword';
import ResetPassword from './pages/auth/ResetPassword';

// Dashboard components
import DashboardLayout from './components/layout/DashboardLayout';
import ProtectedRoute from './components/auth/ProtectedRoute';

// Dashboard pages
import PatientDashboard from './pages/dashboard/PatientDashboard';
import DentistDashboard from './pages/dashboard/DentistDashboard';
import SpecialistDashboard from './pages/dashboard/SpecialistDashboard';

// Feature pages
import ReferralsPage from './pages/referrals/ReferralsPage';
import CreateReferral from './pages/referrals/CreateReferral';
import ReferralDetails from './pages/referrals/ReferralDetails';
import DocumentsPage from './pages/documents/DocumentsPage';
import MessagesPage from './pages/messages/MessagesPage';
import ProfilePage from './pages/profile/ProfilePage';
import RewardsPage from './pages/rewards/RewardsPage';

// Public pages
import PublicReferral from './pages/public/PublicReferral';

import { useAuth } from './contexts/AuthContext';

function App() {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <Box
        display="flex"
        justifyContent="center"
        alignItems="center"
        minHeight="100vh"
      >
        Loading...
      </Box>
    );
  }

  return (
    <Routes>
      {/* Public Routes */}
      <Route path="/login" element={!user ? <Login /> : <Navigate to="/dashboard" />} />
      <Route path="/register" element={!user ? <Register /> : <Navigate to="/dashboard" />} />
      <Route path="/forgot-password" element={!user ? <ForgotPassword /> : <Navigate to="/dashboard" />} />
      <Route path="/reset-password" element={!user ? <ResetPassword /> : <Navigate to="/dashboard" />} />
      <Route path="/referral/:code" element={<PublicReferral />} />

      {/* Protected Routes */}
      <Route
        path="/*"
        element={
          <ProtectedRoute>
            <DashboardLayout>
              <Routes>
                <Route path="/" element={<Navigate to="/dashboard" />} />
                
                {/* Role-based Dashboards */}
                <Route 
                  path="/dashboard" 
                  element={
                    user?.role === 'PATIENT' ? <PatientDashboard /> :
                    user?.role === 'DENTIST' ? <DentistDashboard /> :
                    user?.role === 'SPECIALIST' ? <SpecialistDashboard /> :
                    <Navigate to="/login" />
                  } 
                />

                {/* Feature Routes */}
                <Route path="/referrals" element={<ReferralsPage />} />
                <Route path="/referrals/create" element={<CreateReferral />} />
                <Route path="/referrals/:id" element={<ReferralDetails />} />
                <Route path="/documents" element={<DocumentsPage />} />
                <Route path="/messages" element={<MessagesPage />} />
                <Route path="/profile" element={<ProfilePage />} />
                <Route path="/rewards" element={<RewardsPage />} />

                {/* Catch all route */}
                <Route path="*" element={<Navigate to="/dashboard" />} />
              </Routes>
            </DashboardLayout>
          </ProtectedRoute>
        }
      />
    </Routes>
  );
}

export default App;