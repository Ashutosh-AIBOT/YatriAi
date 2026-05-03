const { Kafka } = require('kafkajs');

const brokers = (process.env.KAFKA_BOOTSTRAP_SERVERS || 'localhost:9092').split(',');

const kafka = new Kafka({
    clientId: 'yatra-admin',
    brokers: brokers,
});

const admin = kafka.admin();

async function createTopics() {
    try {
        await admin.connect();
        console.log('Connected to Kafka admin');

        const topics = [
            {
                topic: 'trip.started',
                numPartitions: 6,
                replicationFactor: 1 // For local dev
            },
            {
                topic: 'price.alert',
                numPartitions: 12,
                replicationFactor: 1
            },
            {
                topic: 'booking.confirmed',
                numPartitions: 6,
                replicationFactor: 1
            },
            {
                topic: 'cab.eta.update',
                numPartitions: 12,
                replicationFactor: 1
            }
        ];

        const created = await admin.createTopics({
            topics: topics,
            waitForLeaders: true,
        });

        if (created) {
            console.log('Topics successfully created!');
        } else {
            console.log('Topics might already exist.');
        }

    } catch (error) {
        console.error('Error creating topics:', error);
    } finally {
        await admin.disconnect();
    }
}

createTopics();
