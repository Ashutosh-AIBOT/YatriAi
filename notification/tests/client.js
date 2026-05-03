require('dotenv').config({ path: '../../.env' });
const { io } = require('socket.io-client');
const jwt = require('jsonwebtoken');

// Generate a dummy token for testing
const secret = process.env.JWT_SECRET || 'minimum_32_char_random_string_here';
const testUserId = 'test-user-123';
const token = jwt.sign({ sub: testUserId, email: 'test@example.com' }, secret, { expiresIn: '1h' });

console.log(`Generated test token for user ${testUserId}`);

const socket = io('http://localhost:3001', {
    auth: {
        token: token
    }
});

socket.on('connect', () => {
    console.log(`Connected to Notification Service with socket ID: ${socket.id}`);
});

const topics = ['trip.started', 'price.alert', 'booking.confirmed', 'cab.eta.update'];

topics.forEach(topic => {
    socket.on(topic, (data) => {
        console.log(`Received event on topic ${topic}:`, data);
    });
});

socket.on('connect_error', (err) => {
    console.error('Connection error:', err.message);
});

socket.on('disconnect', () => {
    console.log('Disconnected from server');
});

// Run for 15 seconds then exit
setTimeout(() => {
    console.log('Test client exiting');
    process.exit(0);
}, 15000);
