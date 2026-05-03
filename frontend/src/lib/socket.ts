import { io, Socket } from 'socket.io-client';
import { useAuthStore } from '../store/authStore';

let socket: Socket | null = null;

export const initSocket = (): Socket => {
  if (socket) return socket;

  const token = useAuthStore.getState().accessToken;
  
  socket = io(process.env.NEXT_PUBLIC_NOTIFICATION_URL || 'http://localhost:3001', {
    auth: {
      token,
    },
    autoConnect: true,
  });

  socket.on('connect', () => {
    console.log('Connected to notification service');
  });

  socket.on('disconnect', () => {
    console.log('Disconnected from notification service');
  });

  return socket;
};

export const getSocket = (): Socket | null => socket;

export const disconnectSocket = () => {
  if (socket) {
    socket.disconnect();
    socket = null;
  }
};
