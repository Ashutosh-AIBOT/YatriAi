require('dotenv').config({ path: '../../.env' });
const express = require('express');
const http = require('http');
const { Server } = require('socket.io');
const authMiddleware = require('./middleware/auth');
const { connectRedis, saveSession, removeSession } = require('./redis/session');
const { startKafkaConsumer } = require('./kafka/consumer');

const app = express();
const server = http.createServer(app);
const io = new Server(server, {
    cors: {
        origin: '*',
    }
});

app.get('/health', (req, res) => {
    res.json({ status: 'UP' });
});

io.use(authMiddleware);

io.on('connection', async (socket) => {
    const userId = socket.user.sub || socket.user.id || 'unknown';
    console.log(`User connected: ${userId} with socket: ${socket.id}`);
    
    await saveSession(userId, socket.id);

    socket.on('disconnect', async () => {
        console.log(`User disconnected: ${userId}`);
        await removeSession(socket.id);
    });
});

const PORT = process.env.NOTIFICATION_PORT || 3001;

async function bootstrap() {
    try {
        await connectRedis();
        console.log('Connected to Redis');
        
        await startKafkaConsumer(io);
        
        server.listen(PORT, () => {
            console.log(`Notification service listening on port ${PORT}`);
        });
    } catch (err) {
        console.error('Failed to start notification service:', err);
        process.exit(1);
    }
}

bootstrap();
