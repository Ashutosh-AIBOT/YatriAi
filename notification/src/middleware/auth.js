const jwt = require('jsonwebtoken');

function authMiddleware(socket, next) {
    const token = socket.handshake.auth?.token || socket.handshake.headers?.authorization?.split(' ')[1];
    if (!token) {
        return next(new Error('Authentication error'));
    }
    try {
        const secret = process.env.JWT_SECRET || 'minimum_32_char_random_string_here';
        const decoded = jwt.verify(token, secret);
        socket.user = decoded; // { sub: userId, email: ... }
        next();
    } catch (err) {
        next(new Error('Authentication error'));
    }
}

module.exports = authMiddleware;
