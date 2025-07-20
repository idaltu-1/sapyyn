import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { io, Socket } from 'socket.io-client';
import { toast } from 'react-toastify';
import { useAuth } from './AuthContext';

interface SocketContextType {
  socket: Socket | null;
  connected: boolean;
  joinReferral: (referralId: string) => void;
  leaveReferral: (referralId: string) => void;
}

const SocketContext = createContext<SocketContextType | undefined>(undefined);

export const useSocket = () => {
  const context = useContext(SocketContext);
  if (context === undefined) {
    throw new Error('useSocket must be used within a SocketProvider');
  }
  return context;
};

interface SocketProviderProps {
  children: ReactNode;
}

export const SocketProvider: React.FC<SocketProviderProps> = ({ children }) => {
  const [socket, setSocket] = useState<Socket | null>(null);
  const [connected, setConnected] = useState(false);
  const { token, user } = useAuth();

  useEffect(() => {
    if (token && user) {
      const newSocket = io('http://localhost:5000', {
        auth: {
          token,
        },
      });

      newSocket.on('connect', () => {
        console.log('Connected to server');
        setConnected(true);
      });

      newSocket.on('disconnect', () => {
        console.log('Disconnected from server');
        setConnected(false);
      });

      newSocket.on('notification', (notification) => {
        toast.info(notification.message, {
          autoClose: 8000,
        });
      });

      newSocket.on('referral_update', (update) => {
        toast.info(`Referral ${update.referralNumber} has been updated`, {
          autoClose: 5000,
        });
      });

      newSocket.on('new_message', (message) => {
        toast.info(`New message from ${message.sender.firstName} ${message.sender.lastName}`, {
          autoClose: 5000,
        });
      });

      setSocket(newSocket);

      return () => {
        newSocket.close();
      };
    } else {
      if (socket) {
        socket.close();
        setSocket(null);
        setConnected(false);
      }
    }
  }, [token, user]);

  const joinReferral = (referralId: string) => {
    if (socket) {
      socket.emit('join_referral', referralId);
    }
  };

  const leaveReferral = (referralId: string) => {
    if (socket) {
      socket.emit('leave_referral', referralId);
    }
  };

  const value = {
    socket,
    connected,
    joinReferral,
    leaveReferral,
  };

  return <SocketContext.Provider value={value}>{children}</SocketContext.Provider>;
};