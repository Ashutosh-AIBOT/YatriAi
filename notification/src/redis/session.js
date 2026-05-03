const { createClient } = require('redis');

const redisUrl = process.env.REDIS_URL || 'redis://localhost:6379';
const client = createClient({ url: redisUrl });

client.on('error', (err) => console.error('Redis Client Error', err));

async function connectRedis() {
    await client.connect();
}

async function saveSession(userId, socketId) {
    await client.set(`user:${userId}:socket`, socketId, { EX: 86400 }); // 24 hours TTL
    await client.set(`socket:${socketId}:user`, userId, { EX: 86400 });
}

async function removeSession(socketId) {
    const userId = await client.get(`socket:${socketId}:user`);
    if (userId) {
        await client.del(`user:${userId}:socket`);
    }
    await client.del(`socket:${socketId}:user`);
}

async function getSocketId(userId) {
    return await client.get(`user:${userId}:socket`);
}

module.exports = {
    connectRedis,
    saveSession,
    removeSession,
    getSocketId
};
