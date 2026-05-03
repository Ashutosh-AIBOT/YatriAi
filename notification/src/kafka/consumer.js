const { Kafka } = require('kafkajs');
const { getSocketId } = require('../redis/session');

const brokers = (process.env.KAFKA_BOOTSTRAP_SERVERS || 'localhost:9092').split(',');

const kafka = new Kafka({
    clientId: 'notification-service',
    brokers: brokers,
});

const consumer = kafka.consumer({ groupId: 'notification-group' });

async function startKafkaConsumer(io) {
    await consumer.connect();
    console.log('Kafka consumer connected');

    const topics = ['trip.started', 'price.alert', 'booking.confirmed', 'cab.eta.update'];
    for (const topic of topics) {
        try {
            await consumer.subscribe({ topic, fromBeginning: false });
            console.log(`Subscribed to topic: ${topic}`);
        } catch (err) {
            console.error(`Error subscribing to topic ${topic}:`, err.message);
        }
    }

    await consumer.run({
        eachMessage: async ({ topic, partition, message }) => {
            try {
                const msgValue = message.value.toString();
                const payload = JSON.parse(msgValue);
                console.log(`Received message on ${topic}:`, payload);

                const userId = payload.userId || payload.user_id;
                if (userId) {
                    const socketId = await getSocketId(userId);
                    if (socketId) {
                        io.to(socketId).emit(topic, payload);
                        console.log(`Pushed to user ${userId} on socket ${socketId}`);
                    }
                }
            } catch (err) {
                console.error('Error processing message:', err);
            }
        },
    });
}

module.exports = { startKafkaConsumer };
