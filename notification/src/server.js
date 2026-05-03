require('dotenv').config({ path: '../../.env' });
const express = require('express');
const http = require('http');
const { Server } = require('socket.io');
const authMiddleware = require('./middleware/auth');

const app = express();
const server = http.createServer(app);
const io = new Server(server, {
    cors: {
        origin: '*',
    }
});

app.get('/health', (req, res) => {
    res.json({ status: 'UP', service: 'notification' });
});

io.use(authMiddleware);

io.on('connection', async (socket) => {
    const userId = socket.user.sub || socket.user.id || 'unknown';
    console.log(`User connected: ${userId} with socket: ${socket.id}`);

    socket.on('disconnect', async () => {
        console.log(`User disconnected: ${userId}`);
    });
});

const PORT = process.env.NOTIFICATION_PORT || 3001;

async function bootstrap() {
    // Try connecting to Redis, but don't crash if unavailable
    try {
        const { connectRedis } = require('./redis/session');
        await connectRedis();
        console.log('✅ Connected to Redis');
    } catch (err) {
        console.warn('⚠️  Redis unavailable — running without session persistence:', err.message);
    }

    // Try connecting to Kafka, but don't crash if unavailable
    try {
        const { startKafkaConsumer } = require('./kafka/consumer');
        await startKafkaConsumer(io);
        console.log('✅ Kafka consumer started');
    } catch (err) {
        console.warn('⚠️  Kafka unavailable — running without real-time push:', err.message);
    }

    // Always start the HTTP server regardless of Redis/Kafka status
    server.listen(PORT, () => {
        console.log(`🔔 Notification service listening on port ${PORT}`);
    });
}

bootstrap();
