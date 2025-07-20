import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  TextField,
  Button,
  Typography,
  Link,
  Divider,
  Alert,
  MenuItem,
  Grid,
  InputAdornment,
  IconButton,
  FormControlLabel,
  Checkbox,
} from '@mui/material';
import { Link as RouterLink, useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { Visibility, VisibilityOff, Email, Lock, Person, Phone } from '@mui/icons-material';
import { useAuth } from '../../contexts/AuthContext';

interface RegisterFormData {
  firstName: string;
  lastName: string;
  email: string;
  phone: string;
  password: string;
  confirmPassword: string;
  role: 'PATIENT' | 'DENTIST' | 'SPECIALIST';
  termsAccepted: boolean;
}

const Register: React.FC = () => {
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const { register: registerUser } = useAuth();
  const navigate = useNavigate();
  
  const {
    register,
    handleSubmit,
    formState: { errors },
    watch,
    setError,
  } = useForm<RegisterFormData>();

  const password = watch('password');

  const onSubmit = async (data: RegisterFormData) => {
    if (data.password !== data.confirmPassword) {
      setError('confirmPassword', { message: 'Passwords do not match' });
      return;
    }

    if (!data.termsAccepted) {
      setError('termsAccepted', { message: 'You must accept the terms and conditions' });
      return;
    }

    setIsLoading(true);
    try {
      const success = await registerUser({
        firstName: data.firstName,
        lastName: data.lastName,
        email: data.email,
        phone: data.phone,
        password: data.password,
        role: data.role,
      });
      
      if (success) {
        navigate('/login');
      }
    } catch (error) {
      setError('root', { message: 'Registration failed. Please try again.' });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'linear-gradient(135deg, #010187 0%, #cb0c9f 100%)',
        p: 2,
      }}
    >
      <Card
        sx={{
          maxWidth: 600,
          width: '100%',
          boxShadow: '0 20px 40px rgba(0, 0, 0, 0.1)',
        }}
      >
        <CardContent sx={{ p: 4 }}>
          <Box sx={{ textAlign: 'center', mb: 4 }}>
            <img
              src="/images/logo.png"
              alt="Sapyyn"
              style={{ height: 50, marginBottom: 16 }}
            />
            <Typography variant="h4" fontWeight="bold" color="primary.main">
              Create Account
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Join the Sapyyn healthcare network
            </Typography>
          </Box>

          {errors.root && (
            <Alert severity="error" sx={{ mb: 3 }}>
              {errors.root.message}
            </Alert>
          )}

          <Box component="form" onSubmit={handleSubmit(onSubmit)}>
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="First Name"
                  margin="normal"
                  InputProps={{
                    startAdornment: (
                      <InputAdornment position="start">
                        <Person color="action" />
                      </InputAdornment>
                    ),
                  }}
                  {...register('firstName', {
                    required: 'First name is required',
                    minLength: {
                      value: 2,
                      message: 'First name must be at least 2 characters',
                    },
                  })}
                  error={!!errors.firstName}
                  helperText={errors.firstName?.message}
                />
              </Grid>

              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Last Name"
                  margin="normal"
                  InputProps={{
                    startAdornment: (
                      <InputAdornment position="start">
                        <Person color="action" />
                      </InputAdornment>
                    ),
                  }}
                  {...register('lastName', {
                    required: 'Last name is required',
                    minLength: {
                      value: 2,
                      message: 'Last name must be at least 2 characters',
                    },
                  })}
                  error={!!errors.lastName}
                  helperText={errors.lastName?.message}
                />
              </Grid>

              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Email Address"
                  type="email"
                  margin="normal"
                  InputProps={{
                    startAdornment: (
                      <InputAdornment position="start">
                        <Email color="action" />
                      </InputAdornment>
                    ),
                  }}
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
                  label="Phone Number"
                  margin="normal"
                  InputProps={{
                    startAdornment: (
                      <InputAdornment position="start">
                        <Phone color="action" />
                      </InputAdornment>
                    ),
                  }}
                  {...register('phone', {
                    required: 'Phone number is required',
                    pattern: {
                      value: /^[\+]?[1-9][\d]{0,15}$/,
                      message: 'Invalid phone number',
                    },
                  })}
                  error={!!errors.phone}
                  helperText={errors.phone?.message}
                />
              </Grid>

              <Grid item xs={12}>
                <TextField
                  fullWidth
                  select
                  label="Account Type"
                  margin="normal"
                  {...register('role', {
                    required: 'Account type is required',
                  })}
                  error={!!errors.role}
                  helperText={errors.role?.message}
                >
                  <MenuItem value="PATIENT">Patient</MenuItem>
                  <MenuItem value="DENTIST">Dentist</MenuItem>
                  <MenuItem value="SPECIALIST">Specialist</MenuItem>
                </TextField>
              </Grid>

              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Password"
                  type={showPassword ? 'text' : 'password'}
                  margin="normal"
                  InputProps={{
                    startAdornment: (
                      <InputAdornment position="start">
                        <Lock color="action" />
                      </InputAdornment>
                    ),
                    endAdornment: (
                      <InputAdornment position="end">
                        <IconButton
                          onClick={() => setShowPassword(!showPassword)}
                          edge="end"
                        >
                          {showPassword ? <VisibilityOff /> : <Visibility />}
                        </IconButton>
                      </InputAdornment>
                    ),
                  }}
                  {...register('password', {
                    required: 'Password is required',
                    minLength: {
                      value: 8,
                      message: 'Password must be at least 8 characters',
                    },
                    pattern: {
                      value: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/,
                      message: 'Password must contain uppercase, lowercase, and number',
                    },
                  })}
                  error={!!errors.password}
                  helperText={errors.password?.message}
                />
              </Grid>

              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Confirm Password"
                  type={showConfirmPassword ? 'text' : 'password'}
                  margin="normal"
                  InputProps={{
                    startAdornment: (
                      <InputAdornment position="start">
                        <Lock color="action" />
                      </InputAdornment>
                    ),
                    endAdornment: (
                      <InputAdornment position="end">
                        <IconButton
                          onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                          edge="end"
                        >
                          {showConfirmPassword ? <VisibilityOff /> : <Visibility />}
                        </IconButton>
                      </InputAdornment>
                    ),
                  }}
                  {...register('confirmPassword', {
                    required: 'Please confirm your password',
                    validate: (value) =>
                      value === password || 'Passwords do not match',
                  })}
                  error={!!errors.confirmPassword}
                  helperText={errors.confirmPassword?.message}
                />
              </Grid>

              <Grid item xs={12}>
                <FormControlLabel
                  control={
                    <Checkbox
                      {...register('termsAccepted', {
                        required: 'You must accept the terms and conditions',
                      })}
                    />
                  }
                  label={
                    <Typography variant="body2">
                      I agree to the{' '}
                      <Link href="/terms" target="_blank" color="primary">
                        Terms of Service
                      </Link>{' '}
                      and{' '}
                      <Link href="/privacy" target="_blank" color="primary">
                        Privacy Policy
                      </Link>
                    </Typography>
                  }
                />
                {errors.termsAccepted && (
                  <Typography variant="caption" color="error" display="block">
                    {errors.termsAccepted.message}
                  </Typography>
                )}
              </Grid>
            </Grid>

            <Button
              type="submit"
              fullWidth
              variant="contained"
              size="large"
              disabled={isLoading}
              sx={{
                mt: 3,
                py: 1.5,
                background: 'linear-gradient(135deg, #010187 0%, #cb0c9f 100%)',
                '&:hover': {
                  background: 'linear-gradient(135deg, #000066 0%, #ad0a87 100%)',
                },
              }}
            >
              {isLoading ? 'Creating Account...' : 'Create Account'}
            </Button>

            <Divider sx={{ my: 3 }}>
              <Typography variant="body2" color="text.secondary">
                or
              </Typography>
            </Divider>

            <Box sx={{ textAlign: 'center' }}>
              <Typography variant="body2" color="text.secondary">
                Already have an account?{' '}
                <Link
                  component={RouterLink}
                  to="/login"
                  color="primary"
                  fontWeight="medium"
                >
                  Sign in
                </Link>
              </Typography>
            </Box>
          </Box>
        </CardContent>
      </Card>
    </Box>
  );
};

export default Register;